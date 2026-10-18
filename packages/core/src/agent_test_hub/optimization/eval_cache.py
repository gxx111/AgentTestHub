from __future__ import annotations

import hashlib
import json
import threading
import time
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from agent_test_hub.schemas import BinaryRubric, BinaryVerdict, ExecutionTrace, RubricJudgment


class EvaluationCacheStats(BaseModel):
    model_config = ConfigDict(frozen=True)

    hits: int = 0
    misses: int = 0
    total_queries: int = 0
    hit_ratio: float = 0.0
    estimated_tokens_saved: int = 0
    estimated_time_saved_ms: float = 0.0


class AdaptiveEvaluationCache:
    """【缺陷四修复】自适应语义评估缓存引擎 (Adaptive Evaluation Cache)

    显著消除长推理链模型（DeepSeek-R1 / o1 / GLM-5.3）的重复推理开销：
    1. 依据 (Rubric, Trace 指纹, Judge 角色) 计算不可变哈希键；
    2. 命中缓存直接毫秒级返回结构化判决，避免重复消耗调用预算与产生超时；
    3. 全流程线程安全，可统计节省的 Token 数量与时延。
    """

    def __init__(self, max_size: int = 5000):
        self.max_size = max_size
        self._lock = threading.RLock()
        self._cache: dict[str, RubricJudgment] = {}
        self._hits = 0
        self._misses = 0

    @classmethod
    def make_cache_key(cls, rubric: BinaryRubric, trace: ExecutionTrace, judge_role: str) -> str:
        # 提取 trace 的行为指纹（事件类型、动作、工具输出）
        events_fingerprint = [
            (e.turn_index, e.actor_role.value, e.event_type.value, (e.content or "")[:300], str(e.tool_observation.arguments if e.tool_observation else ""))
            for e in trace.events
        ]
        raw_key = {
            "rubric_id": rubric.rubric_id,
            "question": rubric.question,
            "expected_verdict": rubric.expected_verdict.value,
            "judge_role": judge_role,
            "events": events_fingerprint,
        }
        key_bytes = json.dumps(raw_key, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(key_bytes).hexdigest()

    def get(self, rubric: BinaryRubric, trace: ExecutionTrace, judge_role: str) -> RubricJudgment | None:
        key = self.make_cache_key(rubric, trace, judge_role)
        with self._lock:
            if key in self._cache:
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return None

    def put(self, rubric: BinaryRubric, trace: ExecutionTrace, judge_role: str, judgment: RubricJudgment) -> None:
        key = self.make_cache_key(rubric, trace, judge_role)
        with self._lock:
            if len(self._cache) >= self.max_size:
                # 简单淘汰首个元素
                first_key = next(iter(self._cache))
                del self._cache[first_key]
            self._cache[key] = judgment

    def get_stats(self) -> EvaluationCacheStats:
        with self._lock:
            total = self._hits + self._misses
            ratio = (self._hits / total) if total > 0 else 0.0
            return EvaluationCacheStats(
                hits=self._hits,
                misses=self._misses,
                total_queries=total,
                hit_ratio=round(ratio, 4),
                estimated_tokens_saved=self._hits * 1800,  # 每次判决约消耗 1800 tokens
                estimated_time_saved_ms=self._hits * 4500.0,  # 每次判决约耗时 4.5s
            )

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
