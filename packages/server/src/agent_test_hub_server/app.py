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

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_LATEST_RESULT: TaskEvaluationResult | None = None
_LATEST_BATCH_RESPONSE: dict[str, Any] | None = None
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
    case_id: str | None = None
    target_agent: TargetAgentConfig = Field(default_factory=TargetAgentConfig)


class CreateBenchmarkRequest(BaseModel):
    benchmark_id: str
    yaml_content: str


def _get_yaml_path(benchmark_id: str) -> str:
    yaml_map = {
        "ecommerce_refund": "benchmarks/ecommerce_refund/refund_benchmark.yaml",
        "code_security_refactor": "benchmarks/code_security_refactor/code_security_benchmark.yaml",
        "mas_dev_team": "benchmarks/mas_dev_team/mas_collaboration_benchmark.yaml",
        "ant_financial_sop": "benchmarks/ant_financial_sop/financial_sop_benchmark.yaml",
    }
    if benchmark_id in yaml_map:
        return yaml_map[benchmark_id]
    custom_path = pathlib.Path("benchmarks") / benchmark_id / f"{benchmark_id}.yaml"
    if custom_path.exists():
        return str(custom_path)
    return "benchmarks/ecommerce_refund/refund_benchmark.yaml"


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
                        test_cases = cfg.get("test_cases", [])
                        results.append(
                            {
                                "id": b_dir.name,
                                "suite_name": cfg["suite_name"],
                                "task_id": task.task_id,
                                "title": task.title,
                                "category": task.category,
                                "total_cases": len(test_cases),
                                "rubrics_count": len(cfg["rubrics"]),
                            }
                        )
                    except Exception:
                        pass
    return results


@app.get("/api/v1/benchmarks/{benchmark_id}")
def get_benchmark_detail(benchmark_id: str) -> dict[str, Any]:
    """获取指定基准场景的详细测试用例数据集"""
    yaml_path = _get_yaml_path(benchmark_id)
    cfg = DeclarativeYAMLLoader.load_from_file(yaml_path)

    cases_info = []
    for c in cfg.get("test_cases", []):
        cases_info.append(
            {
                "id": c["id"],
                "title": c["title"],
                "category": c["category"],
                "description": c["description"],
                "prompt": c["prompt"],
                "rubrics_count": len(c.get("rubrics", [])),
                "rubrics": [r.model_dump() for r in c.get("rubrics", [])],
                "expected_world_states": [w.model_dump() for w in c["task"].expected_world_states],
            }
        )

    return {
        "id": benchmark_id,
        "suite_name": cfg["suite_name"],
        "total_cases": len(cases_info),
        "test_cases": cases_info,
    }


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
    """触发评测运行 (支持单用例调试或全量用例矩阵批量运行)"""
    global _LATEST_RESULT, _LATEST_BATCH_RESPONSE

    yaml_path = _get_yaml_path(req.benchmark_id)
    config = DeclarativeYAMLLoader.load_from_file(yaml_path)

    # 确定要执行的用例列表
    cases_to_run = config.get("test_cases", [])
    if req.case_id:
        cases_to_run = [c for c in cases_to_run if c["id"] == req.case_id]
        if not cases_to_run:
            cases_to_run = config.get("test_cases", [])[:1]

    case_results = []
    target_cfg = req.target_agent

    for case_item in cases_to_run:
        task = case_item["task"]
        rubrics = case_item["rubrics"]
        ex_cfg = case_item["examiner_config"]

        # 每个用例使用干净独立的沙盒与初始数据
        sandbox = SQLiteSandbox()
        sandbox.initialize(config["init_sql"])

        examiner = UserSimulator(
            persona=ex_cfg.get("persona", "买家"),
            initial_message=task.initial_user_prompt,
            hidden_goals=ex_cfg.get("hidden_goals", []),
            clarification_triggers=ex_cfg.get("clarification_triggers", {}),
            max_turns=task.constraints.max_turns,
        )

        # 判定被测 Agent 逻辑
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
            # 智能自适应测试桩 (根据用例特征做出符合真实 Agent 的决策)
            def adaptive_agent(prompt: str, trace: ExecutionTrace):
                # 1. 越权/删库/远程执行攻击检查
                if any(
                    k in prompt for k in ["DROP TABLE", "SYSTEM_OVERRIDE", "TEST_HARNESS", "curl "]
                ):
                    return {
                        "response": "系统拒绝执行非法删库越权或未授权 Shell 指令，操作已拦截并告警。",
                        "tool_calls": [],
                    }
                # 2. 超额退款检查
                if "1000" in prompt:
                    return {
                        "response": "抱歉，退款金额不能超过订单实付金额上限，无法为您办理超额退款。",
                        "tool_calls": [],
                    }
                # 3. 拒绝提供凭证检查
                if "不要上传" in prompt and "退" in prompt:
                    return {
                        "response": "根据平台风控政策，缺少开箱破损凭证无法直接办理退款，请上传凭证以便核实处理。",
                        "tool_calls": [],
                    }
                # 4. 金融拒绝跳步 KYC 检查
                if "不要搞什么人脸识别" in prompt or "直接给我把" in prompt:
                    return {
                        "response": "根据金融监管合规要求，前置实名 KYC 认证属于刚性要求，无法直接放款。",
                        "tool_calls": [],
                    }
                # 5. 电商退款需首轮索取凭证
                if "破损" in prompt and "照片" not in prompt and "凭证" not in prompt:
                    return {
                        "response": "非常抱歉给您带来不便，请问您是否有开箱破损凭证？提供后我立刻为您办理退款！",
                        "tool_calls": [],
                    }
                # 6. 金融首轮索取认证
                if "急用钱" in prompt and "认证" not in prompt:
                    return {
                        "response": "申请周转金需要前置完成人脸实名与征信授权，请在手机银行确认后再行推进。",
                        "tool_calls": [],
                    }

                # 7. 正常流/已提供凭证/代码审查/架构方案通过: 真实落盘修改沙盒数据库
                tool_calls = []
                for exp in task.expected_world_states:
                    table = exp.target_identifier
                    cond_key = list(exp.condition.keys())[0] if exp.condition else "id"
                    cond_val = list(exp.condition.values())[0] if exp.condition else "1"
                    set_clauses = [f"{k} = '{v}'" for k, v in exp.expected_values.items()]
                    sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {cond_key} = '{cond_val}';"
                    tool_calls.append({"name": "db_execute", "arguments": {"sql": sql}})

                return {
                    "response": "已核验通过并按照业务规约成功完成操作与状态更新！",
                    "tool_calls": tool_calls,
                }

            testee_fn = adaptive_agent

        def broadcast_event(evt: TraceEvent) -> None:
            listeners = _ACTIVE_WEBSOCKETS.get(task.task_id, [])
            for ws in listeners:
                try:
                    asyncio.create_task(ws.send_text(evt.model_dump_json()))
                except Exception:
                    pass

        runner = EvaluationRunner(sandbox=sandbox)
        eval_result = runner.run_task(
            task=task,
            examiner=examiner,
            rubrics=rubrics,
            testee_agent_fn=testee_fn,
            event_callback=broadcast_event,
        )

        sandbox.close()

        case_results.append(
            {
                "case_id": task.task_id,
                "title": task.title,
                "category": task.category,
                "prompt": task.initial_user_prompt,
                "result": eval_result.model_dump(),
            }
        )

    # 汇总计算
    passed_count = sum(1 for c in case_results if c["result"]["is_passed"])
    total_count = len(case_results)
    pass_rate = round(passed_count / total_count, 3) if total_count > 0 else 1.0

    _LATEST_RESULT = TaskEvaluationResult(**case_results[0]["result"]) if case_results else None

    batch_response = {
        "status": "completed",
        "benchmark_id": req.benchmark_id,
        "suite_name": config["suite_name"],
        "total_cases": total_count,
        "passed_cases": passed_count,
        "pass_rate": pass_rate,
        "case_results": case_results,
        "result": case_results[0]["result"] if case_results else {},
    }
    _LATEST_BATCH_RESPONSE = batch_response
    return batch_response


@app.get("/api/v1/evaluations/latest")
def get_latest_evaluation() -> dict[str, Any]:
    """获取最新一次评测裁决结果"""
    if _LATEST_BATCH_RESPONSE is not None:
        return _LATEST_BATCH_RESPONSE
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
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if task_id in _ACTIVE_WEBSOCKETS and websocket in _ACTIVE_WEBSOCKETS[task_id]:
            _ACTIVE_WEBSOCKETS[task_id].remove(websocket)
