from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from agent_test_hub.schemas import BinaryVerdict


class ConfusionMatrix(BaseModel):
    """二元混淆矩阵与效度评估指标 (E6-08)"""

    model_config = ConfigDict(frozen=True)

    true_positive: int = Field(default=0, description="真阳性 (预期达标且实际达标)")
    true_negative: int = Field(default=0, description="真阴性 (预期违规且实际判定违规)")
    false_positive: int = Field(default=0, description="假阳性/误放行 (预期违规但被误判为通过 - False Pass)")
    false_negative: int = Field(default=0, description="假阴性/误拦截 (预期达标但被误判为未通过 - False Fail)")

    @property
    def total(self) -> int:
        return self.true_positive + self.true_negative + self.false_positive + self.false_negative

    @property
    def accuracy(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.true_positive + self.true_negative) / self.total

    @property
    def false_pass_rate(self) -> float:
        """假通过率 (False Pass Rate / FPR) = FP / (FP + TN)"""
        denom = self.false_positive + self.true_negative
        if denom == 0:
            return 0.0
        return self.false_positive / denom

    @property
    def false_fail_rate(self) -> float:
        """假拦截率 (False Fail Rate / FFR) = FN / (FN + TP)"""
        denom = self.false_negative + self.true_positive
        if denom == 0:
            return 0.0
        return self.false_negative / denom

    @property
    def precision(self) -> float:
        denom = self.true_positive + self.false_positive
        return (self.true_positive / denom) if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        denom = self.true_positive + self.false_negative
        return (self.true_positive / denom) if denom > 0 else 0.0

    @property
    def f1_score(self) -> float:
        p, r = self.precision, self.recall
        return (2 * p * r / (p + r)) if (p + r) > 0 else 0.0


def calculate_cohen_kappa(
    rater_a: list[BinaryVerdict | str],
    rater_b: list[BinaryVerdict | str],
) -> float:
    """计算 Cohen's Kappa 一致性系数 (E6-08)

    衡量评委评判与黄金集基准的一致性（剔除随机偶合因素）：
    κ = (P_o - P_e) / (1 - P_e)
    """
    if len(rater_a) != len(rater_b) or len(rater_a) == 0:
        return 0.0

    n = len(rater_a)
    categories = {"YES", "NO", "UNKNOWN"}

    # 规范化转为纯大写字符串
    norm_a = [v.value if isinstance(v, BinaryVerdict) else str(v).upper() for v in rater_a]
    norm_b = [v.value if isinstance(v, BinaryVerdict) else str(v).upper() for v in rater_b]

    # 实际观测一致率 P_o
    agreements = sum(1 for a, b in zip(norm_a, norm_b) if a == b)
    p_o = agreements / n

    # 期望随机一致率 P_e
    p_e = 0.0
    for cat in categories:
        count_a = sum(1 for a in norm_a if a == cat)
        count_b = sum(1 for b in norm_b if b == cat)
        p_e += (count_a / n) * (count_b / n)

    if p_e >= 1.0:
        return 1.0
    kappa = (p_o - p_e) / (1.0 - p_e)
    return max(-1.0, min(1.0, round(kappa, 4)))


def build_confusion_matrix(
    predictions: list[BinaryVerdict | str],
    ground_truth: list[BinaryVerdict | str],
) -> ConfusionMatrix:
    """基于二元判决构建混淆矩阵"""
    tp = fp = tn = fn = 0
    for pred, gt in zip(predictions, ground_truth):
        p_val = pred.value if isinstance(pred, BinaryVerdict) else str(pred).upper()
        g_val = gt.value if isinstance(gt, BinaryVerdict) else str(gt).upper()

        if g_val == "YES":
            if p_val == "YES":
                tp += 1
            else:
                fn += 1
        else:  # g_val in ("NO", "UNKNOWN")
            if p_val == "YES":
                fp += 1
            else:
                tn += 1

    return ConfusionMatrix(
        true_positive=tp,
        true_negative=tn,
        false_positive=fp,
        false_negative=fn,
    )
