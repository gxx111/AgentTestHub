from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from agent_test_hub_domain import (
    AgentRepository,
    AuditRepository,
    Base,
    DatasetRepository,
    ExperimentRepository,
    NotFoundError,
    TenantAccessDeniedError,
    WorkspaceRepository,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_workspace_and_project_creation(db_session: Session):
    ws_repo = WorkspaceRepository(db_session)
    ws = ws_repo.create_workspace("Enterprise Workspace", plan="enterprise", region="cn")
    assert ws.id.startswith("ws_")
    assert ws.name == "Enterprise Workspace"

    proj = ws_repo.create_project(ws.id, "Core Agent Project")
    assert proj.id.startswith("proj_")
    assert proj.workspace_id == ws.id


def test_agent_and_dataset_with_immutable_versions(db_session: Session):
    ws_repo = WorkspaceRepository(db_session)
    ws = ws_repo.create_workspace("Test WS")
    proj = ws_repo.create_project(ws.id, "Proj")

    # 1. Agent 与不可变版本
    agent_repo = AgentRepository(db_session)
    agent, version = agent_repo.create_agent(
        project_id=proj.id,
        name="Customer Service Agent",
        model="GLM-5.3",
        prompt="You are a helpful assistant.",
        tools=[{"name": "db_execute"}],
    )
    assert agent.id.startswith("agent_")
    assert version.version_num == 1
    assert len(version.content_hash) == 64  # SHA-256

    # 2. Dataset 与用例
    ds_repo = DatasetRepository(db_session)
    dataset, ds_ver = ds_repo.create_dataset_with_cases(
        project_id=proj.id,
        name="Refund Benchmark",
        cases_data=[
            {"input": "refund ORD_1", "expected_state": {"status": "CANCELLED"}},
            {"input": "refund ORD_2", "expected_state": {"status": "CANCELLED"}},
        ],
    )
    assert dataset.id.startswith("ds_")
    assert ds_ver.version_num == 1
    assert len(ds_ver.cases) == 2


def test_multi_tenant_isolation_raises_access_denied(db_session: Session):
    """验证 E1-15: 跨租户访问抛出 TenantAccessDeniedError (无数据泄露)"""
    ws_repo = WorkspaceRepository(db_session)
    agent_repo = AgentRepository(db_session)
    exp_repo = ExperimentRepository(db_session)

    # 租户 A
    ws_a = ws_repo.create_workspace("Tenant A")
    proj_a = ws_repo.create_project(ws_a.id, "Proj A")
    agent_a, _ = agent_repo.create_agent(proj_a.id, "Agent A")
    exp_a = exp_repo.create_experiment(proj_a.id, "Exp A")

    # 租户 B
    ws_b = ws_repo.create_workspace("Tenant B")

    # 租户 B 试图访问租户 A 的 Agent
    with pytest.raises(TenantAccessDeniedError) as exc_info:
        agent_repo.get_agent_with_tenant_check(agent_a.id, workspace_id=ws_b.id)
    assert exc_info.value.code == "TENANT_ACCESS_DENIED"

    # 租户 B 试图访问租户 A 的 Experiment
    with pytest.raises(TenantAccessDeniedError) as exc_info_exp:
        exp_repo.get_experiment_with_tenant_check(exp_a.id, workspace_id=ws_b.id)
    assert exc_info_exp.value.code == "TENANT_ACCESS_DENIED"


def test_experiment_idempotency_and_cancellation(db_session: Session):
    """验证 E9-05/E9-07: 幂等 Sample 记录与实验取消"""
    ws_repo = WorkspaceRepository(db_session)
    exp_repo = ExperimentRepository(db_session)

    ws = ws_repo.create_workspace("Test WS")
    proj = ws_repo.create_project(ws.id, "Proj")
    exp = exp_repo.create_experiment(proj.id, "Batch Eval")

    # 1. 幂等执行记录 Sample
    run_id = "run_001"
    sample1 = exp_repo.record_sample_result_idempotent(
        run_id=run_id,
        case_id="case_001",
        sample_index=0,
        is_passed=True,
        score=1.0,
        duration_ms=120.0,
        verdicts_data=[{"rubric_id": "r1", "judge_role": "rule_judge", "verdict": "YES"}],
    )
    assert sample1.id.startswith("spl_")

    # 重复写入相同 sample_key，直接返回已有记录，不重复创建
    sample2 = exp_repo.record_sample_result_idempotent(
        run_id=run_id,
        case_id="case_001",
        sample_index=0,
        is_passed=True,
        score=1.0,
        duration_ms=120.0,
        verdicts_data=[],
    )
    assert sample1.id == sample2.id

    # 2. 取消实验
    exp_repo.cancel_experiment(exp.id)
    cancelled_exp = exp_repo.get_experiment_with_tenant_check(exp.id, ws.id)
    assert cancelled_exp.status == "cancelled"
    assert cancelled_exp.completed_at is not None
