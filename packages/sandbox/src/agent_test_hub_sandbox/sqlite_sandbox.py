from __future__ import annotations

import copy
import datetime
import random
import sqlite3
import time
import uuid
from typing import Any

from .base import BaseSandbox, FaultSpec, StateDelta, StateSnapshot


class SQLiteSandbox(BaseSandbox):
    """基于 SQLite 的轻量高保真数字孪生沙盒，支持毫秒级快照与物理差分审计"""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._fault_rules: dict[str, FaultSpec] = {}
        self._snapshots: dict[str, StateSnapshot] = {}

    def initialize(self, init_scripts: list[str] | None = None) -> None:
        """执行 SQL 初始化建表与种子数据填充"""
        if init_scripts:
            cursor = self._conn.cursor()
            for script in init_scripts:
                cursor.executescript(script)
            self._conn.commit()

    def snapshot(self) -> StateSnapshot:
        """遍历所有用户数据表生成不可变深拷贝快照"""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = [row["name"] for row in cursor.fetchall()]

        tables_data: dict[str, list[dict[str, Any]]] = {}
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            tables_data[table] = [dict(row) for row in cursor.fetchall()]

        snap = StateSnapshot(
            snapshot_id=f"snap_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            tables_data=copy.deepcopy(tables_data),
        )
        self._snapshots[snap.snapshot_id] = snap
        return snap

    def rollback(self, snapshot: StateSnapshot) -> None:
        """将当前数据库完全回滚至快照状态"""
        cursor = self._conn.cursor()
        # 清空当前所有表数据
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        current_tables = [row["name"] for row in cursor.fetchall()]

        for table in current_tables:
            cursor.execute(f"DELETE FROM {table};")

        # 重新灌入快照数据
        for table, records in snapshot.tables_data.items():
            if records:
                cols = list(records[0].keys())
                placeholders = ", ".join(["?"] * len(cols))
                col_names = ", ".join(cols)
                sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
                for r in records:
                    cursor.execute(sql, [r[col] for col in cols])
        self._conn.commit()

    def compute_diff(self, initial: StateSnapshot, final: StateSnapshot) -> StateDelta:
        """计算初态与终态各数据表记录的物理差分"""
        modified: list[dict[str, Any]] = []

        all_tables = set(initial.tables_data.keys()).union(set(final.tables_data.keys()))
        is_changed = False

        for table in all_tables:
            init_rows = {str(list(r.values())[0]): r for r in initial.tables_data.get(table, [])}
            final_rows = {str(list(r.values())[0]): r for r in final.tables_data.get(table, [])}

            for pk, f_row in final_rows.items():
                if pk not in init_rows:
                    is_changed = True
                    modified.append({"table": table, "action": "INSERT", "record": f_row})
                elif f_row != init_rows[pk]:
                    is_changed = True
                    modified.append(
                        {
                            "table": table,
                            "action": "UPDATE",
                            "old": init_rows[pk],
                            "new": f_row,
                        }
                    )

            for pk, i_row in init_rows.items():
                if pk not in final_rows:
                    is_changed = True
                    modified.append({"table": table, "action": "DELETE", "record": i_row})

        return StateDelta(is_changed=is_changed, modified_records=modified)

    def inject_fault(self, fault: FaultSpec) -> None:
        """注册针对特定工具调用的故障规则"""
        self._fault_rules[fault.target_tool] = fault

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """执行被测工具并应用透明故障注入规则"""
        # 1. 检查是否存在故障注入规则
        if tool_name in self._fault_rules:
            rule = self._fault_rules[tool_name]
            if random.random() <= rule.probability:
                if rule.delay_ms > 0:
                    time.sleep(rule.delay_ms / 1000.0)

                if rule.fault_type == "http_error":
                    return {
                        "status": "error",
                        "error_code": rule.error_code,
                        "message": rule.error_message,
                    }
                elif rule.fault_type == "malformed_json":
                    return {"status": "error", "raw": '{"corrupted_json": [unclosed'}
                elif rule.fault_type == "exception":
                    raise RuntimeError(f"Injected Sandbox Exception: {rule.error_message}")

        # 2. 内置通用 SQL 执行工具与标准操作分发
        if tool_name == "db_query":
            sql = arguments.get("sql", "")
            cursor = self._conn.cursor()
            cursor.execute(sql)
            rows = [dict(r) for r in cursor.fetchall()]
            return {"status": "success", "rows": rows}
        elif tool_name == "db_execute":
            sql = arguments.get("sql", "")
            params = arguments.get("params", [])
            cursor = self._conn.cursor()
            cursor.execute(sql, params)
            self._conn.commit()
            return {"status": "success", "rows_affected": cursor.rowcount}

        return {"status": "error", "message": f"Tool '{tool_name}' not implemented in sandbox"}

    def close(self) -> None:
        """关闭数据库连接"""
        self._conn.close()
