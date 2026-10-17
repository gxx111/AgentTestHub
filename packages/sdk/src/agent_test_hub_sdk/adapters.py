from __future__ import annotations

import json
from typing import Any, Callable

from agent_test_hub.schemas import ExecutionTrace


class SmolagentsAdapter:
    """smolagents 框架适配器 (E11 / E13)"""

    def __init__(self, agent: Any):
        self.agent = agent

    def __call__(self, prompt: str, trace: ExecutionTrace) -> dict[str, Any]:
        result = self.agent.run(prompt)
        return {
            "response": str(result),
            "tool_calls": [],
        }


class LangChainAdapter:
    """LangChain / LangGraph Runnable 适配器 (E11 / E13)"""

    def __init__(self, runnable: Any, input_key: str = "input", output_key: str = "output"):
        self.runnable = runnable
        self.input_key = input_key
        self.output_key = output_key

    def __call__(self, prompt: str, trace: ExecutionTrace) -> dict[str, Any]:
        try:
            # 兼容 Runnable 与 AgentExecutor
            res = self.runnable.invoke({self.input_key: prompt})
            if isinstance(res, dict):
                content = res.get(self.output_key) or str(res)
            else:
                content = getattr(res, "content", str(res))
            return {
                "response": str(content),
                "tool_calls": [],
            }
        except Exception as exc:
            return {
                "response": f"LangChain execution error: {exc}",
                "error": type(exc).__name__,
                "tool_calls": [],
            }


class OpenAICompatAdapter:
    """通用 OpenAI / Webhook 兼容接口适配器 (E11 / E13)"""

    def __init__(self, client_fn: Callable[[str], str]):
        self.client_fn = client_fn

    def __call__(self, prompt: str, trace: ExecutionTrace) -> dict[str, Any]:
        resp_text = self.client_fn(prompt)
        return {
            "response": resp_text,
            "tool_calls": [],
        }
