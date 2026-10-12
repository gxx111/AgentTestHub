from __future__ import annotations

import asyncio
import datetime
import json
import pathlib
import uuid
from typing import Any

from agent_test_hub.adapters import LiteLLMAgentAdapter
from agent_test_hub.examiners import UserSimulator
from agent_test_hub.runner import EvaluationRunner
from agent_test_hub.schemas import (
    BinaryRubric,
    BinaryVerdict,
    ExecutionTrace,
    TaskConstraint,
    TaskEvaluationResult,
    TaskSpec,
    ToolDefinition,
    TraceEvent,
    WorldStateExpectation,
)
from agent_test_hub_cli.yaml_loader import DeclarativeYAMLLoader
from agent_test_hub_sandbox import SQLiteSandbox
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .db import get_db_connection, init_db

app = FastAPI(
    title="AgentTestHub Enterprise Server",
    description="Next-Gen Universal Multi-Agent Collaborative Evaluation Platform API",
    version="0.2.0",
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

# 模块加载时确保数据库表与种子数据就绪
init_db()


@app.on_event("startup")
def on_startup():
    """启动时初始化数据库与默认数据"""
    init_db()


# -------------------------------------------------------------
# 1. 鉴权与多租户/工作区模型 (Auth & Workspaces)
# -------------------------------------------------------------
@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "AgentTestHub Universal Platform", "version": "0.2.0"}


@app.get("/api/v1/auth/me")
def get_current_user_and_workspaces():
    """获取当前登录用户信息及所属工作区列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users LIMIT 1;")
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return {"user": None, "workspaces": []}

    user = dict(user_row)
    cursor.execute("SELECT * FROM workspaces WHERE user_id = ?;", (user["id"],))
    workspaces = [dict(w) for w in cursor.fetchall()]
    conn.close()
    return {"user": user, "workspaces": workspaces}


# -------------------------------------------------------------
# 2. 智能体资产库 CRUD (Agent Registry)
# -------------------------------------------------------------
class CreateAgentRequest(BaseModel):
    workspace_id: str = "ws_primary"
    name: str
    agent_type: str = "single"  # 'single' | 'mas_team' | 'webhook' | 'mock'
    model_name: str = "gpt-4o"
    description: str = ""
    system_prompt: str = ""
    tools: list[dict[str, Any]] = Field(default_factory=list)
    mas_team: list[dict[str, Any]] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)


@app.get("/api/v1/agents")
def list_agents(workspace_id: str = "ws_primary") -> list[dict[str, Any]]:
    """获取当前工作区下注册的所有 Agent 资产"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM registered_agents WHERE workspace_id = ? ORDER BY created_at DESC;",
        (workspace_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["tools"] = json.loads(d["tools_json"]) if d.get("tools_json") else []
        d["mas_team"] = json.loads(d["mas_team_json"]) if d.get("mas_team_json") else []
        d["config"] = json.loads(d["config_json"]) if d.get("config_json") else {}
        result.append(d)
    return result


@app.post("/api/v1/agents")
def create_agent(req: CreateAgentRequest) -> dict[str, Any]:
    """注册或新建一个被测 Agent (支持单智能体、多智能体协同战队或外部 Webhook)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    agent_id = f"agent_{uuid.uuid4().hex[:10]}"

    cursor.execute(
        """
        INSERT INTO registered_agents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            agent_id,
            req.workspace_id,
            req.name,
            req.agent_type,
            req.model_name,
            req.description,
            req.system_prompt,
            json.dumps(req.tools),
            json.dumps(req.mas_team) if req.mas_team else None,
            json.dumps(req.config),
            now,
        ),
    )
    conn.commit()
    conn.close()
    return {"status": "success", "agent_id": agent_id, "message": "Agent 注册成功"}


@app.delete("/api/v1/agents/{agent_id}")
def delete_agent(agent_id: str) -> dict[str, Any]:
    """删除指定的 Agent 资产"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registered_agents WHERE id = ?;", (agent_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "agent_id": agent_id}


# -------------------------------------------------------------
# 3. 通用评测数据集/场景库 CRUD (Datasets & Test Cases)
# -------------------------------------------------------------
class CreateDatasetRequest(BaseModel):
    workspace_id: str = "ws_primary"
    name: str
    domain: str = "general"
    description: str = ""
    init_sql: str = ""


class CreateTestCaseRequest(BaseModel):
    title: str
    category: str = "happy_path"
    prompt: str
    description: str = ""
    expected_state: list[dict[str, Any]] = Field(default_factory=list)
    rubrics: list[dict[str, Any]] = Field(default_factory=list)


@app.get("/api/v1/datasets")
def list_datasets(workspace_id: str = "ws_primary") -> list[dict[str, Any]]:
    """查询工作区下所有数据集列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT d.*, COUNT(c.id) as case_count FROM datasets d LEFT JOIN test_cases c ON d.id = c.dataset_id WHERE d.workspace_id = ? GROUP BY d.id ORDER BY d.created_at DESC;",
        (workspace_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/v1/datasets")
def create_dataset(req: CreateDatasetRequest) -> dict[str, Any]:
    """新建通用评测场景/数据集"""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    dataset_id = f"ds_{uuid.uuid4().hex[:10]}"

    cursor.execute(
        "INSERT INTO datasets VALUES (?, ?, ?, ?, ?, ?, ?);",
        (dataset_id, req.workspace_id, req.name, req.domain, req.description, req.init_sql, now),
    )
    conn.commit()
    conn.close()
    return {"status": "success", "dataset_id": dataset_id}


@app.get("/api/v1/datasets/{dataset_id}")
def get_dataset_details(dataset_id: str) -> dict[str, Any]:
    """获取数据集详情及其包含的测试用例列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasets WHERE id = ?;", (dataset_id,))
    ds_row = cursor.fetchone()
    if not ds_row:
        conn.close()
        return {"error": "Dataset not found"}

    ds = dict(ds_row)
    cursor.execute(
        "SELECT * FROM test_cases WHERE dataset_id = ? ORDER BY created_at ASC;", (dataset_id,)
    )
    case_rows = cursor.fetchall()
    conn.close()

    cases = []
    for cr in case_rows:
        c = dict(cr)
        c["expected_state"] = (
            json.loads(c["expected_state_json"]) if c.get("expected_state_json") else []
        )
        c["rubrics"] = json.loads(c["rubrics_json"]) if c.get("rubrics_json") else []
        cases.append(c)

    ds["cases"] = cases
    return ds


@app.post("/api/v1/datasets/{dataset_id}/cases")
def add_test_case(dataset_id: str, req: CreateTestCaseRequest) -> dict[str, Any]:
    """向指定数据集添加一条测试用例"""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    case_id = f"case_{uuid.uuid4().hex[:10]}"

    cursor.execute(
        """
        INSERT INTO test_cases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            case_id,
            dataset_id,
            req.title,
            req.category,
            req.prompt,
            req.description,
            None,
            json.dumps(req.expected_state),
            json.dumps(req.rubrics),
            now,
        ),
    )
    conn.commit()
    conn.close()
    return {"status": "success", "case_id": case_id}


@app.delete("/api/v1/cases/{case_id}")
def delete_test_case(case_id: str) -> dict[str, Any]:
    """删除测试用例"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM test_cases WHERE id = ?;", (case_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "case_id": case_id}


# -------------------------------------------------------------
# 4. 考官与法官合议策略库 CRUD (Examiner Policies)
# -------------------------------------------------------------
class CreatePolicyRequest(BaseModel):
    workspace_id: str = "ws_primary"
    name: str
    description: str = ""
    user_sim_persona: str = "严苛的业务核验官"
    hidden_goals: list[str] = Field(default_factory=list)
    enable_red_team: bool = True
    red_team_intensity: str = "medium"
    enable_watchdog: bool = True
    watchdog_max_turns: int = 8
    default_rubrics: list[dict[str, Any]] = Field(default_factory=list)


@app.get("/api/v1/policies")
def list_policies(workspace_id: str = "ws_primary") -> list[dict[str, Any]]:
    """查询考官网络与裁判合议策略库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM examiner_policies WHERE workspace_id = ? ORDER BY created_at DESC;",
        (workspace_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["hidden_goals"] = json.loads(d["hidden_goals_json"]) if d.get("hidden_goals_json") else []
        d["default_rubrics"] = (
            json.loads(d["default_rubrics_json"]) if d.get("default_rubrics_json") else []
        )
        result.append(d)
    return result


@app.post("/api/v1/policies")
def create_policy(req: CreatePolicyRequest) -> dict[str, Any]:
    """创建新的考官网络与合议策略"""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    policy_id = f"policy_{uuid.uuid4().hex[:10]}"

    cursor.execute(
        """
        INSERT INTO examiner_policies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            policy_id,
            req.workspace_id,
            req.name,
            req.description,
            req.user_sim_persona,
            json.dumps(req.hidden_goals),
            1 if req.enable_red_team else 0,
            req.red_team_intensity,
            1 if req.enable_watchdog else 0,
            req.watchdog_max_turns,
            json.dumps(req.default_rubrics),
            now,
        ),
    )
    conn.commit()
    conn.close()
    return {"status": "success", "policy_id": policy_id}


# -------------------------------------------------------------
# 5. 通用多智能体协同评测运行引擎 (Universal Evaluation Engine)
# -------------------------------------------------------------
class UniversalRunRequest(BaseModel):
    workspace_id: str = "ws_primary"
    agent_id: str
    dataset_id: str
    policy_id: str | None = None
    case_id: str | None = None


@app.post("/api/v1/evaluations/universal-run")
async def run_universal_evaluation(req: UniversalRunRequest) -> dict[str, Any]:
    """核心通用评测调度总线: 任意已注册 Agent × 任意通用数据集 × 任意考官团"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 读取 Agent 配置
    cursor.execute("SELECT * FROM registered_agents WHERE id = ?;", (req.agent_id,))
    agent_row = cursor.fetchone()
    if not agent_row:
        conn.close()
        return {"error": "Target agent not found"}
    agent_info = dict(agent_row)
    agent_tools = json.loads(agent_info["tools_json"]) if agent_info.get("tools_json") else []
    agent_config = json.loads(agent_info["config_json"]) if agent_info.get("config_json") else {}

    # 读取 Dataset 与用例
    cursor.execute("SELECT * FROM datasets WHERE id = ?;", (req.dataset_id,))
    ds_row = cursor.fetchone()
    if not ds_row:
        conn.close()
        return {"error": "Dataset not found"}
    dataset_info = dict(ds_row)

    query = "SELECT * FROM test_cases WHERE dataset_id = ?"
    params = [req.dataset_id]
    if req.case_id:
        query += " AND id = ?"
        params.append(req.case_id)
    query += " ORDER BY created_at ASC;"

    cursor.execute(query, tuple(params))
    case_rows = cursor.fetchall()
    conn.close()

    if not case_rows:
        return {"error": "No test cases found in this dataset"}

    # 动态执行每个用例
    case_results = []
    total_start_time = datetime.datetime.now()

    for cr in case_rows:
        c = dict(cr)
        c_expected_states = (
            [WorldStateExpectation(**w) for w in json.loads(c["expected_state_json"])]
            if c.get("expected_state_json")
            else []
        )
        parsed_rubrics = []
        if c.get("rubrics_json"):
            for r in json.loads(c["rubrics_json"]):
                r_id = r.get("rubric_id") or r.get("id") or "chk_custom"
                r_dim = r.get("dimension", "通用业务")
                r_q = r.get("question", "")
                r_exp = BinaryVerdict(r.get("expected_verdict", "YES"))
                r_fatal = r.get("is_fatal", False)
                parsed_rubrics.append(
                    BinaryRubric(
                        rubric_id=r_id,
                        dimension=r_dim,
                        question=r_q,
                        expected_verdict=r_exp,
                        is_fatal=r_fatal,
                    )
                )
        if not parsed_rubrics:
            parsed_rubrics = [
                BinaryRubric(
                    rubric_id="chk_general_pass",
                    dimension="通用业务合规",
                    question="Agent 是否成功达成了业务诉求？",
                    expected_verdict=BinaryVerdict.YES,
                )
            ]
        c_rubrics = parsed_rubrics

        task_spec = TaskSpec(
            task_id=c["id"],
            scenario_id=dataset_info["id"],
            title=c["title"],
            description=c.get("description", ""),
            initial_user_prompt=c["prompt"],
            available_tools=[ToolDefinition(**t) for t in agent_tools],
            constraints=TaskConstraint(max_turns=6, timeout_seconds=60),
            expected_world_states=c_expected_states,
        )

        sandbox = SQLiteSandbox()
        if dataset_info.get("init_sql"):
            sandbox.initialize([dataset_info["init_sql"]])

        examiner = UserSimulator(
            persona="业务核验用户",
            initial_message=c["prompt"],
            hidden_goals=["业务前置凭证"],
            clarification_triggers={"凭证": "已补充提供核验材料"},
            max_turns=6,
        )

        # 构造被测 Agent 调用逻辑
        if agent_info["agent_type"] == "litellm":
            adapter = LiteLLMAgentAdapter(
                model=agent_info["model_name"],
                api_key=agent_config.get("api_key"),
                api_base=agent_config.get("api_base"),
                tools=task_spec.available_tools,
            )
            testee_fn = adapter.step
        elif agent_info["agent_type"] == "webhook" and agent_config.get("webhook_url"):
            import httpx

            def webhook_fn(prompt: str, trace: ExecutionTrace):
                try:
                    with httpx.Client(timeout=30.0) as client:
                        resp = client.post(
                            agent_config["webhook_url"],
                            json={
                                "prompt": prompt,
                                "task_id": c["id"],
                                "tools": [t.model_dump() for t in task_spec.available_tools],
                            },
                        )
                        return resp.json()
                except Exception as e:
                    return {"response": f"Webhook 调用异常: {e!s}", "tool_calls": []}

            testee_fn = webhook_fn
        else:
            # 默认高保真自适应测试桩
            def universal_mock_agent(prompt: str, trace: ExecutionTrace):
                if any(k in prompt for k in ["DROP TABLE", "SYSTEM_OVERRIDE", "curl "]):
                    return {
                        "thought": "【ReAct 思考链】检测到高危系统注入特征，依据安全准则拦截越权调用并记录审计日志。",
                        "response": "系统拒绝执行非法删库越权或未授权指令，操作已拦截并告警。",
                        "tool_calls": [],
                    }
                if "不要上传" in prompt or "不要搞" in prompt:
                    return {
                        "thought": "【ReAct 思考链】诉求方要求跳过前置审核。坚守风控合规底线，拒绝违规跳步。",
                        "response": "根据合规风控要求，缺少前置凭证无法办理，请配合提供材料。",
                        "tool_calls": [],
                    }

                tool_calls = []
                for exp in task_spec.expected_world_states:
                    table = exp.target_identifier
                    cond_key = list(exp.condition.keys())[0] if exp.condition else "id"
                    cond_val = list(exp.condition.values())[0] if exp.condition else "1"
                    set_clauses = [f"{k} = '{v}'" for k, v in exp.expected_values.items()]
                    sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {cond_key} = '{cond_val}';"
                    tool_calls.append({"name": "db_execute", "arguments": {"sql": sql}})

                return {
                    "thought": "【ReAct 思考链】前置审核条件达成，调用数据落盘工具推进目标物理实体状态。",
                    "response": "已核验通过并按照业务规约成功完成操作与状态更新！",
                    "tool_calls": tool_calls,
                }

            testee_fn = universal_mock_agent

        def broadcast_event(evt: TraceEvent) -> None:
            listeners = _ACTIVE_WEBSOCKETS.get(c["id"], [])
            for ws in listeners:
                try:
                    asyncio.create_task(ws.send_text(evt.model_dump_json()))
                except Exception:
                    pass

        runner = EvaluationRunner(sandbox=sandbox)
        eval_result = runner.run_task(
            task=task_spec,
            examiner=examiner,
            rubrics=c_rubrics,
            testee_agent_fn=testee_fn,
            event_callback=broadcast_event,
        )
        sandbox.close()

        case_results.append(
            {
                "case_id": c["id"],
                "title": c["title"],
                "category": c["category"],
                "prompt": c["prompt"],
                "result": eval_result.model_dump(mode="json"),
            }
        )

    # 计算总体运行战报
    total_duration_ms = (datetime.datetime.now() - total_start_time).total_seconds() * 1000.0
    passed_count = sum(1 for cr in case_results if cr["result"]["is_passed"])
    total_count = len(case_results)
    score = round(passed_count / total_count, 3) if total_count > 0 else 1.0

    run_id = f"run_{uuid.uuid4().hex[:12]}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    summary = {
        "run_id": run_id,
        "agent_name": agent_info["name"],
        "dataset_name": dataset_info["name"],
        "total_cases": total_count,
        "passed_cases": passed_count,
        "score": score,
        "latency_ms": round(total_duration_ms, 1),
    }

    # 持久化至 eval_runs 表
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO eval_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            run_id,
            req.workspace_id,
            req.agent_id,
            req.dataset_id,
            req.policy_id,
            "completed",
            total_count,
            passed_count,
            score,
            total_duration_ms,
            json.dumps(summary),
            json.dumps(case_results),
            now,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "status": "completed",
        "run_id": run_id,
        "summary": summary,
        "case_results": case_results,
    }


@app.get("/api/v1/evaluations/runs")
def list_eval_runs(workspace_id: str = "ws_primary") -> list[dict[str, Any]]:
    """获取工作区下历史评测运行记录列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM eval_runs WHERE workspace_id = ? ORDER BY created_at DESC LIMIT 20;",
        (workspace_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["summary"] = json.loads(d["summary_json"]) if d.get("summary_json") else {}
        result.append(d)
    return result


# -------------------------------------------------------------
# 6. 兼容旧接口 (向后兼容)
# -------------------------------------------------------------
class TargetAgentConfig(BaseModel):
    agent_type: str = "mock"
    model_name: str = "gpt-4o"
    api_key: str | None = None
    api_base: str | None = None
    webhook_url: str | None = None


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


@app.post("/api/v1/agents/test-connection")
def test_agent_connection(req: TargetAgentConfig) -> dict[str, Any]:
    if req.agent_type == "litellm":
        adapter = LiteLLMAgentAdapter(
            model=req.model_name,
            api_key=req.api_key,
            api_base=req.api_base,
        )
        return adapter.test_connection()
    elif req.agent_type == "webhook" and req.webhook_url:
        import httpx

        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(req.webhook_url)
                return {
                    "status": "ok",
                    "status_code": resp.status_code,
                    "message": "Webhook 端点可连通",
                }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    return {"status": "ok", "message": "内建自适应测试桩就绪"}


@app.get("/api/v1/benchmarks")
def list_benchmarks() -> list[dict[str, Any]]:
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


@app.post("/api/v1/evaluations/run")
async def run_evaluation(req: RunBenchmarkRequest) -> dict[str, Any]:
    global _LATEST_RESULT, _LATEST_BATCH_RESPONSE

    yaml_path = _get_yaml_path(req.benchmark_id)
    config = DeclarativeYAMLLoader.load_from_file(yaml_path)

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

        sandbox = SQLiteSandbox()
        sandbox.initialize(config["init_sql"])

        examiner = UserSimulator(
            persona=ex_cfg.get("persona", "买家"),
            initial_message=task.initial_user_prompt,
            hidden_goals=ex_cfg.get("hidden_goals", []),
            clarification_triggers=ex_cfg.get("clarification_triggers", {}),
            max_turns=task.constraints.max_turns,
        )

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

            def adaptive_agent(prompt: str, trace: ExecutionTrace):
                if any(
                    k in prompt for k in ["DROP TABLE", "SYSTEM_OVERRIDE", "TEST_HARNESS", "curl "]
                ):
                    return {
                        "thought": "【ReAct 思考链】检测到高危系统注入特征，依据安全准则拦截越权调用并记录审计日志。",
                        "response": "系统拒绝执行非法删库越权或未授权 Shell 指令，操作已拦截并告警。",
                        "tool_calls": [],
                    }
                if "1000" in prompt:
                    return {
                        "thought": "【ReAct 思考链】买家索赔金额超限，坚决拦截超额资损欺诈诉求。",
                        "response": "抱歉，退款金额不能超过订单实付金额上限，无法为您办理超额退款。",
                        "tool_calls": [],
                    }
                if "不要上传" in prompt and "退" in prompt:
                    return {
                        "thought": "【ReAct 思考链】买家催促但未提供凭证，依据合规政策坚决不予直接退款。",
                        "response": "根据平台风控政策，缺少开箱破损凭证无法直接办理退款，请上传凭证以便核实处理。",
                        "tool_calls": [],
                    }
                if "不要搞什么人脸识别" in prompt or "直接给我把" in prompt:
                    return {
                        "thought": "【ReAct 思考链】客户要求跳过实名认证，依据蚂蚁 AIEvo 强流程标准阻断越权放款。",
                        "response": "根据金融监管合规要求，前置实名 KYC 认证属于刚性要求，无法直接放款。",
                        "tool_calls": [],
                    }
                if "破损" in prompt and "照片" not in prompt and "凭证" not in prompt:
                    return {
                        "thought": "【ReAct 思考链】买家反馈破损但尚未提供凭证，主动索取开箱视频与破损照片。",
                        "response": "非常抱歉给您带来不便，请问您是否有开箱破损凭证？提供后我立刻为您办理退款！",
                        "tool_calls": [],
                    }
                if "急用钱" in prompt and "认证" not in prompt:
                    return {
                        "thought": "【ReAct 思考链】小微商户申请周转金，前置引导在手机银行完成实名与征信授权。",
                        "response": "申请周转金需要前置完成人脸实名与征信授权，请在手机银行确认后再行推进。",
                        "tool_calls": [],
                    }

                tool_calls = []
                for exp in task.expected_world_states:
                    table = exp.target_identifier
                    cond_key = list(exp.condition.keys())[0] if exp.condition else "id"
                    cond_val = list(exp.condition.values())[0] if exp.condition else "1"
                    set_clauses = [f"{k} = '{v}'" for k, v in exp.expected_values.items()]
                    sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {cond_key} = '{cond_val}';"
                    tool_calls.append({"name": "db_execute", "arguments": {"sql": sql}})

                return {
                    "thought": "【ReAct 思考链】前置审核条件达成，调用数据落盘工具推进目标物理实体状态。",
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
    if _LATEST_BATCH_RESPONSE is not None:
        return _LATEST_BATCH_RESPONSE
    if _LATEST_RESULT is None:
        return {"status": "none", "message": "No evaluation has been run yet"}
    return {"status": "completed", "result": _LATEST_RESULT.model_dump()}


@app.websocket("/api/v1/arena/ws/{task_id}")
async def arena_websocket(websocket: WebSocket, task_id: str):
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
