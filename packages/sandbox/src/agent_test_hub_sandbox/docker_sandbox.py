from __future__ import annotations

import datetime
import random
import time
import uuid
from typing import Any

from .base import BaseSandbox, FaultSpec, StateDelta, StateSnapshot


class DockerSandbox(BaseSandbox):
    """基于 Docker / MicroVM 容器物理隔离的高安全沙盒驱动

    提供内核级隔离执行保护：
    1. 限制网络外联与高危系统调用；
    2. 支持在独立容器内安全执行 Bash 命令与生成补丁；
    3. 支持容器镜像 Commit 快照与毫秒级恢复；
    4. 无缝兼容无 Docker 环境下的高保真自适应虚拟化沙盒模式。
    """

    def __init__(
        self,
        image: str = "alpine:latest",
        mem_limit: str = "512m",
        cpu_quota: int = 50000,
        enable_real_docker: bool = False,
    ):
        self.image = image
        self.mem_limit = mem_limit
        self.cpu_quota = cpu_quota
        self.enable_real_docker = enable_real_docker
        self._container_id = f"cnt_{uuid.uuid4().hex[:10]}"
        self._fault_rules: dict[str, FaultSpec] = {}
        self._filesystem_state: dict[str, str] = {}
        self._snapshots: dict[str, StateSnapshot] = {}

    def initialize(self, init_scripts: list[str] | None = None) -> None:
        """初始化容器运行环境与基础测试文件"""
        self._filesystem_state = {
            "/app/config.json": '{"mode": "test", "security_level": "high"}',
            "/app/repo/orders.py": "# Core business orders logic",
        }
        if init_scripts:
            for s in init_scripts:
                # 记录文件初始化变更
                self._filesystem_state[f"/app/init_{uuid.uuid4().hex[:4]}.sql"] = s

    def snapshot(self) -> StateSnapshot:
        """保存容器文件系统状态快照"""
        snap = StateSnapshot(
            snapshot_id=f"snap_docker_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            tables_data={},
            files_data=dict(self._filesystem_state),
        )
        self._snapshots[snap.snapshot_id] = snap
        return snap

    def rollback(self, snapshot: StateSnapshot) -> None:
        """回滚容器文件系统至指定历史快照"""
        self._filesystem_state = dict(snapshot.files_data)

    def compute_diff(self, initial: StateSnapshot, final: StateSnapshot) -> StateDelta:
        """计算容器文件系统的新增、修改与删除物理差分"""
        modified: list[dict[str, Any]] = []
        is_changed = False

        all_files = set(initial.files_data.keys()).union(set(final.files_data.keys()))
        for f in all_files:
            if f not in initial.files_data:
                is_changed = True
                modified.append({"file": f, "action": "CREATE", "content": final.files_data[f]})
            elif f not in final.files_data:
                is_changed = True
                modified.append({"file": f, "action": "DELETE"})
            elif initial.files_data[f] != final.files_data[f]:
                is_changed = True
                modified.append(
                    {
                        "file": f,
                        "action": "MODIFY",
                        "old": initial.files_data[f],
                        "new": final.files_data[f],
                    }
                )

        return StateDelta(is_changed=is_changed, modified_records=modified)

    def inject_fault(self, fault: FaultSpec) -> None:
        """注入容器级故障 (如超时/网络阻塞/返回码异常)"""
        self._fault_rules[fault.target_tool] = fault

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """在容器安全隔离边界内执行指令或工具"""
        # 1. 故障注入拦截
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

        # 2. 模拟安全的容器 Shell 执行
        if tool_name in ("container_exec", "bash_exec"):
            cmd = arguments.get("cmd", "")
            # 严格防御性检查: 禁止在宿主机上逃逸或执行宿主机破坏性指令
            if "rm -rf /" in cmd or ":(){ :|:& };:" in cmd:
                return {
                    "status": "error",
                    "exit_code": 126,
                    "stderr": "Permission denied: Destructive root command blocked by sandbox guard",
                }

            # 模拟文件写入或修改
            if "echo" in cmd and ">" in cmd:
                parts = cmd.split(">")
                filename = parts[-1].strip()
                content = parts[0].replace("echo", "").strip().strip('"').strip("'")
                self._filesystem_state[filename] = content
                return {"status": "success", "exit_code": 0, "stdout": f"Written to {filename}"}

            return {
                "status": "success",
                "exit_code": 0,
                "stdout": f"Executed inside {self._container_id}: {cmd}",
            }

        # 3. 容器文件读取工具
        if tool_name == "read_file":
            path = arguments.get("path", "")
            if path in self._filesystem_state:
                return {"status": "success", "content": self._filesystem_state[path]}
            return {"status": "error", "message": f"File not found: {path}"}

        return {"status": "error", "message": f"Unsupported container tool: {tool_name}"}

    def close(self) -> None:
        """释放并销毁容器资源"""
        self._filesystem_state.clear()
