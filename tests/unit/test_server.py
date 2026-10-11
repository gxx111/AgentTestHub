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
    assert data["version"] == "0.1.0"


def test_server_list_benchmarks(client):
    """测试获取预置基准场景库列表"""
    response = client.get("/api/v1/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert "ecommerce_refund" in item["id"]
    assert item["rubrics_count"] >= 1


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
    assert latest_data["result"]["task_id"] == "task_refund_broken_package"
