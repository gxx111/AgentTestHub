from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ActorRole(str, Enum):
    """参与交互的实体角色定义"""

    USER_SIMULATOR = "user_simulator"  # 考官: 状态化用户模拟官
    RED_TEAM_ATTACKER = "red_team_attacker"  # 考官: 对抗攻防红队官
    TESTEE_AGENT = "testee_agent"  # 被测主体 Agent
    WATCHDOG = "watchdog"  # 考官: 环境监考与故障注入官
    TOOL_SANDBOX = "tool_sandbox"  # 沙盒工具执行器


class TraceEventType(str, Enum):
    """OpenInference 语义事件流类型"""

    USER_MESSAGE = "user_message"
    AGENT_THOUGHT = "agent_thought"
    AGENT_MESSAGE = "agent_message"
    TOOL_CALL_REQUEST = "tool_call_request"
    TOOL_CALL_RESPONSE = "tool_call_response"
    FAULT_INJECTED = "fault_injected"
    STATE_SNAPSHOT = "state_snapshot"


class ToolCallObservation(BaseModel):
    """工具调用的输入、输出与耗时详细观测数据"""

    model_config = ConfigDict(frozen=True)

    tool_name: str = Field(description="调用的工具名")
    arguments: dict[str, Any] = Field(default_factory=dict, description="传入的参数字典")
    output: Any = Field(default=None, description="执行返回结果或错误信息")
    is_error: bool = Field(default=False, description="是否发生执行异常/返回错误")
    duration_ms: float = Field(default=0.0, ge=0.0, description="工具耗时(毫秒)")


class TraceEvent(BaseModel):
    """不可变结构化执行事件 (OpenInference 语义单元)"""

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(
        default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}", description="事件唯一 ID"
    )
    span_id: str = Field(
        default_factory=lambda: f"spn_{uuid.uuid4().hex[:12]}", description="Trace Span ID 锚点"
    )
    parent_span_id: str | None = Field(default=None, description="父级 Span ID")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="UTC 时间戳"
    )
    turn_index: int = Field(default=0, ge=0, description="会话交互轮次序号")
    actor_role: ActorRole = Field(description="产生该事件的角色")
    actor_name: str = Field(default="system", description="角色名称")
    event_type: TraceEventType = Field(description="事件类型")

    # 消息内容与载荷
    content: str = Field(default="", description="文本消息或思考链内容")
    tool_observation: ToolCallObservation | None = Field(
        default=None, description="工具调用观测数据"
    )

    # 资源消耗记录
    tokens_consumed: int = Field(default=0, ge=0, description="本事件消耗的 Token 数")
    cost_usd: float = Field(default=0.0, ge=0.0, description="费用开销估算")
    metadata: dict[str, Any] = Field(default_factory=dict, description="额外上下文打点")


class ExecutionTrace(BaseModel):
    """单任务全生命周期执行轨迹集合"""

    model_config = ConfigDict(frozen=True)

    task_id: str = Field(description="关联的任务 ID")
    trace_id: str = Field(
        default_factory=lambda: f"trc_{uuid.uuid4().hex[:16]}", description="Trace 会话 ID"
    )
    events: list[TraceEvent] = Field(default_factory=list, description="事件时间序列流")
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime | None = Field(default=None)
    total_tokens: int = Field(default=0, ge=0)
    total_duration_ms: float = Field(default=0.0, ge=0.0)

    def get_events_by_type(self, event_type: TraceEventType) -> list[TraceEvent]:
        """按类型筛选事件列表"""
        return [e for e in self.events if e.event_type == event_type]

    def get_tool_calls(self) -> list[ToolCallObservation]:
        """提取所有工具调用观测记录"""
        return [e.tool_observation for e in self.events if e.tool_observation is not None]
