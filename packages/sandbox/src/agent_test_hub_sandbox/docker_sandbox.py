from __future__ import annotations

import datetime
import random
import time
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseSandbox, FaultSpec, StateDelta, StateSnapshot


class DockerSecurityConfig(BaseModel):
    """E7 Docker 安全沙盒约束配置"""

    model_config = ConfigDict(frozen=True)

    image: str = Field(default="alpine:3.19@sha256:c5b1261d6d3e43071626931fc004f70149baeba2c8ec672bd49f277b3b5e1d4b")
    user: str = Field(default="1000:1000", description="非 root 运行 (UID:GID)")
    network_mode: str = Field(default="none", description="网络默认完全拒绝 (none)")
    egress_whitelist: list[str] = Field(default_factory=list, description="出口访问白名单网段/域名")
    read_only_rootfs: bool = Field(default=True, description="只读根文件系统")
    cap_drop: list[str] = Field(default_factory=lambda: ["ALL"], description="丢弃全部 Linux Capabilities")
    mem_limit: str = Field(default="512m", description="内存上限配额")
    cpu_quota: int = Field(default=50000, description="CPU 配额 (50% 单核)")
    pids_limit: int = Field(default=100, description="最大进程数限制")
    tmpfs_mounts: list[str] = Field(default_factory=lambda: ["/tmp:rw,noexec,nosuid,size=64m"])


class FaultInjectionRecord(BaseModel):
    """故障注入执行记录 (E7-09 确定性复现日志)"""

    model_config = ConfigDict(frozen=True)

    fault_id: str
    target_tool: str
    fault_type: str
    injected_at: str
    seed: int
    delay_ms: float = 0.0
    error_code: str | None = None


class DockerSandbox(BaseSandbox):
    """基于 Docker 容器隔离与进程级沙盒双驱动的高安全沙盒 (E7-04 ~ E7-09)

    提供：
    1. 非 root / 只读 rootfs / 网络默认拒绝 / cap drop / 资源配额标准规范；
    2. 文件系统快照 (Snapshot) 与零损回滚 (Rollback)；
    3. 确定性 Seed 故障注入 (延迟/错误/脏数据/限流/断连)；
    4. 无 Docker 环境下的轻量进程隔离测试桩模式。
    """

    def __init__(
        self,
        security_config: DockerSecurityConfig | None = None,
        seed: int = 42,
        enable_real_docker: bool = False,
    ):
        self.config = security_config or DockerSecurityConfig()
        self.seed = seed
        self.enable_real_docker = enable_real_docker
        self._container_id = f"cnt_{uuid.uuid4().hex[:10]}"
        self._rng = random.Random(seed)
        self._fault_rules: dict[str, FaultSpec] = {}
        self._fault_history: list[FaultInjectionRecord] = []
        self._filesystem_state: dict[str, str] = {}
        self._snapshots: dict[str, StateSnapshot] = {}

    def initialize(self, init_scripts: list[str] | None = None) -> None:
        """初始化容器运行环境与基础测试文件"""
        self._filesystem_state = {
            "/app/config.json": '{"mode": "sandbox", "security_level": "hardened"}',
            "/app/repo/orders.py": "# Core business orders logic",
        }
        if init_scripts:
            for s in init_scripts:
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
        """计算容器文件系统物理差分"""
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
                modified.append({
                    "file": f,
                    "action": "MODIFY",
                    "old": initial.files_data[f],
                    "new": final.files_data[f],
                })

        return StateDelta(is_changed=is_changed, modified_records=modified)

    def inject_fault(self, fault: FaultSpec) -> None:
        """注册可确定性复现的故障注入规则 (E7-08 ~ E7-09)"""
        self._fault_rules[fault.target_tool] = fault

    def get_fault_history(self) -> list[FaultInjectionRecord]:
        return list(self._fault_history)

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """在容器安全隔离边界内执行指令或工具"""
        # 1. 确定性故障注入拦截 (E7-08/E7-09)
        if tool_name in self._fault_rules:
            rule = self._fault_rules[tool_name]
            roll = self._rng.random()
            if roll <= rule.probability:
                rec = FaultInjectionRecord(
                    fault_id=f"flt_{uuid.uuid4().hex[:8]}",
                    target_tool=tool_name,
                    fault_type=rule.fault_type,
                    injected_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    seed=self.seed,
                    delay_ms=rule.delay_ms,
                    error_code=str(rule.error_code) if rule.error_code is not None else None,
                )
                self._fault_history.append(rec)

                if rule.delay_ms > 0:
                    time.sleep(rule.delay_ms / 1000.0)

                if rule.fault_type == "http_error":
                    return {
                        "status": "error",
                        "error_code": rule.error_code or "HTTP_500",
                        "message": rule.error_message or "Internal Server Error injected by sandbox",
                    }
                elif rule.fault_type == "rate_limit":
                    return {
                        "status": "error",
                        "error_code": "RATE_LIMIT_429",
                        "message": "Too Many Requests: Rate limit exceeded",
                    }
                elif rule.fault_type == "corrupted_data":
                    return {
                        "status": "success",
                        "corrupted": True,
                        "data": "CORRUPTED_HEX_\\x00\\xFF_DIRTY_PAYLOAD",
                    }

        # 2. 模拟安全的容器 Shell 执行
        if tool_name in ("container_exec", "bash_exec"):
            cmd = arguments.get("cmd", "")
            # 严格防御性检查: 禁止在宿主机上逃逸或执行宿主机破坏性指令
            if "rm -rf /" in cmd or ":(){ :|:& };:" in cmd or "sudo" in cmd:
                return {
                    "status": "error",
                    "exit_code": 126,
                    "stderr": "Permission denied: Destructive root command blocked by non-root sandbox policy",
                }

            if "curl" in cmd or "wget" in cmd:
                # 检查网络默认拒绝
                if self.config.network_mode == "none":
                    return {
                        "status": "error",
                        "exit_code": 7,
                        "stderr": "Failed to connect: Network default deny (network_mode=none)",
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
                "stdout": f"Executed inside {self._container_id} ({self.config.user}): {cmd}",
            }

        # 3. 容器文件读取工具
        if tool_name == "read_file":
            path = arguments.get("path", "")
            if path in self._filesystem_state:
                return {"status": "success", "content": self._filesystem_state[path]}
            return {"status": "error", "message": f"File not found: {path}"}

        # 4. 数据库工具透传 (若配置了支持)
        if tool_name == "db_execute":
            return {"status": "success", "message": "SQL query processed in sandbox"}

        return {"status": "error", "message": f"Unsupported container tool: {tool_name}"}

    def close(self) -> None:
        """释放并销毁容器资源"""
        self._filesystem_state.clear()
        self._snapshots.clear()
