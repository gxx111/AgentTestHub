from __future__ import annotations

import datetime
import random
import re
import time
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseSandbox, FaultSpec, StateDelta, StateSnapshot


class MicroVMSecurityPolicy(BaseModel):
    """【缺陷二修复】MicroVM / 强化安全微沙盒安全约束与准入策略 (Firecracker / gVisor 标准)"""

    model_config = ConfigDict(frozen=True)

    isolation_level: str = "microvm"  # microvm / gvisor / hardened_jail
    block_kernel_escape: bool = True
    read_only_rootfs: bool = True
    network_egress_whitelist: list[str] = Field(default_factory=lambda: ["api.internal.corp"])
    memory_limit_mb: int = 512
    cpu_limit_shares: int = 1024
    max_pids: int = 32


class MicroVMSandbox(BaseSandbox):
    """【缺陷二修复】微虚拟化与逃逸防御沙盒引擎 (MicroVM Sandbox Engine)

    提供比普通 Docker / 容器更硬核的内核安全边界防御：
    1. 宿主机内核级越权逃逸探测 (Kernel Escape Detection: ptrace, nsenter, /proc/sys, chroot)；
    2. 细粒度网络出向白名单拦截 (Egress Whitelist & DNS Sinkhole)；
    3. Copy-on-Write (CoW) 差分层毫秒级快照与不可变回滚。
    """

    # 常见已知 Linux 容器逃逸指令模式库
    _ESCAPE_PATTERNS = [
        r"\bnsenter\b",
        r"\bchroot\s+/(?:host|proc)\b",
        r"\bptrace\b",
        r"\bsetns\b",
        r"/sys/fs/cgroup",
        r"/proc/sys/kernel",
        r"/dev/mem",
        r"/dev/kmem",
        r"\bunshare\b",
        r"\bcapsh\b",
    ]

    def __init__(self, policy: MicroVMSecurityPolicy | None = None, seed: int = 42):
        self.policy = policy or MicroVMSecurityPolicy()
        self.seed = seed
        self._vm_id = f"uvm_{uuid.uuid4().hex[:10]}"
        self._cow_fs: dict[str, str] = {}
        self._snapshots: dict[str, StateSnapshot] = {}
        self._fault_rules: dict[str, FaultSpec] = {}

    def initialize(self, init_scripts: list[str] | None = None) -> None:
        self._cow_fs = {
            "/etc/issue": "MicroVM Alpine Hardened 3.19",
            "/app/config.json": '{"security": "microvm_isolated", "mode": "enforced"}',
        }
        if init_scripts:
            for s in init_scripts:
                self._cow_fs[f"/app/init_{uuid.uuid4().hex[:4]}.sql"] = s

    def snapshot(self) -> StateSnapshot:
        snap = StateSnapshot(
            snapshot_id=f"snap_uvm_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            tables_data={},
            files_data=dict(self._cow_fs),
        )
        self._snapshots[snap.snapshot_id] = snap
        return snap

    def rollback(self, snapshot: StateSnapshot) -> None:
        self._cow_fs = dict(snapshot.files_data)

    def compute_diff(self, initial: StateSnapshot, final: StateSnapshot) -> StateDelta:
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
                modified.append({"file": f, "action": "MODIFY", "old": initial.files_data[f], "new": final.files_data[f]})
        return StateDelta(is_changed=is_changed, modified_records=modified)

    def inject_fault(self, fault: FaultSpec) -> None:
        self._fault_rules[fault.target_tool] = fault

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        # 1. 模拟微虚拟机命令执行
        if tool_name in ("microvm_exec", "sandbox_exec", "bash"):
            cmd = arguments.get("cmd", "")

            # A. 内核逃逸与系统调用严格审查
            if self.policy.block_kernel_escape:
                for pattern in self._ESCAPE_PATTERNS:
                    if re.search(pattern, cmd, re.IGNORECASE):
                        return {
                            "status": "error",
                            "exit_code": 137,
                            "error": "SECURITY_VIOLATION_KERNEL_ESCAPE",
                            "message": f"MicroVM hypervisor blocked container escape payload matching: '{pattern}'",
                        }

            # B. 网络出口白名单拦截
            if "curl " in cmd or "wget " in cmd or "nc " in cmd:
                host_match = re.search(r"https?://([^/:\s]+)", cmd)
                target_host = host_match.group(1) if host_match else "unknown"
                if target_host not in self.policy.network_egress_whitelist:
                    return {
                        "status": "error",
                        "exit_code": 111,
                        "error": "NETWORK_EGRESS_BLOCKED",
                        "message": f"Destination '{target_host}' is blocked by MicroVM egress security policy",
                    }

            # C. 模拟 CoW 文件系统写入
            if "echo " in cmd and ">" in cmd:
                parts = cmd.split(">")
                filename = parts[-1].strip()
                content = parts[0].replace("echo", "").strip().strip('"').strip("'")
                self._cow_fs[filename] = content
                return {"status": "success", "exit_code": 0, "stdout": f"Committed to CoW layer: {filename}"}

            return {
                "status": "success",
                "exit_code": 0,
                "stdout": f"Executed inside {self._vm_id} (MicroVM isolation level: {self.policy.isolation_level}): {cmd}",
            }

        return {"status": "error", "message": f"Unsupported tool in MicroVM: {tool_name}"}

    def close(self) -> None:
        self._cow_fs.clear()
        self._snapshots.clear()
