from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ToolDefinition(BaseModel):
    """可供被测 Agent 使用的工具/MCP 接口定义"""
    model_config = ConfigDict(frozen=True)

    name: str = Field(description="工具唯一函数名")
    description: str = Field(description="工具功能语义描述")
    parameters_schema: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema 格式的参数规格"
    )
    is_dangerous: bool = Field(default=False, description="是否属于敏感/不可逆高风险操作")


class TaskConstraint(BaseModel):
    """任务执行过程中的刚性业务或资源约束"""
    model_config = ConfigDict(frozen=True)

    max_turns: int = Field(default=15, ge=1, le=100, description="允许的最大会话轮次")
    timeout_seconds: int = Field(default=180, ge=1, description="单任务最长超时时间(秒)")
    max_tokens: int = Field(default=8000, ge=100, description="最大允许消耗的 Token 总预算")
    forbidden_tools: list[str] = Field(default_factory=list, description="被明确禁用的工具黑名单")


class WorldStateExpectation(BaseModel):
    """沙盒环境物理终态的断言规格（用于真实数据库或文件系统差分核验）"""
    model_config = ConfigDict(frozen=True)

    target_type: str = Field(default="database", description="目标物理介质: database / filesystem")
    target_identifier: str = Field(description="目标实体定位 (如数据表名 'orders' 或文件路径)")
    condition: dict[str, Any] = Field(description="过滤条件 (如 {'order_id': 'ORD_1001'})")
    expected_values: dict[str, Any] = Field(description="期望达成的物理字段终态 (如 {'status': 'CANCELLED'})")


class TaskSpec(BaseModel):
    """标准测试任务规约定义（所有评测场景的基本原子单位）"""
    model_config = ConfigDict(frozen=True)

    task_id: str = Field(description="任务全局唯一 ID")
    scenario_id: str = Field(description="所属业务场景 ID")
    title: str = Field(description="任务简明标题")
    description: str = Field(description="任务背景与初始 Prompt 描述")
    category: str = Field(default="general", description="业务分类: ecommerce / coding / finance / mas")
    difficulty: str = Field(default="medium", description="难度等级: easy / medium / hard / expert")
    
    # 考官与环境配置
    initial_user_prompt: str = Field(description="用户模拟官发出的第一句话")
    available_tools: list[ToolDefinition] = Field(default_factory=list, description="可调用的工具集合")
    constraints: TaskConstraint = Field(default_factory=TaskConstraint, description="业务与资源约束")
    
    # 客观物理状态断言 (真实世界差分核验)
    expected_world_states: list[WorldStateExpectation] = Field(
        default_factory=list, description="物理沙盒终态断言列表"
    )
    
    # 动态上下文与元数据
    metadata: dict[str, Any] = Field(default_factory=dict, description="场景自定义扩展元数据")
