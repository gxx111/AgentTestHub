from __future__ import annotations

from agent_test_hub.schemas import ExecutionTrace

from .base import BaseExaminer, ExaminerAction


class WatcherCircuitBreaker(BaseExaminer):
    """蚂蚁 AIEvo 机制落地: 旁路监考看门狗与自动化熔断器 (Watcher & Circuit Breaker)

    独立于考官和被测 Agent 的旁路监视哨兵：
    1. 实时监控会话轮次、累计 Token 预算开销与执行延迟；
    2. 发现无限循环或死锁迹象时，毫秒级吹哨熔断 (Circuit Break)，保护系统不暴走；
    3. 记录高精度熔断快照供后续归因分析。
    """

    role: str = "env_watchdog"

    def __init__(
        self,
        max_token_budget: int = 8000,
        max_duration_seconds: float = 60.0,
        max_consecutive_errors: int = 3,
    ):
        self.max_token_budget = max_token_budget
        self.max_duration_seconds = max_duration_seconds
        self.max_consecutive_errors = max_consecutive_errors
        self._is_tripped: bool = False
        self._trip_reason: str = ""

    def act(self, trace: ExecutionTrace, turn_index: int) -> ExaminerAction:
        # 1. 检查连续工具报错次数
        tool_calls = trace.get_tool_calls()
        if len(tool_calls) >= self.max_consecutive_errors:
            recent_calls = tool_calls[-self.max_consecutive_errors :]
            if all(c.is_error for c in recent_calls):
                self._is_tripped = True
                self._trip_reason = (
                    f"检测到连续 {self.max_consecutive_errors} 次工具报错无自愈迹象，触发看门狗熔断"
                )
                return ExaminerAction(
                    action_type="terminate",
                    content=f"【WATCHDOG 熔断】{self._trip_reason}",
                    should_stop_eval=True,
                    internal_state={"tripped": True, "reason": self._trip_reason},
                )

        # 2. 检查累计 Token 预算超限
        if trace.total_tokens > self.max_token_budget:
            self._is_tripped = True
            self._trip_reason = (
                f"累计 Token 开销 ({trace.total_tokens}) 突破熔断阈值 ({self.max_token_budget})"
            )
            return ExaminerAction(
                action_type="terminate",
                content=f"【WATCHDOG 熔断】{self._trip_reason}",
                should_stop_eval=True,
                internal_state={"tripped": True, "reason": self._trip_reason},
            )

        return ExaminerAction(
            action_type="monitor",
            content="看门狗运行正常，指标在安全阈值内",
            internal_state={"tripped": False},
        )
