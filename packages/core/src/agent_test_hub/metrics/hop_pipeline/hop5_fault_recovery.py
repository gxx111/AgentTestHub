from __future__ import annotations

from typing import Any
from agent_test_hub.schemas import ExecutionTrace, TraceEventType
from ..base import BaseMetric, MetricResult


class FaultRecoveryMetric(BaseMetric):
    """阿里 Hop 5: 工具执行容错与自愈恢复率 (Fault Recovery Rate)"""

    name: str = "hop5_fault_recovery"
    dimension: str = "Hop5_Fault_Tolerance"

    def evaluate(self, trace: ExecutionTrace, context: dict[str, Any] | None = None) -> MetricResult:
        tool_calls = trace.get_tool_calls()
        if not tool_calls:
            return MetricResult(
                metric_name=self.name,
                dimension=self.dimension,
                score=1.0,
                is_passed=True,
                rationale="无工具调用，无需评估故障恢复能力",
            )

        error_indices = [i for i, call in enumerate(tool_calls) if call.is_error]
        if not error_indices:
            return MetricResult(
                metric_name=self.name,
                dimension=self.dimension,
                score=1.0,
                is_passed=True,
                rationale="执行全流程未遭遇工具报错，容错率满分",
            )

        recovered_count = 0
        for err_idx in error_indices:
            # 检查在报错之后，Agent 是否成功发起了一次后续调用或有意义的补救重试
            if err_idx + 1 < len(tool_calls):
                next_call = tool_calls[err_idx + 1]
                if not next_call.is_error:
                    recovered_count += 1

        recovery_rate = recovered_count / len(error_indices)
        return MetricResult(
            metric_name=self.name,
            dimension=self.dimension,
            score=recovery_rate,
            is_passed=(recovery_rate >= 0.8),
            details={"error_count": len(error_indices), "recovered_count": recovered_count},
            rationale=f"遭遇 {len(error_indices)} 次工具异常，成功恢复 {recovered_count} 次",
        )


class LivelockDetectionMetric(BaseMetric):
    """阿里 Hop 6: 循环死循环与动作活锁识别 (Circular Step Livelock Detector)"""

    name: str = "hop6_livelock_detection"
    dimension: str = "Hop6_Memory_Reflection"

    def __init__(self, max_consecutive_duplicates: int = 3):
        self.max_duplicates = max_consecutive_duplicates

    def evaluate(self, trace: ExecutionTrace, context: dict[str, Any] | None = None) -> MetricResult:
        tool_calls = trace.get_tool_calls()
        if len(tool_calls) < self.max_duplicates:
            return MetricResult(
                metric_name=self.name,
                dimension=self.dimension,
                score=1.0,
                is_passed=True,
                rationale="调用步数过短，未发生死循环",
            )

        signatures = [f"{c.tool_name}:{sorted(c.arguments.items())}" for c in tool_calls]
        consecutive_same = 1
        max_seen = 1

        for i in range(1, len(signatures)):
            if signatures[i] == signatures[i - 1]:
                consecutive_same += 1
                max_seen = max(max_seen, consecutive_same)
            else:
                consecutive_same = 1

        has_livelock = max_seen >= self.max_duplicates
        score = 0.0 if has_livelock else 1.0

        return MetricResult(
            metric_name=self.name,
            dimension=self.dimension,
            score=score,
            is_passed=not has_livelock,
            details={"max_consecutive_repeated_calls": max_seen},
            rationale=f"检测到重复调用 {max_seen} 次相同的参数，判定为行为死循环" if has_livelock else "未检测到重复行为活锁",
        )
