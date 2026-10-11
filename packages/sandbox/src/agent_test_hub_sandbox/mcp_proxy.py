from __future__ import annotations

import random
import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .base import FaultSpec


class MCPToolSchema(BaseModel):
    """符合 Anthropic MCP 标准的工具协议定义"""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="MCP 工具唯一方法名")
    description: str = Field(description="工具语义描述")
    inputSchema: dict[str, Any] = Field(default_factory=dict, description="JSON Schema 参数规格")


class MCPProxy:
    """Anthropic MCP (Model Context Protocol) 虚拟化代理与故障注入引擎

    遵循 JSON-RPC 2.0 标准规范：
    1. 动态挂载与发现 MCP 工具 (tools/list)；
    2. 透明执行中间拦截 (tools/call)；
    3. 支持高难度动态扰动注入 (延迟、字段篡改、异常报错)，压测 Agent 鲁棒性。
    """

    def __init__(self, server_name: str = "mcp_enterprise_gateway"):
        self.server_name = server_name
        self._registered_tools: dict[str, MCPToolSchema] = {}
        self._fault_rules: dict[str, FaultSpec] = {}

    def register_tool(self, tool: MCPToolSchema) -> None:
        """注册一个 MCP 标准工具"""
        self._registered_tools[tool.name] = tool

    def inject_fault(self, fault: FaultSpec) -> None:
        """配置针对指定 MCP 工具的故障注入规则"""
        self._fault_rules[fault.target_tool] = fault

    def list_tools(self) -> list[dict[str, Any]]:
        """实现 MCP tools/list 协议响应"""
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.inputSchema,
            }
            for t in self._registered_tools.values()
        ]

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """实现 MCP tools/call 协议调度并执行透明拦截"""
        # 1. 检查是否存在针对该工具的故障注入规则
        if tool_name in self._fault_rules:
            fault = self._fault_rules[tool_name]
            if random.random() <= fault.probability:
                if fault.delay_ms > 0:
                    time.sleep(fault.delay_ms / 1000.0)

                if fault.fault_type == "delay":
                    pass  # 仅延迟
                elif fault.fault_type == "http_error":
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"MCP Gateway Error [{fault.error_code}]: {fault.error_message}",
                        },
                    }
                elif fault.fault_type == "malformed_json":
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error: MCP client received malformed response chunk",
                        },
                    }

        # 2. 正常 MCP 工具执行分发
        if tool_name not in self._registered_tools:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: MCP tool '{tool_name}' is not registered",
                },
            }

        return {
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Successfully executed MCP tool '{tool_name}' on server '{self.server_name}'",
                    }
                ],
                "isError": False,
            },
        }
