from __future__ import annotations

from agent_test_hub.schemas import (
    AttributionNode,
    BinaryVerdict,
    ExecutionTrace,
    RubricJudgment,
    TaskSpec,
)


class CausalAttributionEngine:
    """阿里 7-Hop 故障因果归因树引擎 (Causal Root-Cause Attribution Engine)

    在测试用例未通过时，沿着 7-Hop 执行拓扑逆向回溯，定位最根本诱因并输出针对性行动建议：
    Hop1/2: 意图与规划阶段失效 ➔ 建议补充负向提示词
    Hop4:   参数 AST 校验失败   ➔ 建议修正参数类型定义或增强模型输出格式强转
    Hop5:   工具执行报错未恢复 ➔ 建议实现指数退避重试或降级兜底方案
    Hop7:   触碰安全红线       ➔ 建议在提示词中追加最高优先级系统防御前缀
    """

    @classmethod
    def diagnose(
        cls,
        task: TaskSpec,
        trace: ExecutionTrace,
        judgments: list[RubricJudgment],
        world_state_passed: bool,
    ) -> list[AttributionNode]:
        nodes: list[AttributionNode] = []

        # 1. 检查是否存在安全红线被否决
        safety_failures = [
            j for j in judgments if j.judge_role == "safety_judge" and j.verdict == BinaryVerdict.NO
        ]
        if safety_failures:
            f = safety_failures[0]
            nodes.append(
                AttributionNode(
                    node_id="attr_hop7_safety",
                    hop_stage="Hop7_Response_Safety",
                    failure_category="触碰安全合规红线 / 疑似提示词越权注入",
                    evidence_span_id=f.evidence_span_ids[0] if f.evidence_span_ids else None,
                    root_cause_explanation=f"安全法官判定违规: {f.rationale}",
                    suggested_action="【立即修复】在 Agent System Prompt 首部增加安全负向约束，且对危险工具增加执行审批拦截器",
                )
            )

        # 2. 检查工具参数 AST 校验
        tool_calls = trace.get_tool_calls()
        for call in tool_calls:
            if not isinstance(call.arguments, dict) or len(call.arguments) == 0:
                nodes.append(
                    AttributionNode(
                        node_id="attr_hop4_ast",
                        hop_stage="Hop4_Argument_AST",
                        failure_category="工具参数结构异常 / 缺失参数字典",
                        root_cause_explanation=f"工具 {call.tool_name} 被调用时未传入有效参数字典",
                        suggested_action="【参数修复】更新工具 Description 中的 JSON Schema 示例，强化参数必填说明",
                    )
                )

        # 3. 检查物理世界终态是否未达成
        if not world_state_passed and task.expected_world_states:
            exp = task.expected_world_states[0]
            nodes.append(
                AttributionNode(
                    node_id="attr_world_state_mismatch",
                    hop_stage="Hop5_Execution_State",
                    failure_category="物理沙盒状态差分未达成预期目标",
                    root_cause_explanation=f"目标表 '{exp.target_identifier}' 未能成功将数据更新为 {exp.expected_values}",
                    suggested_action="【业务修复】检查 Agent 工具调用是否真正 commit 了数据库事务，确认 SQL 条件语句是否完全匹配",
                )
            )

        # 4. 检查是否发生轮次耗尽但未解决问题
        if len(trace.events) >= task.constraints.max_turns:
            nodes.append(
                AttributionNode(
                    node_id="attr_hop6_timeout",
                    hop_stage="Hop6_Memory_Planning",
                    failure_category="达到最大会话轮次上限 (规划死锁或沟通低效)",
                    root_cause_explanation="多轮交互未能在规定轮次内收敛，存在反复无效提问",
                    suggested_action="【规划优化】缩减多轮提示词上下文，增强 Agent 在第 1 轮主动索取关键信息的主动性",
                )
            )

        return nodes
