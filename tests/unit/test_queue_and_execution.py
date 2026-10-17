from __future__ import annotations

import time
import pytest

from agent_test_hub_domain.queue import ExecutionJob, JobQueue, JobStatus


def test_job_queue_enqueue_dequeue():
    queue = JobQueue(max_concurrency=2)
    job1 = ExecutionJob(
        job_id="job_1",
        experiment_id="exp_1",
        run_id="run_1",
        case_id="case_1",
        sample_key="run_1:case_1:0",
    )
    job2 = ExecutionJob(
        job_id="job_2",
        experiment_id="exp_1",
        run_id="run_1",
        case_id="case_2",
        sample_key="run_1:case_2:0",
    )

    queue.enqueue(job1)
    queue.enqueue(job2)

    d1 = queue.dequeue()
    assert d1 is not None
    assert d1.job_id == "job_1"
    assert d1.status == JobStatus.RUNNING

    d2 = queue.dequeue()
    assert d2 is not None
    assert d2.job_id == "job_2"
    assert d2.status == JobStatus.RUNNING

    d3 = queue.dequeue()
    assert d3 is None


def test_experiment_cancellation_in_queue():
    """验证 E9-07: 实验可被取消，已入队和运行中的任务均标记为 CANCELLED"""
    queue = JobQueue()
    job1 = ExecutionJob(
        job_id="job_cancel_1",
        experiment_id="exp_to_cancel",
        run_id="run_1",
        case_id="case_1",
        sample_key="run_1:case_1:0",
    )
    job2 = ExecutionJob(
        job_id="job_cancel_2",
        experiment_id="exp_to_cancel",
        run_id="run_1",
        case_id="case_2",
        sample_key="run_1:case_2:0",
    )

    queue.enqueue(job1)
    queue.enqueue(job2)

    # 取消实验
    queue.cancel_experiment("exp_to_cancel")
    assert queue.is_cancelled("exp_to_cancel") is True

    # 再次 dequeue 应当自动跳过已被取消的实验
    d = queue.dequeue()
    assert d is None
    assert queue.get_job("job_cancel_1").status == JobStatus.CANCELLED
    assert queue.get_job("job_cancel_2").status == JobStatus.CANCELLED


def test_timeout_and_retry_mechanism():
    """验证 E9-02: 超时熔断与重试"""
    queue = JobQueue()
    job = ExecutionJob(
        job_id="job_timeout",
        experiment_id="exp_t",
        run_id="run_t",
        case_id="case_t",
        sample_key="run_t:case_t:0",
        timeout_seconds=0.05,  # 50ms 超时
        max_retries=1,
    )
    queue.enqueue(job)

    running_job = queue.dequeue()
    assert running_job.status == JobStatus.RUNNING

    # 等待超过超时阈值
    time.sleep(0.08)
    timed_out = queue.check_and_handle_timeouts()
    assert "job_timeout" in timed_out

    # 首次超时应触发重试 (状态变为 PENDING 并重新入队)
    job_after_retry = queue.get_job("job_timeout")
    assert job_after_retry.status == JobStatus.PENDING
    assert job_after_retry.retry_count == 1

    # 再次 dequeue 并超时，超过 max_retries 则变为 TIMEOUT 终态
    d_retry = queue.dequeue()
    assert d_retry.status == JobStatus.RUNNING
    time.sleep(0.08)
    queue.check_and_handle_timeouts()

    final_job = queue.get_job("job_timeout")
    assert final_job.status == JobStatus.TIMEOUT
    assert "Job timed out" in final_job.error_message


def test_crash_recovery():
    """验证 E9-10: 崩溃恢复重置遗留 running 任务"""
    queue = JobQueue()
    job = ExecutionJob(
        job_id="job_crash",
        experiment_id="exp_c",
        run_id="run_c",
        case_id="case_c",
        sample_key="run_c:case_c:0",
    )
    queue.enqueue(job)
    running = queue.dequeue()
    assert running.status == JobStatus.RUNNING

    # 模拟 Worker 崩溃重启，执行恢复
    recovered_count = queue.recover_crashed_jobs()
    assert recovered_count == 1
    assert queue.get_job("job_crash").status == JobStatus.PENDING

    # 恢复后可再次被 dequeue 执行
    re_dequeued = queue.dequeue()
    assert re_dequeued is not None
    assert re_dequeued.job_id == "job_crash"
