from __future__ import annotations

import datetime
from typing import Any, Callable
from agent_test_hub.diagnostics import CausalAttributionEngine
from agent_test_hub.examiners import BaseExaminer, UserSimulator
from agent_test_hub.judges import JudicialCommittee
from agent_test_hub.metrics import BaseMetric
from agent_test_hub.schemas import (
    ActorRole,
    BinaryRubric,
    BinaryVerdict,
    EvaluationReport,
    ExecutionTrace,
    RadarDimension,
    TaskEvaluationResult,
    TaskSpec,
    ToolCallObservation,
    TraceEvent,
    TraceEventType,
)
from agent_test_hub_sandbox import BaseSandbox


class EvaluationRunner:
    """AgentTestHub 核心评测调度总线 (Event-Driven Orchestrator)"""

    def __init__(
        self,
        sandbox: BaseSandbox,
        committee: JudicialCommittee | None = None,
        metrics: list[BaseMetric] | None = None,
    ):
        self.sandbox = sandbox
        self.committee = committee or JudicialCommittee()
        self.metrics = metrics or []

    def run_task(
        self,
        task: TaskSpec,
        examiner: BaseExaminer,
        rubrics: list[BinaryRubric],
        testee_agent_fn: Callable[[str, ExecutionTrace], dict[str, Any]],
    ) -> TaskEvaluationResult:
        """执行单任务完整动态评测闭环
        
        Args:
            task: 任务规格定义
            examiner: 考官智能体 (如状态化用户模拟官)
            rubrics: 美团二元检查项列表
            testee_agent_fn: 被测 Agent 执行函数，接收 (user_prompt, trace)，返回 {'response': str, 'tool_calls': [...]}
        """
        # 1. 记录沙盒初始物理快照
        snap_initial = self.sandbox.snapshot()
        trace = ExecutionTrace(task_id=task.task_id)

        turn = 1
        max_turns = task.constraints.max_turns

        # 2. 交互博弈主循环 (Turn-based Evaluation Loop)
        while turn <= max_turns:
            # 考官动作决策
            action = examiner.act(trace, turn)

            # 记录考官发言事件
            trace.events.append(
                TraceEvent(
                    turn_index=turn,
                    actor_role=ActorRole.USER_SIMULATOR,
                    actor_name="examiner",
                    event_type=TraceEventType.USER_MESSAGE,
                    content=action.content,
                )
            )

            if action.should_stop_eval:
                break

            # 被测 Agent 执行响应
            agent_output = testee_agent_fn(action.content, trace)
            response_text = agent_output.get("response", "")
            tool_calls_req = agent_output.get("tool_calls", [])

            # 记录 Agent 思考或发言
            trace.events.append(
                TraceEvent(
                    turn_index=turn,
                    actor_role=ActorRole.TESTEE_AGENT,
                    actor_name="testee",
                    event_type=TraceEventType.AGENT_MESSAGE,
                    content=response_text,
                )
            )

            # 在沙盒中执行 Agent 调用的工具
            for call in tool_calls_req:
                tool_name = call.get("name", "")
                args = call.get("arguments", {})
                start_t = datetime.datetime.now()
                sandbox_res = self.sandbox.execute_tool(tool_name, args)
                duration = (datetime.datetime.now() - start_t).total_seconds() * 1000.0

                is_err = sandbox_res.get("status") == "error"
                trace.events.append(
                    TraceEvent(
                        turn_index=turn,
                        actor_role=ActorRole.TESTEE_AGENT,
                        actor_name="testee",
                        event_type=TraceEventType.TOOL_CALL_REQUEST,
                        tool_observation=ToolCallObservation(
                            tool_name=tool_name,
                            arguments=args,
                            output=sandbox_res,
                            is_error=is_err,
                            duration_ms=duration,
                        ),
                    )
                )

            turn += 1

        # 3. 记录沙盒最终物理快照与状态差分审计
        snap_final = self.sandbox.snapshot()
        delta = self.sandbox.compute_diff(snap_initial, snap_final)

        # 校验预期物理终态
        world_state_passed = True
        for exp in task.expected_world_states:
            # 简单检查是否有对应的修改记录
            matched = any(
                m.get("table") == exp.target_identifier
                for m in delta.modified_records
            )
            if not matched:
                world_state_passed = False

        # 4. 陪审团对美团二元 Rubric 进行合议裁决与辩论
        all_judgments = []
        unknown_count = 0
        rubric_passed = True

        for r in rubrics:
            verdict, judgments, dispute = self.committee.evaluate_rubric(r, trace)
            all_judgments.extend(judgments)
            if verdict == BinaryVerdict.UNKNOWN:
                unknown_count += 1
            if r.is_fatal and verdict != r.expected_verdict:
                rubric_passed = False
            elif verdict != r.expected_verdict:
                rubric_passed = False

        # 5. 综合判定与计算得分
        is_task_passed = world_state_passed and rubric_passed
        total_score = 1.0 if is_task_passed else (0.5 if world_state_passed else 0.0)

        # 6. 若失败，生成阿里 7-Hop 因果归因树
        attribution_tree = []
        if not is_task_passed:
            attribution_tree = CausalAttributionEngine.diagnose(
                task=task,
                trace=trace,
                judgments=all_judgments,
                world_state_passed=world_state_passed,
            )

        return TaskEvaluationResult(
            task_id=task.task_id,
            is_passed=is_task_passed,
            total_score=total_score,
            world_state_passed=world_state_passed,
            world_state_diff={"modified_records": delta.modified_records},
            rubric_judgments=all_judgments,
            unknown_rubric_count=unknown_count,
            attribution_tree=attribution_tree,
        )
