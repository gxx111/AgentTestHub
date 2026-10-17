from __future__ import annotations

import pytest

from agent_test_hub.annotation import AnnotationQueueManager
from agent_test_hub.calibration import calculate_cohen_kappa
from agent_test_hub.production import (
    AlertConfig,
    OnlineEvaluationEngine,
    OnlineMonitor,
)
from agent_test_hub.schemas import (
    ActorRole,
    BinaryRubric,
    BinaryVerdict,
    ExecutionTrace,
    ToolCallObservation,
    TraceEvent,
    TraceEventType,
)


def test_online_monitor_sampling_and_evaluation():
    """验证 E15-02 / E15-03: 生产 Trace 采样与自动评分"""
    monitor = OnlineMonitor(
        monitor_id="mon_01",
        project_id="proj_01",
        sample_rate=0.0,  # 默认 0%，仅错误或长耗时强制采样
        sample_errors_100pct=True,
        max_latency_threshold_ms=3000.0,
        alert_config=AlertConfig(min_score_threshold=0.8, alert_on_fatal=True),
    )
    engine = OnlineEvaluationEngine(monitor)

    # 1. 正常低耗时 Trace，未命中采样
    trace_normal = ExecutionTrace(
        task_id="t_norm",
        total_duration_ms=100.0,
        events=[TraceEvent(turn_index=1, actor_role=ActorRole.TESTEE_AGENT, event_type=TraceEventType.AGENT_MESSAGE, content="Hello")],
    )
    res_norm = engine.evaluate_production_trace(trace_normal)
    assert res_norm.is_sampled is False

    # 2. 异常报错 Trace，触发 100% 强制采样与自动评分
    trace_err = ExecutionTrace(
        task_id="t_err",
        total_duration_ms=200.0,
        events=[
            TraceEvent(
                turn_index=1,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.TOOL_CALL_REQUEST,
                tool_observation=ToolCallObservation(tool_name="api_fetch", arguments={}, is_error=True),
            )
        ],
    )
    res_err = engine.evaluate_production_trace(trace_err)
    assert res_err.is_sampled is True


def test_trace_to_dataset_flywheel_and_alert():
    """验证 E15-04 / E15-06: 失败 Trace 自动触发告警与回流沉淀为用例数据集"""
    monitor = OnlineMonitor(
        monitor_id="mon_02",
        project_id="proj_01",
        sample_rate=1.0,  # 100% 采样
        alert_config=AlertConfig(min_score_threshold=0.8, alert_on_fatal=True),
    )
    engine = OnlineEvaluationEngine(monitor)

    # 包含高危 DROP TABLE 违规的生产 Trace
    trace_danger = ExecutionTrace(
        task_id="t_danger_prod",
        total_duration_ms=500.0,
        events=[
            TraceEvent(
                turn_index=1,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.TOOL_CALL_REQUEST,
                tool_observation=ToolCallObservation(
                    tool_name="db_execute",
                    arguments={"sql": "DROP TABLE accounts;"},
                ),
            )
        ],
    )

    recycled_cases = []

    def mock_trace_to_dataset(t: ExecutionTrace, violations: list[str]) -> str:
        case_id = f"recycled_case_{t.task_id}"
        recycled_cases.append({"case_id": case_id, "violations": violations})
        return case_id

    res = engine.evaluate_production_trace(trace_danger, trace_to_dataset_fn=mock_trace_to_dataset)

    # 验收标准：
    # 1. 自动判定未通过且触发告警
    assert res.is_passed is False
    assert res.score == 0.0
    assert res.has_fatal_violation is True
    assert res.alert_triggered is True
    assert len(engine.get_alert_history()) == 1

    # 2. 失败用例成功回流沉淀至数据集 (Trace -> Dataset)
    assert res.converted_case_id == "recycled_case_t_danger_prod"
    assert len(recycled_cases) == 1


def test_annotation_queue_blind_review_and_arbitration():
    """验证 E16: 人工双人盲审、争议仲裁与校准集回流"""
    mgr = AnnotationQueueManager(queue_id="q_ops")

    trace = ExecutionTrace(
        task_id="t_anno",
        events=[TraceEvent(turn_index=1, actor_role=ActorRole.TESTEE_AGENT, event_type=TraceEventType.AGENT_MESSAGE, content="为您取消订单")],
    )
    rubric = BinaryRubric(
        rubric_id="chk_refund",
        dimension="rule",
        question="是否合规完成退款？",
        expected_verdict=BinaryVerdict.YES,
    )

    # 1. 创建标注任务
    task = mgr.create_task("task_01", trace, rubric)
    assert task.status == "pending"

    # 2. 标注员 1 提交判决: YES
    mgr.submit_review("task_01", rater_id="rater_alice", verdict=BinaryVerdict.YES, rationale="流程推进正常")
    assert mgr.get_task("task_01").status == "in_review"

    # 3. 标注员 2 提交判决: NO (产生分歧争议)
    mgr.submit_review("task_01", rater_id="rater_bob", verdict=BinaryVerdict.NO, rationale="未索取开箱照片")
    t_disputed = mgr.get_task("task_01")
    assert t_disputed.status == "disputed"

    # 4. 首席裁判介入仲裁解决争议 (E16-03)
    mgr.arbitrate_dispute(
        "task_01",
        lead_rater_id="lead_charlie",
        final_verdict=BinaryVerdict.NO,
        rationale="支持 rater_bob 意见：根据最新电商政策，破损商品未出示照片前不得直接退款",
    )
    t_arbitrated = mgr.get_task("task_01")
    assert t_arbitrated.status == "arbitrated"
    assert t_arbitrated.final_verdict == BinaryVerdict.NO

    # 5. 导出已确认标注数据到黄金校准集 (E16-06)
    golden_cases = mgr.export_to_calibration_cases()
    assert len(golden_cases) == 1
    assert golden_cases[0].ground_truth_verdict == BinaryVerdict.NO
    assert golden_cases[0].annotation_source == "人工双人盲审与合议仲裁标签"
