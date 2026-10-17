from __future__ import annotations

import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from agent_test_hub.calibration import GoldenCase
from agent_test_hub.schemas import BinaryRubric, BinaryVerdict, ExecutionTrace


class AnnotationReview(BaseModel):
    """单标注员的独立盲审意见 (E16-02)"""

    model_config = ConfigDict(frozen=True)

    rater_id: str
    verdict: BinaryVerdict
    rationale: str
    evidence_span_ids: list[str] = Field(default_factory=list)
    submitted_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )


class AnnotationTask(BaseModel):
    """标注任务 (E16-01 ~ E16-03)"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_id: str
    queue_id: str
    trace: ExecutionTrace
    rubric: BinaryRubric
    status: str = "pending"  # pending, in_review, agreed, disputed, arbitrated
    reviews: list[AnnotationReview] = Field(default_factory=list)
    final_verdict: BinaryVerdict | None = None
    arbitration_rationale: str | None = None


class AnnotationQueueManager:
    """人工标注队列与校准闭环管理服务 (E16)"""

    def __init__(self, queue_id: str = "default_queue"):
        self.queue_id = queue_id
        self._tasks: dict[str, AnnotationTask] = {}

    def create_task(self, task_id: str, trace: ExecutionTrace, rubric: BinaryRubric) -> AnnotationTask:
        task = AnnotationTask(
            task_id=task_id,
            queue_id=self.queue_id,
            trace=trace,
            rubric=rubric,
            status="pending",
        )
        self._tasks[task_id] = task
        return task

    def submit_review(
        self,
        task_id: str,
        rater_id: str,
        verdict: BinaryVerdict,
        rationale: str,
        evidence_span_ids: list[str] | None = None,
    ) -> AnnotationTask:
        """提交独立盲审标注 (E16-02)"""
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"Annotation task '{task_id}' not found.")

        review = AnnotationReview(
            rater_id=rater_id,
            verdict=verdict,
            rationale=rationale,
            evidence_span_ids=evidence_span_ids or [],
        )
        task.reviews.append(review)
        task.status = "in_review"

        # 若已收集满双人盲审意见 (2 人)，自动核算一致性或标记争议
        if len(task.reviews) == 2:
            r1, r2 = task.reviews[0], task.reviews[1]
            if r1.verdict == r2.verdict:
                task.status = "agreed"
                task.final_verdict = r1.verdict
            else:
                task.status = "disputed"

        return task

    def arbitrate_dispute(
        self,
        task_id: str,
        lead_rater_id: str,
        final_verdict: BinaryVerdict,
        rationale: str,
    ) -> AnnotationTask:
        """资深裁判仲裁解决争议 (E16-03)"""
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"Annotation task '{task_id}' not found.")

        task.status = "arbitrated"
        task.final_verdict = final_verdict
        task.arbitration_rationale = f"[{lead_rater_id} 仲裁结论] {rationale}"
        return task

    def export_to_calibration_cases(self) -> list[GoldenCase]:
        """将已达成一致或仲裁确认的高质量标签导出到黄金校准集 (E16-06)"""
        golden_cases = []
        for task in self._tasks.values():
            if task.status in ("agreed", "arbitrated") and task.final_verdict:
                golden_cases.append(
                    GoldenCase(
                        case_id=task.task_id,
                        rubric=task.rubric,
                        trace=task.trace,
                        ground_truth_verdict=task.final_verdict,
                        is_synthetic=False,
                        annotation_source="人工双人盲审与合议仲裁标签",
                    )
                )
        return golden_cases

    def get_task(self, task_id: str) -> AnnotationTask | None:
        return self._tasks.get(task_id)
