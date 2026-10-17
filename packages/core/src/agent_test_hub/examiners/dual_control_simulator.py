from __future__ import annotations

import json
from typing import Any, Callable

from agent_test_hub.schemas import ActorRole, ExecutionTrace, TraceEvent, TraceEventType
from agent_test_hub_sandbox import BaseSandbox

from .base import BaseExaminer, ExaminerAction


class DualControlUserSimulator(BaseExaminer):
    """双控用户模拟器 (E8-01 ~ E8-02)

    结合有限状态机 (FSM) 与大语言模型：
    1. 拥有环境侧真实操作能力（通过工具直接修改沙盒或出示外部物料，如上传凭证、确认签字）；
    2. 隐藏目标分阶段披露与达成度跟踪；
    3. 支持纯仿真与物理双向受控。
    """

    role = "user_simulator"

    def __init__(
        self,
        persona: str,
        initial_message: str,
        hidden_goals: list[str],
        state_transitions: list[dict[str, Any]],
        sandbox: BaseSandbox | None = None,
        max_turns: int = 4,
    ):
        self.persona = persona
        self.initial_message = initial_message
        self.hidden_goals = hidden_goals
        self.state_transitions = state_transitions
        self.sandbox = sandbox
        self.max_turns = max_turns
        self.current_state = "init"
        self.completed_goals: list[str] = []
        self.emit: Callable[[TraceEvent], None] | None = None

    def bind(self, emit: Callable[[TraceEvent], None]) -> None:
        self.emit = emit

    def act(self, trace: ExecutionTrace, turn_index: int) -> ExaminerAction:
        if turn_index == 1:
            return ExaminerAction(
                action_type="speak",
                content=self.initial_message,
                internal_state={"fsm_state": self.current_state, "completed_goals": []},
            )

        if turn_index >= self.max_turns:
            return ExaminerAction(
                action_type="terminate",
                content="达到双控模拟器会话最大轮次",
                should_stop_eval=True,
            )

        # 检查上一轮 Agent 消息并依据状态机转移
        last_agent_msg = ""
        for event in reversed(trace.events):
            if event.event_type == TraceEventType.AGENT_MESSAGE and event.content:
                last_agent_msg = event.content
                break

        # 遍历状态机规则进行匹配
        triggered_action = None
        for rule in self.state_transitions:
            from_state = rule.get("from_state")
            trigger_keyword = rule.get("trigger_keyword", "")
            if from_state == self.current_state or from_state == "*":
                if not trigger_keyword or trigger_keyword in last_agent_msg:
                    # 状态命中
                    self.current_state = rule.get("to_state", self.current_state)
                    goal_achieved = rule.get("goal_achieved")
                    if goal_achieved and goal_achieved not in self.completed_goals:
                        self.completed_goals.append(goal_achieved)

                    # 若规则定义了环境侧工具动作，真实在沙盒中执行 (双控核心能力)
                    env_tool = rule.get("env_tool")
                    if env_tool and self.sandbox:
                        tool_name = env_tool.get("name", "")
                        tool_args = env_tool.get("arguments", {})
                        sandbox_res = self.sandbox.execute_tool(tool_name, tool_args)
                        if self.emit:
                            self.emit(
                                TraceEvent(
                                    turn_index=turn_index,
                                    actor_role=ActorRole.USER_SIMULATOR,
                                    actor_name="dual_control_user",
                                    event_type=TraceEventType.TOOL_CALL_REQUEST,
                                    content=f"用户模拟器主动向环境执行工具操作: {tool_name}",
                                    metadata={"tool": tool_name, "result": sandbox_res},
                                )
                            )

                    content_reply = rule.get("reply", "好的，我已配合完成。")
                    should_stop = rule.get("stop", False) or len(self.completed_goals) == len(self.hidden_goals)

                    return ExaminerAction(
                        action_type="speak" if not should_stop else "terminate",
                        content=content_reply,
                        should_stop_eval=should_stop,
                        internal_state={
                            "fsm_state": self.current_state,
                            "completed_goals": list(self.completed_goals),
                        },
                    )

        # 默认温和追问
        return ExaminerAction(
            action_type="speak",
            content="请问我的请求还在处理中吗？",
            internal_state={"fsm_state": self.current_state, "completed_goals": list(self.completed_goals)},
        )
