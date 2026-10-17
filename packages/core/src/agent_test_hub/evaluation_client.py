from __future__ import annotations

import threading
import time

import litellm

from .schemas import ActorRole, TraceEvent, TraceEventType


class EvaluationBudgetExceededError(RuntimeError):
    pass


class EvaluationModelError(RuntimeError):
    pass


class EvaluationClient:
    """Shared per-case call budget and observable, credential-free model requests."""

    def __init__(self, max_calls: int, deadline_seconds: float):
        self.remaining = max_calls
        self.deadline = time.monotonic() + deadline_seconds
        self.lock = threading.Lock()
        self.emit = None
        self.failed = False

    def bind(self, emit):
        self.emit = emit

    def for_role(self, role: str):
        def complete(**kwargs):
            with self.lock:
                if self.remaining <= 0 or time.monotonic() >= self.deadline:
                    self.failed = True
                    raise EvaluationBudgetExceededError("Evaluation call budget exhausted")
                self.remaining -= 1
            started = time.monotonic()
            metadata = {"model_name": kwargs["model"], "status": "started"}
            self._emit(role, "模型请求已发出", metadata)
            try:
                kwargs["timeout"] = min(
                    kwargs.get("timeout", 30), max(0.1, self.deadline - started)
                )
                kwargs["num_retries"] = 0
                response = litellm.completion(**kwargs)
                usage = getattr(response, "usage", None)
                tokens = int(getattr(usage, "total_tokens", 0) or 0)
                self._emit(
                    role, "模型响应已收到",
                    {
                        **metadata,
                        "status": "completed",
                        "duration_ms": (time.monotonic() - started) * 1000,
                    },
                    tokens,
                )
                return response
            except Exception as exc:
                with self.lock:
                    self.failed = True
                self._emit(
                    role, "模型调用失败",
                    {**metadata, "status": "error", "error_type": type(exc).__name__},
                )
                raise EvaluationModelError(type(exc).__name__) from None
        return complete

    def _emit(self, role, content, metadata, tokens=0):
        if self.emit:
            with self.lock:
                self.emit(TraceEvent(
                    actor_role=ActorRole(role),
                    actor_name=role,
                    event_type=TraceEventType.EVALUATOR_CALL,
                    content=content,
                    metadata=metadata,
                    tokens_consumed=tokens,
                ))
