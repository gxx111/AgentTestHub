from agent_test_hub_sandbox import FaultSpec, SQLiteSandbox


def test_sqlite_sandbox_snapshot_and_diff():
    """测试沙盒状态快照与真实的数据库物理差分计算"""
    sandbox = SQLiteSandbox()
    init_sql = """
    CREATE TABLE orders (
        order_id TEXT PRIMARY KEY,
        amount REAL,
        status TEXT
    );
    INSERT INTO orders VALUES ('ORD_1001', 99.0, 'PAID');
    """
    sandbox.initialize([init_sql])

    # 1. 记录初态快照
    snap_before = sandbox.snapshot()
    assert "orders" in snap_before.tables_data
    assert len(snap_before.tables_data["orders"]) == 1
    assert snap_before.tables_data["orders"][0]["status"] == "PAID"

    # 2. Agent 模拟执行工具修改数据库状态
    res = sandbox.execute_tool(
        "db_execute",
        {
            "sql": "UPDATE orders SET status = ? WHERE order_id = ?",
            "params": ["CANCELLED", "ORD_1001"],
        },
    )
    assert res["status"] == "success"
    assert res["rows_affected"] == 1

    # 3. 记录终态快照并计算客观差分
    snap_after = sandbox.snapshot()
    delta = sandbox.compute_diff(snap_before, snap_after)
    assert delta.is_changed is True
    assert len(delta.modified_records) == 1
    mod = delta.modified_records[0]
    assert mod["action"] == "UPDATE"
    assert mod["old"]["status"] == "PAID"
    assert mod["new"]["status"] == "CANCELLED"

    # 4. 验证回滚能力
    sandbox.rollback(snap_before)
    snap_reverted = sandbox.snapshot()
    assert snap_reverted.tables_data["orders"][0]["status"] == "PAID"
    sandbox.close()


def test_sqlite_sandbox_fault_injection():
    """测试透明故障注入 (HTTP 错误与延迟拦截)"""
    sandbox = SQLiteSandbox()
    fault = FaultSpec(
        fault_type="http_error",
        target_tool="remote_api",
        error_code=502,
        error_message="Bad Gateway",
        probability=1.0,
    )
    sandbox.inject_fault(fault)

    res = sandbox.execute_tool("remote_api", {"param": 1})
    assert res["status"] == "error"
    assert res["error_code"] == 502
    assert "Bad Gateway" in res["message"]
    sandbox.close()


def test_sqlite_sandbox_query_results_and_dangerous_sql_are_controlled():
    sandbox = SQLiteSandbox()
    sandbox.initialize(
        [
            "CREATE TABLE orders (order_id TEXT PRIMARY KEY, status TEXT);"
            "INSERT INTO orders VALUES ('ORD_1', 'SHIPPED');"
        ]
    )

    query = sandbox.execute_tool(
        "db_execute", {"sql": "SELECT * FROM orders WHERE order_id = ?", "params": ["ORD_1"]}
    )
    assert query["rows"] == [{"order_id": "ORD_1", "status": "SHIPPED"}]

    blocked = sandbox.execute_tool("db_execute", {"sql": "DROP TABLE orders;"})
    assert blocked["status"] == "error"
    assert blocked["error_code"] == "dangerous_sql_blocked"
    assert sandbox.snapshot().tables_data["orders"]
    sandbox.close()


def test_read_only_query_tool_cannot_mutate_or_bypass_destructive_guard():
    sandbox = SQLiteSandbox()
    sandbox.initialize(
        [
            "CREATE TABLE orders (order_id TEXT PRIMARY KEY, status TEXT);"
            "INSERT INTO orders VALUES ('ORD_1', 'SHIPPED');"
        ]
    )
    for sql in (
        "UPDATE orders SET status = 'CANCELLED'",
        "WITH target AS (SELECT order_id FROM orders) DELETE FROM orders",
        "PRAGMA writable_schema = ON",
        "DROP TABLE orders",
    ):
        result = sandbox.execute_tool("db_query", {"sql": sql})
        assert result["status"] == "error"
        assert result["error_code"] == "dangerous_sql_blocked"
        assert sandbox.snapshot().tables_data["orders"] == [
            {"order_id": "ORD_1", "status": "SHIPPED"}
        ]

    delete = sandbox.execute_tool("db_execute", {"sql": "WITH target AS (SELECT 1) DELETE FROM orders"})
    assert delete["status"] == "error"
    assert delete["error_code"] == "dangerous_sql_blocked"
    assert sandbox.snapshot().tables_data["orders"]
    sandbox.close()
