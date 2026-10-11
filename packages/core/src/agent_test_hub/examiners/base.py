from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from agent_test_hub.schemas import ExecutionTrace


class ExaminerAction(BaseModel):
    """考官执行的一项交互行为指令"""
    model_config = ConfigDict(frozen=True)

    action_type: str = Field(description="speak / attack / inject_fault / terminate")
    content: str = Field(default="", description="交互回复消息或攻击 Prompt")
    internal_state: dict[str, Any] = Field(default_factory=dict, description="考官当前内部状态机快照")
    should_stop_eval: bool = Field(default=False, description="是否要求终止测试会话")


class BaseExaminer(ABC):
    """考官智能体基类"""

    role: str = "base_examiner"

    @abstractmethod
    def act(self, trace: ExecutionTrace, turn_index: int) -> ExaminerAction:
        """根据历史轨迹动态做出下一轮交互决策"""
        pass
