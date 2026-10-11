from agent_test_hub.adapters import LiteLLMAgentAdapter
from agent_test_hub.schemas import ExecutionTrace, ToolDefinition


def test_litellm_adapter_tool_formatting():
    """测试将 ToolDefinition 转换为标准 OpenAI tools JSON schema"""
    tool = ToolDefinition(
        name="refund_order",
        description="执行订单退款",
        parameters_schema={
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    )

    adapter = LiteLLMAgentAdapter(model="gpt-4o", tools=[tool], mock_mode=True)
    tools_spec = adapter._convert_tools_to_openai_format()

    assert len(tools_spec) == 1
    assert tools_spec[0]["type"] == "function"
    assert tools_spec[0]["function"]["name"] == "refund_order"
    assert "order_id" in tools_spec[0]["function"]["parameters"]["properties"]


def test_litellm_adapter_mock_mode_step():
    """测试离线/Mock 模式下的多轮推理分发"""
    trace = ExecutionTrace(task_id="t_mock")
    mock_responses = [
        {"response": "正在核实凭证...", "tool_calls": []},
        {
            "response": "核验通过，正在执行退款",
            "tool_calls": [{"name": "refund_order", "arguments": {"order_id": "ORD_1001"}}],
        },
    ]

    adapter = LiteLLMAgentAdapter(
        model="claude-3-5-sonnet",
        mock_mode=True,
        mock_responses=mock_responses,
    )

    step1 = adapter.step("我需要退款", trace)
    assert step1["response"] == "正在核实凭证..."
    assert len(step1["tool_calls"]) == 0

    step2 = adapter.step("已上传凭证", trace)
    assert step2["response"] == "核验通过，正在执行退款"
    assert len(step2["tool_calls"]) == 1
    assert step2["tool_calls"][0]["name"] == "refund_order"
