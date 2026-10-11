from __future__ import annotations

from abc import ABC, abstractmethod

from agent_test_hub.schemas import (
    BinaryRubric,
    ExecutionTrace,
    RubricJudgment,
)


class BaseJudge(ABC):
    """评审法官抽象基类"""

    role: str = "base_judge"

    @abstractmethod
    def judge(self, rubric: BinaryRubric, trace: ExecutionTrace) -> RubricJudgment:
        """针对单条二元 Rubric 检查项进行独立盲审并出示证据链"""
        pass
