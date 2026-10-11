from __future__ import annotations

from typing import Any

import networkx as nx
from agent_test_hub.schemas import ExecutionTrace, TraceEventType

from ..base import BaseMetric, MetricResult


class CommunicationSNRMetric(BaseMetric):
    """MAS 协同度量 1: 团队通信信噪比 (Signal-to-Noise Ratio)"""

    name: str = "mas_communication_snr"
    dimension: str = "MAS_Fidelity"

    def __init__(self, min_valid_ratio: float = 0.65):
        self.min_valid_ratio = min_valid_ratio
        # 常见冗余闲聊词表
        self.chatter_keywords = [
            "收到",
            "好的",
            "没问题",
            "辛苦",
            "roger that",
            "got it",
            "acknowledged",
            "thanks",
        ]

    def evaluate(
        self, trace: ExecutionTrace, context: dict[str, Any] | None = None
    ) -> MetricResult:
        messages = [
            e.content.strip().lower()
            for e in trace.events
            if e.event_type in (TraceEventType.AGENT_MESSAGE, TraceEventType.USER_MESSAGE)
        ]

        if not messages:
            return MetricResult(
                metric_name=self.name,
                dimension=self.dimension,
                score=1.0,
                is_passed=True,
                rationale="无团队通信消息，信噪比默认满分",
            )

        chatter_count = 0
        for msg in messages:
            # 简短且完全由闲聊词组成
            if len(msg) < 20 and any(kw in msg for kw in self.chatter_keywords):
                chatter_count += 1

        snr = 1.0 - (chatter_count / len(messages))
        is_passed = snr >= self.min_valid_ratio

        return MetricResult(
            metric_name=self.name,
            dimension=self.dimension,
            score=round(snr, 4),
            is_passed=is_passed,
            details={
                "total_messages": len(messages),
                "chatter_messages": chatter_count,
                "snr": snr,
            },
            rationale=f"团队通信信噪比为 {snr:.1%} (冗余寒暄消息占比 {chatter_count}/{len(messages)})",
        )


class MASDeadlockDetectorMetric(BaseMetric):
    """MAS 协同度量 2: 多智能体级联死锁识别 (基于 NetworkX 有向环检测)"""

    name: str = "mas_deadlock_detection"
    dimension: str = "MAS_Consensus"

    def __init__(self, min_cycle_weight: int = 2):
        self.min_cycle_weight = min_cycle_weight

    def evaluate(
        self, trace: ExecutionTrace, context: dict[str, Any] | None = None
    ) -> MetricResult:
        # 构建 Agent 间消息交互依赖图 (有向图 DiGraph)
        g = nx.DiGraph()

        prev_actor: str | None = None
        for event in trace.events:
            current_actor = event.actor_name
            if prev_actor and prev_actor != current_actor:
                if g.has_edge(prev_actor, current_actor):
                    g[prev_actor][current_actor]["weight"] += 1
                else:
                    g.add_edge(prev_actor, current_actor, weight=1)
            prev_actor = current_actor

        # 检测依赖图中的有向环 (Cycles) 且每条边的权重大于等于阈值 (说明在反复互相推诿/等待)
        deadlock_cycles = []
        try:
            cycles = list(nx.simple_cycles(g))
            for cycle in cycles:
                if len(cycle) >= 2:
                    # 检查环路上每个转移是否发生多次
                    is_heavy_cycle = True
                    for i in range(len(cycle)):
                        u = cycle[i]
                        v = cycle[(i + 1) % len(cycle)]
                        if g[u][v]["weight"] < self.min_cycle_weight:
                            is_heavy_cycle = False
                            break
                    if is_heavy_cycle:
                        deadlock_cycles.append(cycle)
        except Exception:
            deadlock_cycles = []

        has_deadlock = len(deadlock_cycles) > 0
        score = 0.0 if has_deadlock else 1.0

        return MetricResult(
            metric_name=self.name,
            dimension=self.dimension,
            score=score,
            is_passed=not has_deadlock,
            details={"deadlock_cycles": deadlock_cycles},
            rationale=f"检测到智能体团队存在互相等待死锁环: {deadlock_cycles}"
            if has_deadlock
            else "未发生级联通信死锁",
        )
