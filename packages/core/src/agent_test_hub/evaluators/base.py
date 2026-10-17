from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agent_test_hub.schemas import BinaryVerdict, SeverityLevel


class EvaluatorResult(BaseModel):
    """确定性 Evaluator 执行产物"""

    model_config = ConfigDict(frozen=True)

    evaluator_name: str = Field(description="Evaluator 唯一标识")
    verdict: BinaryVerdict = Field(description="裁决：YES / NO / UNKNOWN")
    score: float = Field(default=1.0, ge=0.0, le=1.0, description="归一化分值 0.0 ~ 1.0")
    evidence_span_ids: list[str] = Field(default_factory=list, description="关联的 Trace Span ID")
    evidence_data: dict[str, Any] = Field(default_factory=dict, description="结构化证据详情")
    rationale: str = Field(default="", description="结论说明与因果证据")
    is_fatal: bool = Field(default=False, description="是否一票否决项")
    severity: SeverityLevel = Field(default=SeverityLevel.MEDIUM, description="违规严重度分级")


class BaseEvaluator(ABC):
    """确定性 Evaluator 统一抽象基类"""

    name: str = "base_evaluator"
    is_fatal: bool = False
    severity: SeverityLevel = SeverityLevel.MEDIUM

    @abstractmethod
    def evaluate(self, **kwargs: Any) -> EvaluatorResult:
        """执行确定性评估"""
        pass
