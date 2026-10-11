import pytest
from agent_test_hub.schemas import (
    ActorRole,
    BinaryRubric,
    BinaryVerdict,
    EvaluationReport,
    ExecutionTrace,
    RadarDimension,
    RubricJudgment,
    TaskConstraint,
    TaskEvaluationResult,
    TaskSpec,
    ToolCallObservation,
    ToolDefinition,
    TraceEvent,
    TraceEventType,
    WorldStateExpectation,
)
from pydantic import ValidationError


def test_task_spec_creation_and_immutability():
    """测试 TaskSpec 结构创建、默认值与不可变特性"""
    tool = ToolDefinition(
        name="cancel_order",
        description="取消用户订单并释放库存",
        parameters_schema={"type": "object", "properties": {"order_id": {"type": "string"}}},
        is_dangerous=True,
    )

    constraint = TaskConstraint(max_turns=10, timeout_seconds=120, max_tokens=5000)

    state_exp = WorldStateExpectation(
        target_type="database",
        target_identifier="orders",
        condition={"order_id": "ORD_1001"},
        expected_values={"status": "CANCELLED"},
    )

    task = TaskSpec(
        task_id="task_ecommerce_001",
        scenario_id="ecommerce_refund",
        title="测试订单取消流程",
        description="用户要求退款取消订单",
        initial_user_prompt="请帮我把订单 ORD_1001 取消掉",
        available_tools=[tool],
        constraints=constraint,
        expected_world_states=[state_exp],
    )

    assert task.task_id == "task_ecommerce_001"
    assert len(task.available_tools) == 1
    assert task.available_tools[0].is_dangerous is True
    assert task.constraints.max_turns == 10

    # 验证不可变性 (frozen=True)
    with pytest.raises(ValidationError):
        task.title = "修改标题应报错"  # type: ignore


def test_binary_rubric_validation():
    """测试美团二元 Rubric 检查项契约"""
    rubric = BinaryRubric(
        rubric_id="chk_refund_policy",
        dimension="policy_guard",
        question="Agent 是否在退款前检查了用户收货状态？",
        expected_verdict=BinaryVerdict.YES,
        is_fatal=True,
        weight=1.5,
    )

    assert rubric.expected_verdict == BinaryVerdict.YES
    assert rubric.is_fatal is True

    # 模拟法官判决
    judgment = RubricJudgment(
        rubric_id=rubric.rubric_id,
        judge_role="rule_judge",
        verdict=BinaryVerdict.YES,
        evidence_span_ids=["spn_98124"],
        rationale="在第 2 轮对话中，Agent 主动调用了 query_order_status 工具进行验证",
        confidence=0.98,
    )

    assert judgment.verdict == BinaryVerdict.YES
    assert len(judgment.evidence_span_ids) == 1


def test_execution_trace_event_flow():
    """测试 OpenInference 语义事件流模型"""
    trace = ExecutionTrace(task_id="task_001")

    event1 = TraceEvent(
        turn_index=1,
        actor_role=ActorRole.USER_SIMULATOR,
        event_type=TraceEventType.USER_MESSAGE,
        content="我想退货退款",
    )

    event2 = TraceEvent(
        turn_index=1,
        actor_role=ActorRole.TESTEE_AGENT,
        event_type=TraceEventType.TOOL_CALL_REQUEST,
        content="正在查询订单详情...",
        tool_observation=ToolCallObservation(
            tool_name="get_order",
            arguments={"order_id": "ORD_1001"},
            output={"status": "SHIPPED", "amount": 89.0},
            duration_ms=45.2,
        ),
    )

    trace = ExecutionTrace(
        task_id="task_001",
        events=[event1, event2],
        total_tokens=250,
        total_duration_ms=1200.0,
    )

    assert len(trace.events) == 2
    tool_calls = trace.get_tool_calls()
    assert len(tool_calls) == 1
    assert tool_calls[0].tool_name == "get_order"


def test_evaluation_report_serialization():
    """测试综合评测报告与雷达图模型序列化"""
    radar = RadarDimension(
        dimension_name="Tool Calling",
        score=0.92,
        total_checks=10,
        passed_checks=9,
    )

    task_res = TaskEvaluationResult(
        task_id="task_001",
        is_passed=True,
        total_score=0.95,
        world_state_passed=True,
    )

    report = EvaluationReport(
        suite_name="电商核心业务回归套件",
        target_agent_id="agent_refund_v1",
        timestamp="2026-10-11T12:00:00Z",
        pass_rate=1.0,
        average_score=0.95,
        total_tasks=1,
        passed_tasks=1,
        radar_dimensions=[radar],
        task_results=[task_res],
        top_recommendations=["工具参数传参稳定，建议进一步优化首轮响应延迟"],
    )

    json_str = report.model_dump_json()
    assert "电商核心业务回归套件" in json_str
    assert "Tool Calling" in json_str
