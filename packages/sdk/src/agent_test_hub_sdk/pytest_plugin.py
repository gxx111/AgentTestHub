from __future__ import annotations

import pytest

from agent_test_hub.schemas import TaskEvaluationResult
from agent_test_hub_domain.gate import GateDecisionType, GatePolicy, ReleaseGateEvaluator

from .client import AgentTestHubClient


@pytest.fixture
def agent_eval_client() -> AgentTestHubClient:
    """提供开箱即用的 AgentTestHub 本地测试客户端 Fixture (E13-03)"""
    return AgentTestHubClient()


def assert_gate_passed(
    result: TaskEvaluationResult | list[TaskEvaluationResult],
    policy: GatePolicy | None = None,
) -> None:
    """断言发布门禁通过，若被阻断则抛出格式化错误信息与证据链详情 (E13-03)"""
    decision = ReleaseGateEvaluator.evaluate(result, policy=policy)
    if decision.decision != GateDecisionType.PASS:
        reasons_text = "\n  - ".join(decision.reasons)
        pytest.fail(
            f"\n[Release Gate Blocked] 发布门禁被阻断：\n  - {reasons_text}\n\n"
            f"详细 PR 评审报告：\n{decision.pr_comment_markdown}"
        )


def assert_sql_safety(result: TaskEvaluationResult) -> None:
    """断言评测过程中未触发任何高危 SQL 注入或越权操作"""
    for j in result.rubric_judgments:
        if j.judge_role == "safety_judge" and j.verdict.value == "NO":
            pytest.fail(f"SQL 安全红线未通过：{j.rationale}")


def assert_no_pii_leaked(result: TaskEvaluationResult) -> None:
    """断言评测过程中无敏感 PII 泄露"""
    for event in result.trace.events if result.trace else []:
        if "PII" in str(event.content) or "敏感数据泄漏" in str(event.content):
            pytest.fail(f"发现敏感数据泄漏: {event.content}")
