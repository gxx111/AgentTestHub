from __future__ import annotations

import json
from pathlib import Path
import pytest
from click.testing import CliRunner

from agent_test_hub.schemas import (
    ActorRole,
    BinaryRubric,
    BinaryVerdict,
    ExecutionTrace,
    SeverityLevel,
    TaskEvaluationResult,
    TaskSpec,
    ToolCallObservation,
    TraceEvent,
    TraceEventType,
    WorldStateExpectation,
)
from agent_test_hub.telemetry import OTelGenAISpanExporter, sanitize_sensitive_data
from agent_test_hub_cli.main import cli
from agent_test_hub_domain.gate import (
    GateDecisionType,
    GatePolicy,
    ReleaseGateEvaluator,
)
from agent_test_hub_sdk import (
    AgentTestHubClient,
    LangChainAdapter,
    OpenAICompatAdapter,
    assert_gate_passed,
    assert_no_pii_leaked,
    assert_sql_safety,
)


def test_sdk_local_evaluation_and_gate_check():
    """验证 E13-01: Python SDK 10 分钟快速跑通本地评测与门禁检查"""
    client = AgentTestHubClient()

    task = TaskSpec(
        task_id="sdk_test_task",
        scenario_id="sdk_demo",
        title="SDK 订单取消评测",
        description="Demo",
        initial_user_prompt="请帮我取消订单 ORD_SDK_1",
        expected_world_states=[
            WorldStateExpectation(
                target_identifier="orders",
                condition={"order_id": "ORD_SDK_1"},
                expected_values={"status": "CANCELLED"},
            )
        ],
    )
    rubrics = [
        BinaryRubric(
            rubric_id="chk_cancel_action",
            dimension="rule_compliance",
            question="Agent 是否执行了订单取消？",
            expected_verdict=BinaryVerdict.YES,
            severity=SeverityLevel.HIGH,
        )
    ]

    def testee_agent(prompt: str, trace):
        return {
            "response": "已帮您取消订单 ORD_SDK_1",
            "tool_calls": [
                {
                    "name": "db_execute",
                    "arguments": {"sql": "UPDATE orders SET status = 'CANCELLED' WHERE order_id = 'ORD_SDK_1';"},
                }
            ],
        }

    init_sql = [
        "CREATE TABLE orders (order_id TEXT PRIMARY KEY, status TEXT);",
        "INSERT INTO orders VALUES ('ORD_SDK_1', 'PAID');",
    ]

    result = client.evaluate(task, rubrics, testee_agent, init_sql=init_sql)
    assert result.is_passed is True
    assert result.world_state_passed is True

    # 门禁检查
    decision = client.check_release_gate(result)
    assert decision.decision == GateDecisionType.PASS
    assert decision.is_blocked is False

    # pytest 断言插件辅助函数
    assert_gate_passed(result)
    assert_sql_safety(result)


def test_framework_adapters():
    """验证 E11 / E13: 框架适配器 (LangChain / OpenAICompat)"""
    # 1. LangChain / LangGraph 适配
    class MockLangChainRunnable:
        def invoke(self, input_dict):
            return {"output": f"Processed: {input_dict.get('input')}"}

    lc_adapter = LangChainAdapter(MockLangChainRunnable())
    res_lc = lc_adapter("Hello LangChain", ExecutionTrace(task_id="t_lc"))
    assert "Processed: Hello LangChain" in res_lc["response"]

    # 2. OpenAI 兼容 / Webhook 适配
    raw_adapter = OpenAICompatAdapter(lambda p: f"Echo: {p}")
    res_raw = raw_adapter("Ping", ExecutionTrace(task_id="t_raw"))
    assert res_raw["response"] == "Echo: Ping"


def test_otel_span_exporter_and_sanitization(tmp_path: Path):
    """验证 E11-01 ~ E11-05: OTel GenAI 标准 Trace 导出与脱敏"""
    trace = ExecutionTrace(
        task_id="t_otel",
        events=[
            TraceEvent(
                turn_index=1,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.AGENT_MESSAGE,
                content="这是您的手机号 13812345678 和密钥 sk-abcdef12345678901234567890",
            ),
            TraceEvent(
                turn_index=2,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.TOOL_CALL_REQUEST,
                tool_observation=ToolCallObservation(
                    tool_name="api_call",
                    arguments={"auth": "Bearer secret_token_1234567890", "password": "super_secret"},
                    duration_ms=45.0,
                ),
            ),
        ],
    )

    # 验证脱敏函数
    sanitized = sanitize_sensitive_data("密钥 sk-12345678901234567890, 电话 13912345678, 密码 \"password\": \"my_pass\"")
    assert "139****5678" in sanitized
    assert "******" in sanitized

    # 导出 OTLP 格式
    otlp_data = OTelGenAISpanExporter.to_otlp_resource_spans(trace)
    assert "resourceSpans" in otlp_data
    spans = otlp_data["resourceSpans"][0]["scopeSpans"][0]["spans"]
    assert len(spans) == 2
    assert spans[0]["name"] == "gen_ai.chat"
    assert spans[1]["name"] == "gen_ai.tool_call.api_call"

    # 文件导出验证
    out_file = tmp_path / "otel_trace.json"
    OTelGenAISpanExporter.export_to_file(trace, out_file.as_posix())
    assert out_file.exists()


def test_ci_gate_blocking_and_pr_comment():
    """验证 E14-02: 门禁阻断与 PR 评论生成"""
    failed_result = TaskEvaluationResult(
        task_id="task_fail",
        is_passed=False,
        total_score=0.4,
        world_state_passed=False,
        world_state_diff={},
        rubric_judgments=[],
        total_duration_ms=100.0,
    )

    policy = GatePolicy(min_pass_rate=0.95)
    decision = ReleaseGateEvaluator.evaluate(failed_result, policy=policy)

    assert decision.decision == GateDecisionType.BLOCK
    assert decision.is_blocked is True
    assert len(decision.reasons) >= 1
    assert "门禁已拦截" in decision.pr_comment_markdown
    assert "<testsuite" in decision.junit_xml


def test_ath_cli_commands(tmp_path: Path):
    """验证 E13-02: ath init / eval / gate 命令行跑通"""
    runner = CliRunner()

    # 1. ath init
    target_dir = tmp_path / "quickstart"
    init_res = runner.invoke(cli, ["init", "-d", target_dir.as_posix()])
    assert init_res.exit_code == 0
    assert (target_dir / "suite.yaml").exists()

    # 2. ath eval
    suite_file = target_dir / "suite.yaml"
    report_file = tmp_path / "report.json"
    junit_file = tmp_path / "junit.xml"
    otel_file = tmp_path / "otel.json"

    eval_res = runner.invoke(
        cli,
        [
            "eval",
            suite_file.as_posix(),
            "-o",
            report_file.as_posix(),
            "--junit-xml",
            junit_file.as_posix(),
            "--otel-export",
            otel_file.as_posix(),
        ],
    )
    assert eval_res.exit_code == 0
    assert report_file.exists()
    assert junit_file.exists()
    assert otel_file.exists()

    # 3. ath gate
    gate_res = runner.invoke(cli, ["gate", report_file.as_posix()])
    assert gate_res.exit_code == 0
    assert "发布门禁评审报告" in gate_res.output
