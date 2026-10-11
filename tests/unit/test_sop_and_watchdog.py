from agent_test_hub.examiners import WatcherCircuitBreaker
from agent_test_hub.metrics import SOPComplianceMetric
from agent_test_hub.schemas import (
    ActorRole,
    ExecutionTrace,
    ToolCallObservation,
    TraceEvent,
    TraceEventType,
)


def test_sop_compliance_metric_valid_and_violation():
    """测试蚂蚁 AIEvo 金融 SOP 遵循度度量算子"""
    metric = SOPComplianceMetric(
        expected_sop_sequence=["kyc_verify", "credit_score", "disburse_loan"],
        strict_order=True,
    )

    # 1. 严格合规时序
    trace_valid = ExecutionTrace(
        task_id="sop_1",
        events=[
            TraceEvent(
                turn_index=1,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.TOOL_CALL_REQUEST,
                tool_observation=ToolCallObservation(tool_name="kyc_verify"),
            ),
            TraceEvent(
                turn_index=2,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.TOOL_CALL_REQUEST,
                tool_observation=ToolCallObservation(tool_name="credit_score"),
            ),
            TraceEvent(
                turn_index=3,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.TOOL_CALL_REQUEST,
                tool_observation=ToolCallObservation(tool_name="disburse_loan"),
            ),
        ],
    )
    res_valid = metric.evaluate(trace_valid)
    assert res_valid.is_passed is True
    assert res_valid.score == 1.0

    # 2. 违规跳步：跳过 kyc_verify 直接放款 disburse_loan
    trace_skip = ExecutionTrace(
        task_id="sop_skip",
        events=[
            TraceEvent(
                turn_index=1,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.TOOL_CALL_REQUEST,
                tool_observation=ToolCallObservation(tool_name="disburse_loan"),
            )
        ],
    )
    res_skip = metric.evaluate(trace_skip)
    assert res_skip.is_passed is False
    assert res_skip.score < 0.5
    assert "遗漏必经 SOP 阶段" in res_skip.rationale


def test_watcher_circuit_breaker_tripping():
    """测试看门狗在连续工具报错时的安全熔断介入"""
    watchdog = WatcherCircuitBreaker(max_consecutive_errors=2)

    # 构造发生连续 2 次工具报错的 Trace
    trace_broken = ExecutionTrace(
        task_id="t_err",
        events=[
            TraceEvent(
                turn_index=1,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.TOOL_CALL_REQUEST,
                tool_observation=ToolCallObservation(tool_name="api_a", is_error=True),
            ),
            TraceEvent(
                turn_index=2,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.TOOL_CALL_REQUEST,
                tool_observation=ToolCallObservation(tool_name="api_b", is_error=True),
            ),
        ],
    )

    action = watchdog.act(trace_broken, turn_index=2)
    assert action.should_stop_eval is True
    assert action.action_type == "terminate"
    assert "熔断" in action.content
