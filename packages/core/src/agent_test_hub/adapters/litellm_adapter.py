from __future__ import annotations

import json
import time
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
        self.api_key = api_key
        self.api_base = self._normalize_api_base(api_base)
        self.model = self._normalize_model_name(model, self.api_base)
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.temperature = temperature
        self.mock_mode = mock_mode
        self._mock_responses = mock_responses or []
        self._mock_idx = 0

    @classmethod
    def _normalize_api_base(cls, api_base: str | None) -> str | None:
        """自动规范化自定义 Base URL (自适应追加 /v1 路径)"""
        if not api_base:
            return None
        base = api_base.strip().rstrip("/")
        if (
            ("http://" in base or "https://" in base)
            and not base.endswith("/v1")
            and ("11434" not in base)
        ):
            return f"{base}/v1"
        return base

    @classmethod
    def _normalize_model_name(cls, model_name: str, api_base: str | None = None) -> str:
        """自动推断并规整大模型 Provider 格式 (规避未加前缀导致报错)"""
        m = model_name.strip()
        if "/" in m:
            return m

        # 若配置了自定义第三方的 Base URL (如自建 OneAPI / 中转反代 / 本地私有服务)，统一按 OpenAI 兼容网关处理
        if api_base and ("http://" in api_base or "https://" in api_base):
            if "googleapis" not in api_base and "anthropic" not in api_base:
                return f"openai/{m}"

        lower = m.lower()
        if "gemini" in lower:
            return f"gemini/{m}"
        elif "deepseek" in lower:
            return f"deepseek/{m}"
        elif "claude" in lower:
            return f"anthropic/{m}"
        elif "qwen" in lower:
            return f"qwen/{m}"
        elif "llama" in lower or "ollama" in lower:
            return f"ollama/{m}"
        return m

    def test_connection(self) -> dict[str, Any]:
        """连通性与密钥校验探针，附带智能中文故障诊断建议"""
        if self.mock_mode:
            return {"status": "ok", "latency_ms": 10.0, "message": "Mock 模式连通正常"}

        start = time.time()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": "Hello, respond with OK"}],
            "max_tokens": 10,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base

        try:
            resp = litellm.completion(**kwargs)
            latency = (time.time() - start) * 1000.0
            content = resp.choices[0].message.content or "OK"
            return {
                "status": "ok",
                "latency_ms": round(latency, 1),
                "model": self.model,
                "reply": content.strip(),
            }
        except Exception as e:
            err_str = str(e)
            tip = ""
            if "401" in err_str or "Invalid API key" in err_str:
                tip = "【鉴权失败 401】API Key 无效或未授权，请检查密钥是否正确（勿误填为模型名）。"
            elif "404" in err_str or "NotFoundError" in err_str:
                tip = (
                    "【路径未找到 404】未找到该模型或 API Base 路径错误，请确认网关是否支持该模型。"
                )
            elif "Connection" in err_str or "Timeout" in err_str:
                tip = "【网络超时】无法连接到指定 API Base 地址，请检查 IP 端口与网络防火墙。"

            return {
                "status": "error",
                "model": self.model,
                "error": tip or err_str,
                "raw_error": err_str,
            }

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
