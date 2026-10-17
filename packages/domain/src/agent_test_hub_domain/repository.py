from __future__ import annotations

import datetime
import json
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from .errors import ExperimentCancelledError, NotFoundError, TenantAccessDeniedError
from .ids import canonical_json_hash, new_id
from .models import (
    AgentModel,
    AgentVersionModel,
    AuditLogModel,
    CaseModel,
    DatasetModel,
    DatasetVersionModel,
    ExperimentModel,
    ProjectModel,
    ReleaseDecisionModel,
    RunModel,
    SampleModel,
    VerdictModel,
    WorkspaceModel,
)


class BaseRepository:
    def __init__(self, session: Session):
        self.session = session


class WorkspaceRepository(BaseRepository):
    def create_workspace(self, name: str, plan: str = "team", region: str = "cn") -> WorkspaceModel:
        ws = WorkspaceModel(id=new_id("ws"), name=name, plan=plan, region=region)
        self.session.add(ws)
        self.session.flush()
        return ws

    def get_workspace(self, workspace_id: str) -> WorkspaceModel:
        ws = self.session.get(WorkspaceModel, workspace_id)
        if not ws:
            raise NotFoundError("Workspace", workspace_id)
        return ws

    def create_project(self, workspace_id: str, name: str) -> ProjectModel:
        # 校验工作区存在
        self.get_workspace(workspace_id)
        proj = ProjectModel(id=new_id("proj"), workspace_id=workspace_id, name=name)
        self.session.add(proj)
        self.session.flush()
        return proj


class AgentRepository(BaseRepository):
    def create_agent(
        self,
        project_id: str,
        name: str,
        agent_type: str = "smolagents",
        prompt: str | None = None,
        model: str = "GLM-5.3",
        tools: list[dict[str, Any]] | None = None,
        config: dict[str, Any] | None = None,
    ) -> tuple[AgentModel, AgentVersionModel]:
        agent = AgentModel(id=new_id("agent"), project_id=project_id, name=name, type=agent_type)
        self.session.add(agent)
        self.session.flush()

        tools_json = json.dumps(tools or [], ensure_ascii=False)
        config_json = json.dumps(config or {}, ensure_ascii=False)
        content_hash = canonical_json_hash({
            "prompt": prompt,
            "model": model,
            "tools": tools or [],
            "config": config or {},
        })

        version = AgentVersionModel(
            id=new_id("agv"),
            agent_id=agent.id,
            version_num=1,
            content_hash=content_hash,
            prompt=prompt,
            model=model,
            tools_json=tools_json,
            config_json=config_json,
        )
        self.session.add(version)
        self.session.flush()
        return agent, version

    def get_agent_with_tenant_check(self, agent_id: str, workspace_id: str) -> AgentModel:
        stmt = (
            select(AgentModel)
            .join(ProjectModel, AgentModel.project_id == ProjectModel.id)
            .where(AgentModel.id == agent_id, ProjectModel.workspace_id == workspace_id)
        )
        agent = self.session.execute(stmt).scalar_one_or_none()
        if not agent:
            # 判断是真正 404 还是跨租户拒绝
            raw = self.session.get(AgentModel, agent_id)
            if raw:
                raise TenantAccessDeniedError(workspace_id, agent_id)
            raise NotFoundError("Agent", agent_id)
        return agent


class DatasetRepository(BaseRepository):
    def create_dataset_with_cases(
        self,
        project_id: str,
        name: str,
        cases_data: list[dict[str, Any]],
        description: str | None = None,
    ) -> tuple[DatasetModel, DatasetVersionModel]:
        dataset = DatasetModel(id=new_id("ds"), project_id=project_id, name=name, description=description)
        self.session.add(dataset)
        self.session.flush()

        content_hash = canonical_json_hash(cases_data)
        version = DatasetVersionModel(
            id=new_id("dsv"),
            dataset_id=dataset.id,
            version_num=1,
            content_hash=content_hash,
        )
        self.session.add(version)
        self.session.flush()

        for c in cases_data:
            case = CaseModel(
                id=new_id("case"),
                dataset_version_id=version.id,
                input_text=c.get("input", ""),
                environment_spec_json=json.dumps(c.get("environment", {}), ensure_ascii=False),
                expected_state_json=json.dumps(c.get("expected_state", {}), ensure_ascii=False),
                rubric_set_json=json.dumps(c.get("rubrics", []), ensure_ascii=False),
            )
            self.session.add(case)
        self.session.flush()
        return dataset, version


class ExperimentRepository(BaseRepository):
    def create_experiment(
        self,
        project_id: str,
        name: str,
        config: dict[str, Any] | None = None,
    ) -> ExperimentModel:
        exp = ExperimentModel(
            id=new_id("exp"),
            project_id=project_id,
            name=name,
            status="pending",
            config_json=json.dumps(config or {}, ensure_ascii=False),
        )
        self.session.add(exp)
        self.session.flush()
        return exp

    def get_experiment_with_tenant_check(self, experiment_id: str, workspace_id: str) -> ExperimentModel:
        stmt = (
            select(ExperimentModel)
            .join(ProjectModel, ExperimentModel.project_id == ProjectModel.id)
            .where(ExperimentModel.id == experiment_id, ProjectModel.workspace_id == workspace_id)
        )
        exp = self.session.execute(stmt).scalar_one_or_none()
        if not exp:
            raw = self.session.get(ExperimentModel, experiment_id)
            if raw:
                raise TenantAccessDeniedError(workspace_id, experiment_id)
            raise NotFoundError("Experiment", experiment_id)
        return exp

    def cancel_experiment(self, experiment_id: str) -> None:
        """取消正在运行的实验 (E9-07)"""
        exp = self.session.get(ExperimentModel, experiment_id)
        if not exp:
            raise NotFoundError("Experiment", experiment_id)
        exp.status = "cancelled"
        exp.completed_at = datetime.datetime.now(datetime.timezone.utc)
        self.session.flush()

    def record_sample_result_idempotent(
        self,
        run_id: str,
        case_id: str,
        sample_index: int,
        is_passed: bool,
        score: float,
        duration_ms: float,
        verdicts_data: list[dict[str, Any]],
        trace_json: str | None = None,
        error_code: str | None = None,
    ) -> SampleModel:
        """幂等记录 Sample 执行结果，同一 (run_id, case_id, index) 不会重复计分 (E9-05)"""
        sample_key = f"{run_id}:{case_id}:{sample_index}"
        existing = self.session.execute(
            select(SampleModel).where(SampleModel.sample_key == sample_key)
        ).scalar_one_or_none()

        if existing:
            # 已经完成则直接返回，保证幂等
            return existing

        sample = SampleModel(
            id=new_id("spl"),
            run_id=run_id,
            case_id=case_id,
            sample_index=sample_index,
            sample_key=sample_key,
            status="completed" if not error_code else "failed",
            is_passed=is_passed,
            score=score,
            duration_ms=duration_ms,
            error_code=error_code,
            trace_json=trace_json,
        )
        self.session.add(sample)
        self.session.flush()

        for v in verdicts_data:
            verdict = VerdictModel(
                id=new_id("vd"),
                sample_id=sample.id,
                rubric_id=v.get("rubric_id", ""),
                judge_role=v.get("judge_role", ""),
                verdict=v.get("verdict", "UNKNOWN"),
                confidence=v.get("confidence", 1.0),
                rationale=v.get("rationale", ""),
                evidence_span_ids=json.dumps(v.get("evidence_span_ids", []), ensure_ascii=False),
            )
            self.session.add(verdict)
        self.session.flush()
        return sample

    def recover_incomplete_samples(self, run_id: str) -> list[SampleModel]:
        """崩溃恢复：扫描 run 中处于 pending 或 running 的遗留任务 (E9-10)"""
        stmt = select(SampleModel).where(
            SampleModel.run_id == run_id,
            SampleModel.status.in_(["pending", "running"]),
        )
        incomplete = list(self.session.execute(stmt).scalars().all())
        for spl in incomplete:
            spl.status = "pending"  # 重置为待重跑状态
        self.session.flush()
        return incomplete


class AuditRepository(BaseRepository):
    def log(
        self,
        workspace_id: str,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any] | None = None,
    ) -> AuditLogModel:
        audit = AuditLogModel(
            id=new_id("audit"),
            workspace_id=workspace_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details_json=json.dumps(details or {}, ensure_ascii=False),
        )
        self.session.add(audit)
        self.session.flush()
        return audit
