from __future__ import annotations

from typing import Any

from .base import BaseEvaluator, EvaluatorResult
from .deterministic import (
    BudgetEvaluator,
    BusinessPolicyEvaluator,
    PIILeakEvaluator,
    SQLSafetyEvaluator,
    StateDiffEvaluator,
    ToolArgEvaluator,
    ToolCallEvaluator,
)


class EvaluatorRegistry:
    """Evaluator 统一注册中心与执行套件 (E5-01)"""

    def __init__(self):
        self._evaluators: dict[str, BaseEvaluator] = {}
        # 预注册开箱即用的标准确定性 Evaluator
        self.register(SQLSafetyEvaluator())
        self.register(PIILeakEvaluator())

    def register(self, evaluator: BaseEvaluator) -> None:
        self._evaluators[evaluator.name] = evaluator

    def get(self, name: str) -> BaseEvaluator | None:
        return self._evaluators.get(name)

    def list_evaluators(self) -> list[str]:
        return list(self._evaluators.keys())

    def run_all(self, **kwargs: Any) -> list[EvaluatorResult]:
        """按序运行已注册的所有 Evaluator 并收集结构化结果"""
        results = []
        for evaluator in self._evaluators.values():
            try:
                res = evaluator.evaluate(**kwargs)
                results.append(res)
            except Exception as exc:
                from agent_test_hub.schemas import BinaryVerdict, SeverityLevel
                results.append(
                    EvaluatorResult(
                        evaluator_name=evaluator.name,
                        verdict=BinaryVerdict.UNKNOWN,
                        score=0.0,
                        rationale=f"Evaluator 执行异常: {type(exc).__name__}: {exc}",
                        is_fatal=evaluator.is_fatal,
                        severity=SeverityLevel.HIGH,
                    )
                )
        return results
