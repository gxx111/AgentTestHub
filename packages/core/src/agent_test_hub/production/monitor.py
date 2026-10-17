from __future__ import annotations

import datetime
import random
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from agent_test_hub.evaluators import PIILeakEvaluator, SQLSafetyEvaluator
from agent_test_hub.schemas import BinaryVerdict, ExecutionTrace, SeverityLevel
from agent_test_hub_domain.models import CaseModel, DatasetModel, DatasetVersionModel


class AlertConfig(BaseModel):
    """告警策略配置 (E15-04)"""

    model_config = ConfigDict(frozen=True)

    webhook_url: str | None = None
    min_score_threshold: float = 0.8
    alert_on_fatal: bool = True
    alert_on_error: bool = True


class OnlineMonitor(BaseModel):
    """生产在线监控与采样器规格 (E15-01 / E15-02)"""

    model_config = ConfigDict(frozen=True)

    monitor_id: str
    project_id: str
    name: str = "生产实时监控"
    sample_rate: float = Field(default=0.1, ge=0.0, le=1.0, description="常规采样比例 0.0 ~ 1.0")
    sample_errors_100pct: bool = Field(default=True, description="异常与报错 100% 全量采样")
    max_latency_threshold_ms: float = Field(default=5000.0, description="长耗时强制采样阈值")
    alert_config: AlertConfig = Field(default_factory=AlertConfig)


class OnlineEvaluationResult(BaseModel):
    """生产 Trace 在线评分产物 (E15-03)"""

    model_config = ConfigDict(frozen=True)

    trace_id: str
    is_sampled: bool
    score: float
    is_passed: bool
    has_fatal_violation: bool
    violations: list[str] = Field(default_factory=list)
    alert_triggered: bool = False
    alert_message: str | None = None
    converted_case_id: str | None = None


class OnlineEvaluationEngine:
    """生产 Trace 实时评测、采样、告警与回流闭环引擎 (E15)"""

    def __init__(self, monitor: OnlineMonitor):
        self.monitor = monitor
        self.sql_evaluator = SQLSafetyEvaluator()
        self.pii_evaluator = PIILeakEvaluator()
        self._alert_history: list[dict[str, Any]] = []

    def should_sample(self, trace: ExecutionTrace) -> bool:
        """判定生产 Trace 是否命中采样策略 (E15-02)"""
        # 1. 若 Trace 包含工具报错或错误事件，且开启了 100% 采样，强制采样
        has_error = any(
            (e.tool_observation and e.tool_observation.is_error) or "error" in (e.content or "").lower()
            for e in trace.events
        )
        if self.monitor.sample_errors_100pct and has_error:
            return True

        # 2. 若耗时超阈值，强制采样
        if trace.total_duration_ms > self.monitor.max_latency_threshold_ms:
            return True

        # 3. 常规比例随机采样
        return random.random() <= self.monitor.sample_rate

    def evaluate_production_trace(
        self,
        trace: ExecutionTrace,
        trace_to_dataset_fn: Callable[[ExecutionTrace, list[str]], str] | None = None,
    ) -> OnlineEvaluationResult:
        """对单条生产 Trace 异步自动打分并驱动告警与回流 (E15-03 ~ E15-06)"""
        is_sampled = self.should_sample(trace)
        if not is_sampled:
            return OnlineEvaluationResult(
                trace_id=trace.trace_id,
                is_sampled=False,
                score=1.0,
                is_passed=True,
                has_fatal_violation=False,
            )

        violations = []
        has_fatal = False

        # 运行确定性安全检查 (SQL 安全与 PII 泄漏)
        sql_res = self.sql_evaluator.evaluate(trace)
        if sql_res.verdict == BinaryVerdict.NO:
            violations.append(f"SQL 安全违规: {sql_res.rationale}")
            has_fatal = True

        pii_res = self.pii_evaluator.evaluate(trace)
        if pii_res.verdict == BinaryVerdict.NO:
            violations.append(f"敏感数据泄露: {pii_res.rationale}")
            has_fatal = True

        # 计算得分
        if has_fatal:
            score = 0.0
            is_passed = False
        elif violations:
            score = 0.5
            is_passed = False
        else:
            score = 1.0
            is_passed = True

        # 告警触发判定 (E15-04)
        alert_triggered = False
        alert_msg = None
        if (
            (has_fatal and self.monitor.alert_config.alert_on_fatal)
            or (score < self.monitor.alert_config.min_score_threshold)
        ):
            alert_triggered = True
            alert_msg = f"[告警] 生产 Agent Trace [{trace.trace_id}] 评分 {score:.2f} 低于阈值，违规: {'; '.join(violations)}"
            self._alert_history.append({
                "trace_id": trace.trace_id,
                "message": alert_msg,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })

        # 失败用例自动回流至数据集 (E15-06 Trace -> Dataset)
        converted_case_id = None
        if not is_passed and trace_to_dataset_fn:
            converted_case_id = trace_to_dataset_fn(trace, violations)

        return OnlineEvaluationResult(
            trace_id=trace.trace_id,
            is_sampled=True,
            score=score,
            is_passed=is_passed,
            has_fatal_violation=has_fatal,
            violations=violations,
            alert_triggered=alert_triggered,
            alert_message=alert_msg,
            converted_case_id=converted_case_id,
        )

    def get_alert_history(self) -> list[dict[str, Any]]:
        return list(self._alert_history)
