from __future__ import annotations

import json
from typing import Any

import litellm
from agent_test_hub.schemas import ExecutionTrace, ToolDefinition, TraceEventType


class LiteLLMAgentAdapter:
    """基于 LiteLLM 的真实大模型/Agent 统一调度适配器

    统一抽象 100+ 商业与开源大模型 (OpenAI, Claude, DeepSeek, Qwen, Ollama 等)，
    原生支持 Function Calling 工具调用参数解析与多轮上下文维护。
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        system_prompt: str = "你是一个专业的智能助理。",
        tools: list[ToolDefinition] | None = None,
        api_key: str | None = None,
        api_base: str | None = None,
        temperature: float = 0.0,
        mock_mode: bool = False,
        mock_responses: list[dict[str, Any]] | None = None,
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.api_key = api_key
        self.api_base = api_base
        self.temperature = temperature
        self.mock_mode = mock_mode
        self._mock_responses = mock_responses or []
        self._mock_idx = 0

    def _convert_tools_to_openai_format(self) -> list[dict[str, Any]]:
        """将 ToolDefinition 转换为标准 OpenAI tools 规格"""
        formatted = []
        for t in self.tools:
            formatted.append(
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters_schema
                        or {
                            "type": "object",
                            "properties": {},
                        },
                    },
                }
            )
        return formatted

    def _build_messages_from_trace(
        self, user_prompt: str, trace: ExecutionTrace
    ) -> list[dict[str, Any]]:
        """从不可变执行日志回溯组装多轮上下文消息列表"""
        messages: list[dict[str, Any]] = [{"role": "system", "content": self.system_prompt}]

        # 按轮次提取历史消息
        for event in trace.events:
            if event.event_type == TraceEventType.USER_MESSAGE:
                messages.append({"role": "user", "content": event.content})
            elif event.event_type == TraceEventType.AGENT_MESSAGE:
                messages.append({"role": "assistant", "content": event.content})

        # 确保当前用户最新 Prompt 在末尾
        if not messages or messages[-1].get("content") != user_prompt:
            messages.append({"role": "user", "content": user_prompt})

        return messages

    def step(self, user_prompt: str, trace: ExecutionTrace) -> dict[str, Any]:
        """执行单轮推理与工具调用生成"""
        # 1. 若处于离线/测试 Mock 模式，直接分发预设响应
        if self.mock_mode:
            if self._mock_idx < len(self._mock_responses):
                res = self._mock_responses[self._mock_idx]
                self._mock_idx += 1
                return res
            return {"response": "处理完毕", "tool_calls": []}

        # 2. 真实在线模式：调用 LiteLLM 统一网关
        messages = self._build_messages_from_trace(user_prompt, trace)
        tools_spec = self._convert_tools_to_openai_format()

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if tools_spec:
            kwargs["tools"] = tools_spec
            kwargs["tool_choice"] = "auto"
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base

        try:
            response = litellm.completion(**kwargs)
            choice = response.choices[0].message
            content = choice.content or ""

            # 解析 tool_calls
            tool_calls = []
            if hasattr(choice, "tool_calls") and choice.tool_calls:
                for tc in choice.tool_calls:
                    fn_name = tc.function.name
                    fn_args = {}
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except Exception:
                        pass
                    tool_calls.append({"name": fn_name, "arguments": fn_args})

            return {"response": content, "tool_calls": tool_calls}
        except Exception as e:
            return {
                "response": f"LiteLLM 调用异常: {e!s}",
                "tool_calls": [],
                "error": str(e),
            }
