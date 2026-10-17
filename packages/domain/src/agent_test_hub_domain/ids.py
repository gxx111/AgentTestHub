from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from typing import Any


def new_id(prefix: str = "") -> str:
    """生成带业务前缀的紧凑唯一标识 (基于时间戳与安全随机数)"""
    rand = uuid.uuid4().hex[:16]
    ts = int(time.time() * 1000)
    uid = f"{ts:x}{rand}"[:24]
    return f"{prefix}_{uid}" if prefix else uid


def canonical_json_hash(data: Any) -> str:
    """计算规范化 Canonical JSON 的 SHA-256 哈希 (键排序、紧凑分隔符、UTF-8)"""
    canonical_bytes = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()
