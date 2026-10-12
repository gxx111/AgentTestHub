import pytest
from agent_test_hub_server import app, db
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "server.db")
    with TestClient(app) as test_client:
        yield test_client


def test_server_health_check(client):
    """测试后端健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.2.0"


def test_server_crud_and_universal_run(client):
    """测试企业级多租户 CRUD 与通用评测运行接口"""
    unauthenticated = client.get("/api/v1/auth/me")
    assert unauthenticated.status_code == 401

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "engineer@example.com",
            "name": "测试工程师",
            "password": "a-long-test-password",
        },
    )
    assert registration.status_code == 201
    token = registration.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. 验证登录身份与私有工作区
    auth_resp = client.get("/api/v1/auth/me", headers=headers)
    assert auth_resp.status_code == 200
    auth_data = auth_resp.json()
    assert auth_data["user"]["email"] == "engineer@example.com"
    workspace_id = auth_data["workspaces"][0]["id"]

    # 2. 验证该工作区的 Agent 与创建接口
    agents_resp = client.get(f"/api/v1/agents?workspace_id={workspace_id}", headers=headers)
    assert agents_resp.status_code == 200
    agents = agents_resp.json()
    assert len(agents) == 1
    agent_id = agents[0]["id"]
    update_agent = client.put(
        f"/api/v1/agents/{agent_id}",
        headers=headers,
        json={"description": "updated description"},
    )
    assert update_agent.status_code == 200

    # 3. 验证数据集、用例编辑与授权
    datasets_resp = client.get(f"/api/v1/datasets?workspace_id={workspace_id}", headers=headers)
    assert datasets_resp.status_code == 200
    datasets = datasets_resp.json()
    assert len(datasets) == 1

    ds_id = datasets[0]["id"]
    detail_resp = client.get(f"/api/v1/datasets/{ds_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert len(detail_data["cases"]) == 1
    case_id = detail_data["cases"][0]["id"]
    updated_case = client.put(
        f"/api/v1/cases/{case_id}",
        headers=headers,
        json={"description": "updated case"},
    )
    assert updated_case.status_code == 200
    assert client.get("/api/v1/agents", headers=headers).status_code == 404

    # 4. 触发通用评测运行 (Universal Run)
    run_resp = client.post(
        "/api/v1/evaluations/universal-run",
        headers=headers,
        json={
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "dataset_id": ds_id,
        },
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["status"] == "completed"
    assert run_data["summary"]["score"] == 1.0
    assert len(run_data["case_results"]) >= 1
    assert run_data["summary"]["repetitions"] == 1
    assert run_data["snapshot_hash"]

    repeated_resp = client.post(
        "/api/v1/evaluations/universal-run",
        headers=headers,
        json={
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "dataset_id": ds_id,
            "repetitions": 3,
        },
    )
    assert repeated_resp.status_code == 200
    repeated = repeated_resp.json()
    assert repeated["status"] == "completed"
    assert repeated["summary"]["repetitions"] == 3
    assert len(repeated["runs"]) == 3
    assert repeated["summary"]["unique_cases"] == 1
    assert repeated["summary"]["score_statistics"]["sample_stddev"] is not None
    experiment_detail = client.get(
        f"/api/v1/evaluations/experiments/{repeated['experiment_id']}",
        headers=headers,
    )
    assert experiment_detail.status_code == 200
    assert len(experiment_detail.json()["runs"]) == 3
    assert experiment_detail.json()["snapshot_hash"] == repeated["snapshot_hash"]
    assert (
        client.get(
            f"/api/v1/evaluations/experiments?workspace_id={workspace_id}",
            headers=headers,
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/evaluations/universal-run",
            headers=headers,
            json={
                "workspace_id": workspace_id,
                "agent_id": agent_id,
                "dataset_id": ds_id,
                "repetitions": 0,
            },
        ).status_code
        == 422
    )

    # 5. 验证运行历史持久化
    history_resp = client.get(
        f"/api/v1/evaluations/runs?workspace_id={workspace_id}", headers=headers
    )
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) >= 1
    assert history[0]["id"] == repeated["runs"][-1]["run_id"]
    assert run_data["run_id"] in [item["id"] for item in history]

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "engineer@example.com", "password": "a-long-test-password"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["id"] == auth_data["user"]["id"]
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": "engineer@example.com", "password": "wrong-password-long"},
        ).status_code
        == 401
    )


def test_server_list_benchmarks(client):
    """测试获取预置基准场景库列表"""
    response = client.get("/api/v1/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    benchmark_ids = [item["id"] for item in data]
    assert "ecommerce_refund" in benchmark_ids
    assert "code_security_refactor" in benchmark_ids
    assert "mas_dev_team" in benchmark_ids
    assert "ant_financial_sop" in benchmark_ids


def test_server_run_and_get_evaluation(client):
    """测试通过 API 触发完整评测运行并获取最新结果"""
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "compat@example.com",
            "name": "兼容测试用户",
            "password": "a-long-compat-password",
        },
    )
    assert registration.status_code == 201
    headers = {"Authorization": f"Bearer {registration.json()['token']}"}

    # 1. 触发运行
    run_resp = client.post(
        "/api/v1/evaluations/run",
        headers=headers,
        json={"benchmark_id": "ecommerce_refund"},
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["status"] == "completed"
    result = run_data["result"]
    assert result["is_passed"] is True
    assert result["world_state_passed"] is True

    # 2. 获取最新裁决报告
    latest_resp = client.get("/api/v1/evaluations/latest", headers=headers)
    assert latest_resp.status_code == 200
    latest_data = latest_resp.json()
    assert latest_data["status"] == "completed"
    assert "case_01" in latest_data["result"]["task_id"]
