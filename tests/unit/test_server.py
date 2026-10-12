import pytest
from agent_test_hub_server import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    return TestClient(app)


def test_server_health_check(client):
    """测试后端健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.2.0"


def test_server_crud_and_universal_run(client):
    """测试企业级多租户 CRUD 与通用评测运行接口"""
    # 1. 验证获取当前用户与工作区
    auth_resp = client.get("/api/v1/auth/me")
    assert auth_resp.status_code == 200
    auth_data = auth_resp.json()
    assert auth_data["user"] is not None
    assert len(auth_data["workspaces"]) >= 1

    # 2. 验证获取已注册智能体列表
    agents_resp = client.get("/api/v1/agents")
    assert agents_resp.status_code == 200
    agents = agents_resp.json()
    assert len(agents) >= 2
    agent_ids = [a["id"] for a in agents]
    assert "agent_ecommerce_assistant" in agent_ids

    # 3. 验证获取通用数据集列表与详情
    datasets_resp = client.get("/api/v1/datasets")
    assert datasets_resp.status_code == 200
    datasets = datasets_resp.json()
    assert len(datasets) >= 1

    ds_id = datasets[0]["id"]
    detail_resp = client.get(f"/api/v1/datasets/{ds_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert len(detail_data["cases"]) >= 1

    # 4. 触发通用评测运行 (Universal Run)
    run_resp = client.post(
        "/api/v1/evaluations/universal-run",
        json={
            "workspace_id": "ws_primary",
            "agent_id": "agent_ecommerce_assistant",
            "dataset_id": ds_id,
        },
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["status"] == "completed"
    assert run_data["summary"]["score"] == 1.0
    assert len(run_data["case_results"]) >= 1

    # 5. 验证运行历史持久化
    history_resp = client.get("/api/v1/evaluations/runs")
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) >= 1
    assert history[0]["id"] == run_data["run_id"]


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
    # 1. 触发运行
    run_resp = client.post("/api/v1/evaluations/run", json={"benchmark_id": "ecommerce_refund"})
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["status"] == "completed"
    result = run_data["result"]
    assert result["is_passed"] is True
    assert result["world_state_passed"] is True

    # 2. 获取最新裁决报告
    latest_resp = client.get("/api/v1/evaluations/latest")
    assert latest_resp.status_code == 200
    latest_data = latest_resp.json()
    assert latest_data["status"] == "completed"
    assert "case_01" in latest_data["result"]["task_id"]
