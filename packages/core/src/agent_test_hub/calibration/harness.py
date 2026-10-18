from __future__ import annotations

import json
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from agent_test_hub.judges import JudicialCommittee
from agent_test_hub.schemas import BinaryRubric, BinaryVerdict, ExecutionTrace

from .metrics import ConfusionMatrix, build_confusion_matrix, calculate_cohen_kappa


class GoldenCase(BaseModel):
    """黄金校准集单用例"""

    model_config = ConfigDict(frozen=True)

    case_id: str
    rubric: BinaryRubric
    trace: ExecutionTrace
    ground_truth_verdict: BinaryVerdict
    is_synthetic: bool = True
    annotation_source: str = "非人工标签，Kappa 仅作工程基线"


class CalibrationReport(BaseModel):
    """校准评测报告 (E6-08)"""

    model_config = ConfigDict(frozen=True)

    total_cases: int
    kappa: float
    confusion_matrix: ConfusionMatrix
    false_pass_rate: float
    false_fail_rate: float
    annotation_source: str = "非人工标签，Kappa 仅作工程基线"
    details: list[dict[str, Any]] = Field(default_factory=list)


class CalibrationHarness:
    """Judge 校准与黄金集评测套件 (E6-07 ~ E6-09)"""

    def __init__(self, committee: JudicialCommittee | None = None):
        self.committee = committee or JudicialCommittee()

    def run_calibration(self, cases: list[GoldenCase]) -> CalibrationReport:
        predictions: list[BinaryVerdict] = []
        ground_truths: list[BinaryVerdict] = []
        details = []

        for case in cases:
            verdict, judgments, dispute = self.committee.evaluate_rubric(
                case.rubric, case.trace
            )
            predictions.append(verdict)
            ground_truths.append(case.ground_truth_verdict)
            details.append({
                "case_id": case.case_id,
                "expected": case.ground_truth_verdict.value,
                "predicted": verdict.value,
                "is_match": verdict == case.ground_truth_verdict,
                "dispute_resolved": dispute is not None,
            })

        kappa = calculate_cohen_kappa(predictions, ground_truths)
        matrix = build_confusion_matrix(predictions, ground_truths)

        source = (
            cases[0].annotation_source
            if cases and cases[0].annotation_source
            else "非人工标签，Kappa 仅作工程基线"
        )

        return CalibrationReport(
            total_cases=len(cases),
            kappa=kappa,
            confusion_matrix=matrix,
            false_pass_rate=matrix.false_pass_rate,
            false_fail_rate=matrix.false_fail_rate,
            annotation_source=source,
            details=details,
        )
