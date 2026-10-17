from __future__ import annotations

import asyncio
import datetime
import threading
import time
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from .errors import ExperimentCancelledError


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ExecutionJob(BaseModel):
    """评测执行任务单元 (E9-05 ~ E9-07)"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    job_id: str
    experiment_id: str
    run_id: str
    case_id: str
    sample_index: int = 0
    sample_key: str
    status: JobStatus = JobStatus.PENDING
    timeout_seconds: float = 60.0
    max_retries: int = 2
    retry_count: int = 0
    started_at: float | None = None
    completed_at: float | None = None
    error_message: str | None = None
    task_fn: Any | None = None


class JobQueue:
    """线程与协程安全的执行队列管理器 (E9-06 ~ E9-10)

    提供任务入队、并发调度、动态取消、超时熔断与崩溃恢复能力。
    """

    def __init__(self, max_concurrency: int = 4):
        self.max_concurrency = max_concurrency
        self._lock = threading.RLock()
        self._jobs: dict[str, ExecutionJob] = {}
        self._queue: list[str] = []
        self._cancelled_experiments: set[str] = set()

    def enqueue(self, job: ExecutionJob) -> None:
        with self._lock:
            self._jobs[job.job_id] = job
            self._queue.append(job.job_id)

    def dequeue(self) -> ExecutionJob | None:
        with self._lock:
            while self._queue:
                job_id = self._queue.pop(0)
                job = self._jobs.get(job_id)
                if not job:
                    continue
                # 若其所属实验已被取消，直接置为 CANCELLED 并跳过
                if job.experiment_id in self._cancelled_experiments:
                    job.status = JobStatus.CANCELLED
                    job.completed_at = time.time()
                    continue
                job.status = JobStatus.RUNNING
                job.started_at = time.time()
                return job
            return None

    def cancel_experiment(self, experiment_id: str) -> None:
        """取消指定实验的所有任务 (E9-07)"""
        with self._lock:
            self._cancelled_experiments.add(experiment_id)
            for job in self._jobs.values():
                if job.experiment_id == experiment_id and job.status in (JobStatus.PENDING, JobStatus.RUNNING):
                    job.status = JobStatus.CANCELLED
                    job.completed_at = time.time()
                    job.error_message = "Cancelled by user"

    def is_cancelled(self, experiment_id: str) -> bool:
        with self._lock:
            return experiment_id in self._cancelled_experiments

    def check_and_handle_timeouts(self) -> list[str]:
        """检测并熔断超时任务 (E9-02)"""
        timed_out_ids = []
        now = time.time()
        with self._lock:
            for job in self._jobs.values():
                if job.status == JobStatus.RUNNING and job.started_at:
                    if (now - job.started_at) > job.timeout_seconds:
                        timed_out_ids.append(job.job_id)
                        if job.retry_count < job.max_retries:
                            # 触发重试
                            job.retry_count += 1
                            job.status = JobStatus.PENDING
                            job.started_at = None
                            self._queue.append(job.job_id)
                        else:
                            job.status = JobStatus.TIMEOUT
                            job.completed_at = now
                            job.error_message = f"Job timed out after {job.timeout_seconds}s"
        return timed_out_ids

    def recover_crashed_jobs(self) -> int:
        """崩溃恢复：将异常中断/遗留状态重置为待重跑 (E9-10)"""
        recovered = 0
        with self._lock:
            for job in self._jobs.values():
                if job.status == JobStatus.RUNNING:
                    job.status = JobStatus.PENDING
                    job.started_at = None
                    self._queue.append(job.job_id)
                    recovered += 1
        return recovered

    def get_job(self, job_id: str) -> ExecutionJob | None:
        with self._lock:
            return self._jobs.get(job_id)
