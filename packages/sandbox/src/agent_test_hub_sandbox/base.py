from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class FaultSpec(BaseModel):
    """注入的系统或工具故障规格"""
    model_config = ConfigDict(frozen=True)

    fault_type: str = Field(description="故障类型: delay / http_error / malformed_json / exception")
    target_tool: str = Field(description="受到影响的目标工具名称")
    delay_ms: float = Field(default=0.0, ge=0.0, description="模拟延迟毫秒数")
    error_code: int = Field(default=500, description="模拟 HTTP 状态码")
    error_message: str = Field(default="Internal Server Error", description="模拟返回的错误信息")
    probability: float = Field(default=1.0, ge=0.0, le=1.0, description="故障触发概率")


class StateSnapshot(BaseModel):
    """沙盒环境某一时间点的物理状态快照"""
    model_config = ConfigDict(frozen=True)

    snapshot_id: str = Field(description="快照唯一标识")
    timestamp: str = Field(description="快照生成时间")
    tables_data: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict, description="各数据表的完整数据记录快照"
    )
    files_data: dict[str, str] = Field(
        default_factory=dict, description="受监控文件的哈希或内容映射"
    )


class StateDelta(BaseModel):
    """环境初态与终态之间的客观物理差异"""
    model_config = ConfigDict(frozen=True)

    is_changed: bool = Field(description="是否存在物理变更")
    modified_records: list[dict[str, Any]] = Field(
        default_factory=list, description="被新增、修改或删除的具体记录明细"
    )
    unmatched_expectations: list[dict[str, Any]] = Field(
        default_factory=list, description="未达成预期终态的断言差异列表"
    )


class BaseSandbox(ABC):
    """受控物理/逻辑沙盒环境抽象基类"""

    @abstractmethod
    def initialize(self, init_scripts: list[str] | None = None) -> None:
        """初始化沙盒环境与初始测试数据"""
        pass

    @abstractmethod
    def snapshot(self) -> StateSnapshot:
        """保存当前环境状态快照"""
        pass

    @abstractmethod
    def rollback(self, snapshot: StateSnapshot) -> None:
        """回滚环境到历史指定快照"""
        pass

    @abstractmethod
    def compute_diff(self, initial: StateSnapshot, final: StateSnapshot) -> StateDelta:
        """计算初态与终态的物理差分"""
        pass

    @abstractmethod
    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """在受控沙盒内安全调用并执行工具"""
        pass

    @abstractmethod
    def inject_fault(self, fault: FaultSpec) -> None:
        """配置透明故障注入规则"""
        pass
