import pytest
from agent_test_hub.schemas import ExecutionTrace, TraceEvent, ActorRole, TraceEventType, ToolCallObservation
from agent_test_hub.metrics import (
    ToolArgumentASTMetric,
    FaultRecoveryMetric,
    LivelockDetectionMetric,
    CommunicationSNRMetric,
    MASDeadlockDetectorMetric,
)


def test_hop4_tool_argument_ast_validation():
    """测试 Hop 4: 工具参数 AST 语法树结构校验"""
    metric = ToolArgumentASTMetric(
        required_schema={"cancel_order": {"order_id": "str", "refund_amount": "int"}}
    )

    # 1. 构造合法参数 Trace
    trace_valid = ExecutionTrace(
        task_id="t1",
        events=[
            TraceEvent(
                turn_index=1,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.TOOL_CALL_REQUEST,
                tool_observation=ToolCallObservation(
                    tool_name="cancel_order",
                    arguments={"order_id": "ORD_1001", "refund_amount": 100},
                ),
            )
        ],
    )
    res_valid = metric.evaluate(trace_valid)
    assert res_valid.is_passed is True
    assert res_valid.score == 1.0

    # 2. 构造类型违规 Trace (refund_amount 传成了字符串 "100")
    trace_invalid = ExecutionTrace(
        task_id="t2",
        events=[
            TraceEvent(
                turn_index=1,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.TOOL_CALL_REQUEST,
                tool_observation=ToolCallObservation(
                    tool_name="cancel_order",
                    arguments={"order_id": "ORD_1001", "refund_amount": "100"},
                ),
            )
        ],
    )
    res_invalid = metric.evaluate(trace_invalid)
    assert res_invalid.is_passed is False
    assert res_invalid.score == 0.0


def test_hop5_fault_recovery_metric():
    """测试 Hop 5: 故障恢复率度量"""
    metric = FaultRecoveryMetric()

    # 构造一次报错后成功重试恢复的 Trace
    trace = ExecutionTrace(
        task_id="t1",
        events=[
            TraceEvent(
                turn_index=1,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.TOOL_CALL_REQUEST,
                tool_observation=ToolCallObservation(
                    tool_name="fetch_api", arguments={}, is_error=True
                ),
            ),
            TraceEvent(
                turn_index=2,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.TOOL_CALL_REQUEST,
                tool_observation=ToolCallObservation(
                    tool_name="fetch_api", arguments={"retry": True}, is_error=False
                ),
            ),
        ],
    )
    res = metric.evaluate(trace)
    assert res.is_passed is True
    assert res.score == 1.0


def test_mas_communication_snr_and_deadlock():
    """测试 MAS 多智能体通信信噪比与死锁环检测"""
    snr_metric = CommunicationSNRMetric(min_valid_ratio=0.5)

    # 构造含闲聊的团队会话
    trace = ExecutionTrace(
        task_id="mas_01",
        events=[
            TraceEvent(
                turn_index=1,
                actor_role=ActorRole.TESTEE_AGENT,
                actor_name="Agent_A",
                event_type=TraceEventType.AGENT_MESSAGE,
                content="请分析数据库慢查询原因",
            ),
            TraceEvent(
                turn_index=2,
                actor_role=ActorRole.TESTEE_AGENT,
                actor_name="Agent_B",
                event_type=TraceEventType.AGENT_MESSAGE,
                content="收到",  # 闲聊
            ),
            TraceEvent(
                turn_index=3,
                actor_role=ActorRole.TESTEE_AGENT,
                actor_name="Agent_A",
                event_type=TraceEventType.AGENT_MESSAGE,
                content="好的",  # 闲聊
            ),
            TraceEvent(
                turn_index=4,
                actor_role=ActorRole.TESTEE_AGENT,
                actor_name="Agent_B",
                event_type=TraceEventType.AGENT_MESSAGE,
                content="分析结果：缺少 (user_id, status) 复合索引",
            ),
        ],
    )
    res_snr = snr_metric.evaluate(trace)
    assert res_snr.score == 0.5  # 4条消息中2条有效
    assert res_snr.is_passed is True

    # 测试死锁检测 (Agent_A 与 Agent_B 反复死锁循环)
    deadlock_metric = MASDeadlockDetectorMetric(min_cycle_weight=2)
    trace_deadlock = ExecutionTrace(
        task_id="mas_deadlock",
        events=[
            TraceEvent(actor_role=ActorRole.TESTEE_AGENT, actor_name="A", event_type=TraceEventType.AGENT_MESSAGE, content="等你输出"),
            TraceEvent(actor_role=ActorRole.TESTEE_AGENT, actor_name="B", event_type=TraceEventType.AGENT_MESSAGE, content="等你输出"),
            TraceEvent(actor_role=ActorRole.TESTEE_AGENT, actor_name="A", event_type=TraceEventType.AGENT_MESSAGE, content="等你输出"),
            TraceEvent(actor_role=ActorRole.TESTEE_AGENT, actor_name="B", event_type=TraceEventType.AGENT_MESSAGE, content="等你输出"),
            TraceEvent(actor_role=ActorRole.TESTEE_AGENT, actor_name="A", event_type=TraceEventType.AGENT_MESSAGE, content="等你输出"),
        ],
    )
    res_deadlock = deadlock_metric.evaluate(trace_deadlock)
    assert res_deadlock.is_passed is False
    assert res_deadlock.score == 0.0
