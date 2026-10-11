from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from agent_test_hub.schemas import ExecutionTrace


class MetricResult(BaseModel):
    """单项评测指标的统一输出契约"""
    model_config = ConfigDict(frozen=True)

    metric_name: str = Field(description="指标唯一英文标识")
    dimension: str = Field(description="所属能力维度 (Hop1-7 / MAS / System)")
    score: float = Field(ge=0.0, le=1.0, description="归一化分值 (0.0 ~ 1.0)")
    is_passed: bool = Field(description="是否达到达标阈值")
    details: dict[str, Any] = Field(default_factory=dict, description="细粒度分析数据与中间指标")
    rationale: str = Field(default="", description="评分依据与诊断说明")


class BaseMetric(ABC):
    """所有评测算子的抽象基类"""

    name: str = "base_metric"
    dimension: str = "general"

    @abstractmethod
    def evaluate(self, trace: ExecutionTrace, context: dict[str, Any] | None = None) -> MetricResult:
        """从执行日志与上下文计算指标分值"""
        pass
