from __future__ import annotations

from typing import Any

from agent_test_hub.schemas import ExecutionTrace

from ..base import BaseMetric, MetricResult


class SOPComplianceMetric(BaseMetric):
    """蚂蚁 AIEvo 机制落地: 金融级 SOP 标准作业程序有向图遵循度量算子

    专门针对金融、审批、政企等强流程场景：
    1. 验证被测 Agent/团队是否严格按照预定 SOP 阶段推进；
    2. 严厉拦截越权跳步（如未完成身份核身 KYC 即直接审批放款）；
    3. 输出细粒度的步骤覆盖率、时序吻合度与跳步违规违禁项。
    """

    name: str = "sop_graph_compliance"
    dimension: str = "MAS_SOP_Governance"

    def __init__(self, expected_sop_sequence: list[str] | None = None, strict_order: bool = True):
        # 预期的标准 SOP 序列，如: ["verify_identity", "query_credit", "risk_audit", "disburse_loan"]
        self.expected_sop = expected_sop_sequence or []
        self.strict_order = strict_order

    def evaluate(
        self, trace: ExecutionTrace, context: dict[str, Any] | None = None
    ) -> MetricResult:
        if not self.expected_sop:
            return MetricResult(
                metric_name=self.name,
                dimension=self.dimension,
                score=1.0,
                is_passed=True,
                rationale="未指定 SOP 规约序列，跳过流程合规核验",
            )

        # 提取实际发生的工具调用时序
        actual_calls = [c.tool_name for c in trace.get_tool_calls()]
        if not actual_calls:
            return MetricResult(
                metric_name=self.name,
                dimension=self.dimension,
                score=0.0,
                is_passed=False,
                details={"actual_sequence": [], "expected_sequence": self.expected_sop},
                rationale="未检测到任何动作执行，SOP 覆盖率为 0",
            )

        # 1. 步骤覆盖度检查
        covered_steps = set(actual_calls).intersection(set(self.expected_sop))
        coverage_ratio = len(covered_steps) / len(self.expected_sop)

        # 2. 时序正确性与跳步检测 (Topological Sequence Match)
        violations: list[str] = []
        actual_filtered = [c for c in actual_calls if c in self.expected_sop]

        last_idx = -1
        for step in actual_filtered:
            expected_idx = self.expected_sop.index(step)
            if self.strict_order and expected_idx < last_idx:
                violations.append(f"时序倒置: 步骤 '{step}' 执行于后置步骤之后")
            last_idx = max(last_idx, expected_idx)

        # 检查未执行的前置必经步骤是否被跳过
        missing_steps = [s for s in self.expected_sop if s not in covered_steps]
        if missing_steps:
            violations.append(f"遗漏必经 SOP 阶段: {missing_steps}")

        is_passed = (coverage_ratio == 1.0) and (len(violations) == 0)
        score = 1.0 if is_passed else round(coverage_ratio * (0.5 if violations else 1.0), 3)

        return MetricResult(
            metric_name=self.name,
            dimension=self.dimension,
            score=score,
            is_passed=is_passed,
            details={
                "expected_sop": self.expected_sop,
                "actual_sequence": actual_calls,
                "coverage_ratio": coverage_ratio,
                "violations": violations,
            },
            rationale="100% 严谨遵循 SOP 作业程序"
            if is_passed
            else f"发现 SOP 流程违规: {'; '.join(violations)}",
        )
