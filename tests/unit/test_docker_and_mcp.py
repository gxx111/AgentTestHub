from agent_test_hub_sandbox import DockerSandbox, FaultSpec, MCPProxy, MCPToolSchema


def test_docker_sandbox_file_diff_and_command():
    """测试 Docker 容器沙盒的文件系统快照、差分与命令执行隔离"""
    sandbox = DockerSandbox()
    sandbox.initialize()

    # 1. 记录初始快照
    snap1 = sandbox.snapshot()
    assert "/app/config.json" in snap1.files_data

    # 2. 执行安全指令写入新文件
    res = sandbox.execute_tool("container_exec", {"cmd": "echo 'print(1)' > /app/test.py"})
    assert res["status"] == "success"
    assert res["exit_code"] == 0

    # 3. 记录终态并计算物理差分
    snap2 = sandbox.snapshot()
    diff = sandbox.compute_diff(snap1, snap2)
    assert diff.is_changed is True
    assert any(m.get("file") == "/app/test.py" for m in diff.modified_records)

    # 4. 验证恶意越权命令被沙盒拦截
    danger_res = sandbox.execute_tool("container_exec", {"cmd": "rm -rf / --no-preserve-root"})
    assert danger_res["status"] == "error"
    assert danger_res["exit_code"] == 126
    sandbox.close()


def test_mcp_proxy_protocol_and_fault_injection():
    """测试 Anthropic MCP 协议网关 tools/list、tools/call 与透明故障拦截"""
    proxy = MCPProxy(server_name="payment_mcp_server")

    tool = MCPToolSchema(
        name="process_payment",
        description="执行跨境支付结算",
        inputSchema={"type": "object", "properties": {"amount": {"type": "number"}}},
    )
    proxy.register_tool(tool)

    # 1. 测试 MCP tools/list
    tools_list = proxy.list_tools()
    assert len(tools_list) == 1
    assert tools_list[0]["name"] == "process_payment"

    # 2. 正常调用 tools/call
    res_normal = proxy.call_tool("process_payment", {"amount": 200.0})
    assert res_normal["jsonrpc"] == "2.0"
    assert "result" in res_normal
    assert res_normal["result"]["isError"] is False

    # 3. 注入网络故障并调用
    fault = FaultSpec(
        fault_type="http_error",
        target_tool="process_payment",
        error_code=502,
        error_message="Gateway Timeout",
        probability=1.0,
    )
    proxy.inject_fault(fault)

    res_fault = proxy.call_tool("process_payment", {"amount": 200.0})
    assert res_fault["jsonrpc"] == "2.0"
    assert "error" in res_fault
    assert res_fault["error"]["code"] == -32603
    assert "502" in res_fault["error"]["message"]
