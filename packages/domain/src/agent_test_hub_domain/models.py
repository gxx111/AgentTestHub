from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class WorkspaceModel(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    plan: Mapped[str] = mapped_column(String(32), default="team", nullable=False)
    region: Mapped[str] = mapped_column(String(32), default="cn", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    projects: Mapped[list[ProjectModel]] = relationship(
        "ProjectModel", back_populates="workspace", cascade="all, delete-orphan"
    )


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    workspace: Mapped[WorkspaceModel] = relationship("WorkspaceModel", back_populates="projects")
    agents: Mapped[list[AgentModel]] = relationship(
        "AgentModel", back_populates="project", cascade="all, delete-orphan"
    )
    datasets: Mapped[list[DatasetModel]] = relationship(
        "DatasetModel", back_populates="project", cascade="all, delete-orphan"
    )
    experiments: Mapped[list[ExperimentModel]] = relationship(
        "ExperimentModel", back_populates="project", cascade="all, delete-orphan"
    )


class AgentModel(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), default="smolagents", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    project: Mapped[ProjectModel] = relationship("ProjectModel", back_populates="agents")
    versions: Mapped[list[AgentVersionModel]] = relationship(
        "AgentVersionModel", back_populates="agent", cascade="all, delete-orphan"
    )


class AgentVersionModel(Base):
    __tablename__ = "agent_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_num: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(128), default="GLM-5.3", nullable=False)
    tools_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    agent: Mapped[AgentModel] = relationship("AgentModel", back_populates="versions")

    __table_args__ = (Index("idx_agent_version_unique", "agent_id", "version_num", unique=True),)


class DatasetModel(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    project: Mapped[ProjectModel] = relationship("ProjectModel", back_populates="datasets")
    versions: Mapped[list[DatasetVersionModel]] = relationship(
        "DatasetVersionModel", back_populates="dataset", cascade="all, delete-orphan"
    )


class DatasetVersionModel(Base):
    __tablename__ = "dataset_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_num: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    dataset: Mapped[DatasetModel] = relationship("DatasetModel", back_populates="versions")
    cases: Mapped[list[CaseModel]] = relationship(
        "CaseModel", back_populates="version", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_dataset_version_unique", "dataset_id", "version_num", unique=True),)


class CaseModel(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dataset_version_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    environment_spec_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_state_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    rubric_set_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    version: Mapped[DatasetVersionModel] = relationship("DatasetVersionModel", back_populates="cases")


class ExperimentModel(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="pending", nullable=False
    )  # pending, running, completed, failed, cancelling, cancelled
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    started_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[ProjectModel] = relationship("ProjectModel", back_populates="experiments")
    runs: Mapped[list[RunModel]] = relationship(
        "RunModel", back_populates="experiment", cascade="all, delete-orphan"
    )


class RunModel(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_version_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("agent_versions.id"), nullable=True
    )
    dataset_version_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("dataset_versions.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    experiment: Mapped[ExperimentModel] = relationship("ExperimentModel", back_populates="runs")
    samples: Mapped[list[SampleModel]] = relationship(
        "SampleModel", back_populates="run", cascade="all, delete-orphan"
    )


class SampleModel(Base):
    __tablename__ = "samples"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sample_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sample_key: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )  # 幂等执行键 run_id:case_id:index
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    is_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trace_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    run: Mapped[RunModel] = relationship("RunModel", back_populates="samples")
    verdicts: Mapped[list[VerdictModel]] = relationship(
        "VerdictModel", back_populates="sample", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_sample_idempotent", "sample_key", unique=True),)


class VerdictModel(Base):
    __tablename__ = "verdicts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sample_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("samples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rubric_id: Mapped[str] = mapped_column(String(64), nullable=False)
    judge_role: Mapped[str] = mapped_column(String(64), nullable=False)
    verdict: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_span_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    sample: Mapped[SampleModel] = relationship("SampleModel", back_populates="verdicts")


class GatePolicyModel(Base):
    __tablename__ = "gate_policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    policy_json: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


class ReleaseDecisionModel(Base):
    __tablename__ = "release_decisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    gate_policy_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("gate_policies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    experiment_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    decision: Mapped[str] = mapped_column(String(32), nullable=False)  # PASS, BLOCK, OVERRIDE
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(64), nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
