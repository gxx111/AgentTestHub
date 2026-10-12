from __future__ import annotations

from agent_test_hub.schemas import ExecutionTrace, TraceEventType

from .base import BaseExaminer, ExaminerAction


class UserSimulator(BaseExaminer):
    """状态化用户模拟官 (Stateful User Simulator with Hidden Goal FSM)

    不同于死板的单句 Prompt，模拟真实用户：
    1. 拥有不可见的隐藏诉求 (Hidden Goal)；
    2. 根据被测 Agent 的提问状态机，分阶段释放意图 (Information Phasing)；
    3. 支持中途模拟用户产生情绪变化或需求微调。
    """

    role: str = "user_simulator"

    def __init__(
        self,
        persona: str,
        initial_message: str,
        hidden_goals: list[str],
        clarification_triggers: dict[str, str] | None = None,
        max_turns: int = 10,
    ):
        self.persona = persona
        self.initial_message = initial_message
        self.hidden_goals = hidden_goals
        # 触发词与隐藏信息释放映射: {"凭证/开箱": "我这里有快递破损照片和开箱视频"}
        self.clarification_triggers = clarification_triggers or {}
        self.max_turns = max_turns
        self._revealed_goals: set[str] = set()

    def act(self, trace: ExecutionTrace, turn_index: int) -> ExaminerAction:
        if turn_index == 1:
            return ExaminerAction(
                action_type="speak",
                content=self.initial_message,
                internal_state={"revealed_goals": list(self._revealed_goals)},
            )

        if turn_index >= self.max_turns:
            return ExaminerAction(
                action_type="terminate",
                content="轮次已达上限，结束对话",
                should_stop_eval=True,
            )

        # 检查 Agent 最后一轮说了什么
        agent_messages = [
            e.content for e in trace.events if e.event_type == TraceEventType.AGENT_MESSAGE
        ]
        last_agent_msg = agent_messages[-1] if agent_messages else ""

        # 匹配触发词释放下一个隐藏意图
        for trigger_kw, reveal_content in self.clarification_triggers.items():
            if trigger_kw in last_agent_msg and trigger_kw not in self._revealed_goals:
                self._revealed_goals.add(trigger_kw)
                return ExaminerAction(
                    action_type="speak",
                    content=reveal_content,
                    internal_state={"revealed_goals": list(self._revealed_goals)},
                )

        # 若 Agent 已完成操作或致歉
        if any(
            w in last_agent_msg
            for w in [
                "已为您办理",
                "成功办理",
                "已退款",
                "退款成功",
                "退款取消",
                "处理完毕",
                "成功取消",
                "拦截",
                "拒绝执行",
                "无法为您办理",
            ]
        ):
            return ExaminerAction(
                action_type="terminate",
                content="收到答复，测试交互结束。",
                should_stop_eval=True,
            )

        # 默认继续施压与追问
        return ExaminerAction(
            action_type="speak",
            content=f"请问我的诉求到底能不能解决？{self.persona}已经等了很久了！",
            internal_state={"revealed_goals": list(self._revealed_goals)},
        )
