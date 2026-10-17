from __future__ import annotations

import json
from pathlib import Path
import pytest
import yaml

from agent_test_hub.reports import (
    EvidencePackage,
    EvidenceSigner,
    OfflineHTMLReportRenderer,
)
from agent_test_hub.schemas import (
    BinaryVerdict,
    RubricJudgment,
    TaskEvaluationResult,
)


def test_evidence_package_signing_and_verification():
    """验证 E17-03: 证据包数字签名生成与防篡改核验"""
    task = TaskEvaluationResult(
        task_id="enterprise_task_01",
        is_passed=True,
        total_score=1.0,
        world_state_passed=True,
        world_state_diff={},
        rubric_judgments=[
            RubricJudgment(
                rubric_id="r1",
                judge_role="rule_judge",
                verdict=BinaryVerdict.YES,
                rationale="合规完成操作",
            )
        ],
    )

    signing_key = "corp_secret_key_2026"

    # 1. 生成带数字签名的证据包
    pkg = EvidenceSigner.create_signed_package(task, signing_key=signing_key)
    assert pkg.manifest.package_id.startswith("pkg_")
    assert pkg.manifest.pass_rate == 1.0
    assert len(pkg.manifest.signature) == 64  # SHA256 hex digest

    # 2. 正常核验签名
    ok, msg = EvidenceSigner.verify_package(pkg, signing_key=signing_key)
    assert ok is True
    assert "签名有效且数据完整" in msg

    # 3. 错误密钥核验失败
    ok_bad_key, msg_bad_key = EvidenceSigner.verify_package(pkg, signing_key="wrong_secret")
    assert ok_bad_key is False
    assert "数字签名核验失败" in msg_bad_key

    # 4. 篡改 Payload 内容后核验失败 (防数据篡改)
    tampered_tasks = list(pkg.task_results)
    tampered_tasks[0]["total_score"] = 0.1
    tampered_pkg = EvidencePackage(
        manifest=pkg.manifest,
        task_results=tampered_tasks,
        top_recommendations=pkg.top_recommendations,
    )
    ok_tamper, msg_tamper = EvidenceSigner.verify_package(tampered_pkg, signing_key=signing_key)
    assert ok_tamper is False
    assert "内容哈希校验失败" in msg_tamper


def test_offline_html_report_rendering(tmp_path: Path):
    """验证 E17-02 / E17-06: 自包含离线 HTML 报告渲染与脱机可读性"""
    task = TaskEvaluationResult(
        task_id="task_html_01",
        is_passed=True,
        total_score=0.95,
        world_state_passed=True,
        world_state_diff={},
        rubric_judgments=[],
        total_duration_ms=450.0,
    )

    pkg = EvidenceSigner.create_signed_package(task)
    html = OfflineHTMLReportRenderer.render(pkg, is_verified=True)

    # 校验 HTML 自包含要素
    assert "<!DOCTYPE html>" in html
    assert "VERIFIED SIGNATURE" in html
    assert "task_html_01" in html
    assert pkg.manifest.package_id in html
    assert "自包含脱机文档" in html

    # 保存并在离线文件路径检验
    html_file = tmp_path / "offline_report.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html)
    assert html_file.exists()
    assert html_file.stat().st_size > 1000


def test_deployment_configs_integrity():
    """验证 E20: Docker Compose 与 Helm Chart 配置文件完整性"""
    compose_path = Path("deploy/compose/docker-compose.yml")
    assert compose_path.exists()
    with open(compose_path, encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)
    services = compose_data.get("services", {})
    assert "postgres" in services
    assert "redis" in services
    assert "api" in services
    assert "web" in services

    chart_path = Path("deploy/helm/agent-test-hub/Chart.yaml")
    assert chart_path.exists()
    with open(chart_path, encoding="utf-8") as f:
        chart_data = yaml.safe_load(f)
    assert chart_data["name"] == "agent-test-hub"

    values_path = Path("deploy/helm/agent-test-hub/values.yaml")
    assert values_path.exists()
    with open(values_path, encoding="utf-8") as f:
        values_data = yaml.safe_load(f)
    assert "replicaCount" in values_data
