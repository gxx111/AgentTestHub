import pytest
from agent_test_hub.schemas import (
    TaskSpec,
    WorldStateExpectation,
    ExecutionTrace,
    RubricJudgment,
    BinaryVerdict,
)
from agent_test_hub.diagnostics import CausalAttributionEngine


def test_causal_tree_diagnose_safety_and_state_failure():
    """测试在安全红线被否决且状态差分未达成时的因果树推导"""
    task = TaskSpec(
        task_id="t_diag",
        scenario_id="s1",
        title="诊断测试",
        description="测试",
        initial_user_prompt="测试",
        expected_world_states=[
            WorldStateExpectation(
                target_identifier="orders",
                condition={"id": "1"},
                expected_values={"status": "REFUNDED"},
            )
        ],
    )

    trace = ExecutionTrace(task_id="t_diag")

    judgments = [
        RubricJudgment(
            rubric_id="chk_safety",
            judge_role="safety_judge",
            verdict=BinaryVerdict.NO,
            evidence_span_ids=["spn_001"],
            rationale="发现执行了未经授权的管理员指令",
        )
    ]

    nodes = CausalAttributionEngine.diagnose(
        task=task,
        trace=trace,
        judgments=judgments,
        world_state_passed=False,
    )

    assert len(nodes) >= 2
    # 校验是否命中了 Hop 7 安全节点
    stages = [n.hop_stage for n in nodes]
    assert "Hop7_Response_Safety" in stages
    assert "Hop5_Execution_State" in stages

    safety_node = [n for n in nodes if n.hop_stage == "Hop7_Response_Safety"][0]
    assert "负向约束" in safety_node.suggested_action
