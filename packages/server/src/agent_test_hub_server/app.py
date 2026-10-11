from __future__ import annotations

import asyncio
import pathlib
from typing import Any

from agent_test_hub.adapters import LiteLLMAgentAdapter
from agent_test_hub.examiners import UserSimulator
from agent_test_hub.runner import EvaluationRunner
from agent_test_hub.schemas import ExecutionTrace, TaskEvaluationResult, TraceEvent
from agent_test_hub_cli.yaml_loader import DeclarativeYAMLLoader
from agent_test_hub_sandbox import SQLiteSandbox
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="AgentTestHub Enterprise Server",
    description="Next-Gen Multi-Agent Collaborative Evaluation Engine API",
    version="0.1.0",
)

# 允许跨域，方便未来的 Next.js 15 (如 http://localhost:3005) 随时接入
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存缓存最近一次评测结果与 WebSocket 连接池
_LATEST_RESULT: TaskEvaluationResult | None = None
_ACTIVE_WEBSOCKETS: dict[str, list[WebSocket]] = {}


class TargetAgentConfig(BaseModel):
    """被测 Agent 来源与连接配置"""

    agent_type: str = Field(default="mock", description="类型: mock / litellm / webhook")
    model_name: str = Field(
        default="gpt-4o", description="模型名称 (gpt-4o, claude-3-5-sonnet, deepseek-chat 等)"
    )
    api_key: str | None = Field(default=None, description="大模型 API Key")
    api_base: str | None = Field(default=None, description="自定义 API Base URL (如本地 Ollama)")
    webhook_url: str | None = Field(default=None, description="外部自定义 HTTP Agent Webhook")


class RunBenchmarkRequest(BaseModel):
    benchmark_id: str = "ecommerce_refund"
    target_agent: TargetAgentConfig = Field(default_factory=TargetAgentConfig)


class CreateBenchmarkRequest(BaseModel):
    benchmark_id: str
    yaml_content: str


@app.get("/health")
def health_check() -> dict[str, str]:
    """系统健康检查端点"""
    return {"status": "ok", "service": "AgentTestHub Engine", "version": "0.1.0"}


@app.get("/api/v1/benchmarks")
def list_benchmarks() -> list[dict[str, Any]]:
    """列出系统预置的所有基准场景列表"""
    benchmarks_dir = pathlib.Path("benchmarks")
    results = []
    if benchmarks_dir.exists():
        for b_dir in benchmarks_dir.iterdir():
            if b_dir.is_dir():
                yaml_files = list(b_dir.glob("*.yaml"))
                if yaml_files:
                    try:
                        cfg = DeclarativeYAMLLoader.load_from_file(yaml_files[0])
                        task = cfg["task"]
                        results.append(
                            {
                                "id": b_dir.name,
                                "suite_name": cfg["suite_name"],
                                "task_id": task.task_id,
                                "title": task.title,
                                "category": task.category,
                                "rubrics_count": len(cfg["rubrics"]),
                            }
                        )
                    except Exception:
                        pass
    return results


@app.post("/api/v1/benchmarks")
def create_benchmark(req: CreateBenchmarkRequest) -> dict[str, Any]:
    """保存或新增自定义基准场景到 benchmarks/ 资产库"""
    target_dir = pathlib.Path("benchmarks") / req.benchmark_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / f"{req.benchmark_id}.yaml"
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(req.yaml_content)

    return {
        "status": "success",
        "benchmark_id": req.benchmark_id,
        "saved_path": str(target_file),
    }


@app.post("/api/v1/evaluations/run")
async def run_evaluation(req: RunBenchmarkRequest) -> dict[str, Any]:
    """触发评测运行并保存结果"""
    global _LATEST_RESULT

    yaml_map = {
        "ecommerce_refund": "benchmarks/ecommerce_refund/refund_benchmark.yaml",
        "code_security_refactor": "benchmarks/code_security_refactor/code_security_benchmark.yaml",
        "mas_dev_team": "benchmarks/mas_dev_team/mas_collaboration_benchmark.yaml",
        "ant_financial_sop": "benchmarks/ant_financial_sop/financial_sop_benchmark.yaml",
    }
    yaml_path = yaml_map.get(req.benchmark_id, "benchmarks/ecommerce_refund/refund_benchmark.yaml")
    config = DeclarativeYAMLLoader.load_from_file(yaml_path)

    task = config["task"]
    rubrics = config["rubrics"]
    ex_cfg = config["examiner_config"]

    sandbox = SQLiteSandbox()
    sandbox.initialize(config["init_sql"])

    examiner = UserSimulator(
        persona=ex_cfg.get("persona", "买家"),
        initial_message=task.initial_user_prompt,
        hidden_goals=ex_cfg.get("hidden_goals", []),
        clarification_triggers=ex_cfg.get("clarification_triggers", {}),
        max_turns=task.constraints.max_turns,
    )

    # 判定被测 Agent 类型
    target_cfg = req.target_agent
    if target_cfg.agent_type == "litellm":
        adapter = LiteLLMAgentAdapter(
            model=target_cfg.model_name,
            api_key=target_cfg.api_key,
            api_base=target_cfg.api_base,
            tools=task.available_tools,
        )
        testee_fn = adapter.step
    elif target_cfg.agent_type == "webhook" and target_cfg.webhook_url:
        import httpx

        def webhook_agent(prompt: str, trace: ExecutionTrace):
            try:
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post(
                        target_cfg.webhook_url,
                        json={
                            "prompt": prompt,
                            "task_id": task.task_id,
                            "tools": [t.model_dump() for t in task.available_tools],
                        },
                    )
                    return resp.json()
            except Exception as e:
                return {"response": f"Webhook 调用异常: {e!s}", "tool_calls": []}

        testee_fn = webhook_agent
    else:
        # 默认自适应模拟被测 Agent
        def support_agent(prompt: str, trace: ExecutionTrace):
            tool_calls = []
            for exp in task.expected_world_states:
                table = exp.target_identifier
                cond_key = list(exp.condition.keys())[0] if exp.condition else "id"
                cond_val = list(exp.condition.values())[0] if exp.condition else "1"
                set_clauses = [f"{k} = '{v}'" for k, v in exp.expected_values.items()]
                sql = (
                    f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {cond_key} = '{cond_val}';"
                )
                tool_calls.append({"name": "db_execute", "arguments": {"sql": sql}})

            return {
                "response": "已根据业务诉求完成相关操作与状态更新。",
                "tool_calls": tool_calls,
            }

        testee_fn = support_agent

    # 事件推流回调函数
    def broadcast_event(evt: TraceEvent) -> None:
        listeners = _ACTIVE_WEBSOCKETS.get(task.task_id, [])
        for ws in listeners:
            try:
                asyncio.create_task(ws.send_text(evt.model_dump_json()))
            except Exception:
                pass

    runner = EvaluationRunner(sandbox=sandbox)
    result = runner.run_task(
        task=task,
        examiner=examiner,
        rubrics=rubrics,
        testee_agent_fn=testee_fn,
        event_callback=broadcast_event,
    )

    _LATEST_RESULT = result
    sandbox.close()

    return {
        "status": "completed",
        "result": result.model_dump(),
    }


@app.get("/api/v1/evaluations/latest")
def get_latest_evaluation() -> dict[str, Any]:
    """获取最新一次评测裁决结果"""
    if _LATEST_RESULT is None:
        return {"status": "none", "message": "No evaluation has been run yet"}
    return {"status": "completed", "result": _LATEST_RESULT.model_dump()}


@app.websocket("/api/v1/arena/ws/{task_id}")
async def arena_websocket(websocket: WebSocket, task_id: str):
    """前端 Web 竞技场实时拓扑对战推流通道"""
    await websocket.accept()
    if task_id not in _ACTIVE_WEBSOCKETS:
        _ACTIVE_WEBSOCKETS[task_id] = []
    _ACTIVE_WEBSOCKETS[task_id].append(websocket)

    try:
        while True:
            # 保持心跳连接
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if task_id in _ACTIVE_WEBSOCKETS and websocket in _ACTIVE_WEBSOCKETS[task_id]:
            _ACTIVE_WEBSOCKETS[task_id].remove(websocket)
