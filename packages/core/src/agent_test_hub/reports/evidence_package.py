from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agent_test_hub.schemas import EvaluationReport, TaskEvaluationResult


class EvidencePackageManifest(BaseModel):
    """E17-03: 证据包元数据清单与防篡改指纹"""

    model_config = ConfigDict(frozen=True)

    package_id: str
    suite_name: str
    target_agent_id: str
    timestamp: str
    total_tasks: int
    passed_tasks: int
    pass_rate: float
    average_score: float
    content_sha256: str
    signature: str
    signature_algorithm: str = "HMAC-SHA256"


class EvidencePackage(BaseModel):
    """E17-01: 可验证离线证据包 (Signed Evidence Package)"""

    model_config = ConfigDict(frozen=True)

    manifest: EvidencePackageManifest
    task_results: list[dict[str, Any]] = Field(default_factory=list)
    top_recommendations: list[str] = Field(default_factory=list)


class EvidenceSigner:
    """证据包数字签名与真伪核验引擎 (E17-03 / E17-07)"""

    @classmethod
    def create_signed_package(
        cls,
        report_or_results: EvaluationReport | list[TaskEvaluationResult] | TaskEvaluationResult,
        signing_key: str = "ath_default_enterprise_signing_secret_2026",
        suite_name: str = "Enterprise Release Gate Audit",
        agent_id: str = "target_agent_v1",
    ) -> EvidencePackage:
        import uuid
        from datetime import datetime, timezone

        if isinstance(report_or_results, TaskEvaluationResult):
            tasks = [report_or_results]
        elif isinstance(report_or_results, list):
            tasks = report_or_results
        else:
            tasks = report_or_results.task_results
            suite_name = report_or_results.suite_name or suite_name
            agent_id = report_or_results.target_agent_id or agent_id

        total_tasks = len(tasks)
        passed_tasks = sum(1 for t in tasks if t.is_passed)
        pass_rate = (passed_tasks / total_tasks) if total_tasks > 0 else 0.0
        avg_score = (sum(t.total_score for t in tasks) / total_tasks) if total_tasks > 0 else 0.0

        # 按 severity 严重度对失败任务排序 (E17-04: CRITICAL > HIGH > MEDIUM > LOW)
        severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        def sort_key(t: TaskEvaluationResult) -> tuple[int, int]:
            if t.is_passed:
                return (1, 0)
            # 找到最高违规 severity
            worst_sev = 3
            for j in t.rubric_judgments:
                if j.verdict.value == "NO":
                    worst_sev = min(worst_sev, 0 if j.judge_role == "safety_judge" else 1)
            return (0, worst_sev)

        sorted_tasks = sorted(tasks, key=sort_key)
        tasks_dump = [t.model_dump(mode="json") for t in sorted_tasks]

        # 规范化计算 Payload 的 SHA-256 哈希
        payload_bytes = json.dumps(tasks_dump, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        content_sha256 = hashlib.sha256(payload_bytes).hexdigest()

        # 生成数字签名
        sig = hmac.new(signing_key.encode("utf-8"), content_sha256.encode("utf-8"), hashlib.sha256).hexdigest()

        manifest = EvidencePackageManifest(
            package_id=f"pkg_{uuid.uuid4().hex[:12]}",
            suite_name=suite_name,
            target_agent_id=agent_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_tasks=total_tasks,
            passed_tasks=passed_tasks,
            pass_rate=round(pass_rate, 4),
            average_score=round(avg_score, 4),
            content_sha256=content_sha256,
            signature=sig,
            signature_algorithm="HMAC-SHA256",
        )

        return EvidencePackage(
            manifest=manifest,
            task_results=tasks_dump,
            top_recommendations=["建议针对失败检查项审查 Prompt 上下文与约束边界"],
        )

    @classmethod
    def verify_package(
        cls,
        package: EvidencePackage,
        signing_key: str = "ath_default_enterprise_signing_secret_2026",
    ) -> tuple[bool, str]:
        """验证证据包签名与内容完整性，检测是否被外部篡改 (E17-03)"""
        # 1. 验证 SHA-256 哈希
        payload_bytes = json.dumps(package.task_results, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        calc_sha256 = hashlib.sha256(payload_bytes).hexdigest()
        if calc_sha256 != package.manifest.content_sha256:
            return False, "内容哈希校验失败：证据包数据可能已被篡改"

        # 2. 验证 HMAC 签名
        expected_sig = hmac.new(signing_key.encode("utf-8"), calc_sha256.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, package.manifest.signature):
            return False, "数字签名核验失败：未知签名密钥或签名伪造"

        return True, "证据包签名有效且数据完整未受篡改"


class OfflineHTMLReportRenderer:
    """自包含离线 HTML 报告渲染器 (E17-02 / E17-06)"""

    @classmethod
    def render(cls, package: EvidencePackage, is_verified: bool = True) -> str:
        m = package.manifest
        status_color = "#10B981" if m.pass_rate >= 0.95 else "#EF4444"
        badge_text = "VERIFIED SIGNATURE" if is_verified else "UNVERIFIED"

        task_rows_html = []
        for t in package.task_results:
            is_passed = t.get("is_passed", False)
            p_badge = '<span style="color:#10B981;font-weight:bold;">PASS</span>' if is_passed else '<span style="color:#EF4444;font-weight:bold;">FAIL</span>'
            score = t.get("total_score", 0.0)
            task_id = t.get("task_id", "")
            duration = t.get("total_duration_ms", 0.0)

            judgments_html = []
            for j in t.get("rubric_judgments", []):
                verdict = j.get("verdict", "")
                j_color = "#10B981" if verdict == "YES" else "#EF4444"
                spans = ", ".join(j.get("evidence_span_ids", [])) or "None"
                judgments_html.append(
                    f"<li><b>{j.get('rubric_id')}</b> ({j.get('judge_role')}): <span style='color:{j_color};font-weight:bold;'>{verdict}</span> - {j.get('rationale')} <small style='color:#9CA3AF;'>[Spans: {spans}]</small></li>"
                )

            task_rows_html.append(f"""
            <div style="background:#1F2937;border:1px solid #374151;border-radius:8px;padding:16px;margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:16px;font-weight:600;color:#F9FAFB;">{task_id}</span>
                    <div>
                        <span style="margin-right:12px;color:#9CA3AF;">Score: {score:.2f} ({duration:.0f}ms)</span>
                        {p_badge}
                    </div>
                </div>
                <ul style="margin-top:10px;padding-left:20px;font-size:13px;color:#D1D5DB;line-height:1.6;">
                    {"".join(judgments_html) or "<li>No specific rubrics recorded.</li>"}
                </ul>
            </div>
            """)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgentTestHub Release Gate Report - {m.package_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #111827;
            color: #F3F4F6;
            margin: 0;
            padding: 32px;
        }}
        .container {{
            max-width: 960px;
            margin: 0 auto;
        }}
        .header {{
            border-bottom: 1px solid #374151;
            padding-bottom: 20px;
            margin-bottom: 24px;
        }}
        .badge {{
            display: inline-block;
            background: #065F46;
            color: #34D399;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 28px;
        }}
        .stat-card {{
            background: #1F2937;
            border: 1px solid #374151;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .stat-val {{
            font-size: 24px;
            font-weight: 700;
            color: #F9FAFB;
            margin-top: 4px;
        }}
        .stat-lbl {{
            font-size: 12px;
            color: #9CA3AF;
            text-transform: uppercase;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <h1 style="margin:0;font-size:24px;">🛡️ AgentTestHub 发布门禁评测报告</h1>
                <span class="badge">{badge_text}</span>
            </div>
            <p style="color:#9CA3AF;margin:8px 0 0 0;font-size:14px;">
                套件: <b>{m.suite_name}</b> | Agent: <b>{m.target_agent_id}</b> | 生成时间: {m.timestamp}
            </p>
            <p style="color:#6B7280;margin:4px 0 0 0;font-size:12px;font-family:monospace;">
                SHA-256: {m.content_sha256} | Signature: {m.signature[:16]}...
            </p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-lbl">通过率 (Pass Rate)</div>
                <div class="stat-val" style="color:{status_color};">{m.pass_rate*100:.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-lbl">加权得分 (Avg Score)</div>
                <div class="stat-val">{m.average_score:.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-lbl">评测任务总数</div>
                <div class="stat-val">{m.total_tasks}</div>
            </div>
            <div class="stat-card">
                <div class="stat-lbl">达标任务数</div>
                <div class="stat-val" style="color:#10B981;">{m.passed_tasks}</div>
            </div>
        </div>

        <h2 style="font-size:18px;margin-bottom:16px;">逐用例裁决详情 (按严重度优先级排序)</h2>
        {"".join(task_rows_html)}

        <div style="margin-top:32px;border-top:1px solid #374151;padding-top:16px;text-align:center;color:#6B7280;font-size:12px;">
            本报告为自包含脱机文档，内嵌完整执行证据链与加密指纹 · AgentTestHub Release Gate System
        </div>
    </div>
</body>
</html>
"""
        return html
