from __future__ import annotations

import datetime
import hashlib
import importlib.metadata
import importlib.util
import inspect
import json
import math
import platform
import random
import statistics
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from agent_test_hub.adapters import LiteLLMAgentAdapter
from agent_test_hub.evaluation_client import EvaluationClient
from agent_test_hub.examiners import UserSimulator
from agent_test_hub.examiners.llm_simulator import (
    CoordinatedExaminer,
    LLMRedTeamAttacker,
    LLMUserSimulator,
)
from agent_test_hub.judges import JudicialCommittee, LLMJudge, LLMModerator
from agent_test_hub.runner import EvaluationRunner
from agent_test_hub.schemas import (
    ActorRole,
    BinaryRubric,
    ExecutionTrace,
    TaskConstraint,
    TaskSpec,
    ToolCallObservation,
    ToolDefinition,
    TraceEvent,
    TraceEventType,
    WorldStateExpectation,
)
from agent_test_hub_sandbox import SQLiteSandbox


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def _secret_key(key: str) -> bool:
    normalized = "".join(char for char in key.lower() if char.isalnum())
    if normalized == "apikeyconfigured":
        return False
    if normalized in (
        "totaltokens",
        "tokensconsumed",
        "inputtokens",
        "outputtokens",
        "completiontokens",
        "prompttokens",
        "maxtokens",
        "tokenbudget",
    ):
        return False
    return any(
        part in normalized
        for part in (
            "apikey",
            "token",
            "secret",
            "password",
            "authorization",
            "credential",
            "cookie",
        )
    )


def sanitize_snapshot(value: Any) -> Any:
    """Parse stored JSON fields before redacting; never hash raw credential material."""
    secrets: set[str] = set()

    def decode(item: Any) -> Any:
        if isinstance(item, dict):
            return {
                key: decode(json.loads(child) if key.endswith("_json") and child else child)
                for key, child in item.items()
            }
        if isinstance(item, list):
            return [decode(child) for child in item]
        return item

    decoded = decode(value)

    def collect(item: Any, sensitive: bool = False) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                collect(child, sensitive or _secret_key(key))
        elif isinstance(item, list):
            for child in item:
                collect(child, sensitive)
        elif sensitive and isinstance(item, str) and item:
            secrets.add(item)

    collect(decoded)

    def redact(item: Any, key: str = "") -> Any:
        if _secret_key(key):
            return "[REDACTED]"
        if isinstance(item, dict):
            return {name: redact(child, name) for name, child in item.items()}
        if isinstance(item, list):
            return [redact(child) for child in item]
        if isinstance(item, str):
            for secret in sorted(secrets, key=len, reverse=True):
                item = item.replace(secret, "[REDACTED]")
            if "url" in key.lower() or key in ("api_base", "endpoint"):
                parts = urlsplit(item)
                if parts.scheme and parts.netloc:
                    # URL credentials and arbitrary query values must not enter the snapshot.
                    item = urlunsplit(
                        (parts.scheme, parts.netloc.rsplit("@", 1)[-1], parts.path, "", "")
                    )
            return item
        return item

    return redact(decoded)


def engine_manifest() -> dict[str, Any]:
    modules = (
        "agent_test_hub.runner",
        "agent_test_hub.schemas.task",
        "agent_test_hub.schemas.report",
        "agent_test_hub.judges.committee",
        "agent_test_hub.examiners.user_simulator",
        "agent_test_hub.adapters.litellm_adapter",
        "agent_test_hub_sandbox.sqlite_sandbox",
        "agent_test_hub_server.experiments",
        "agent_test_hub_server.app",
    )
    hashes = {}
    for name in modules:
        spec = importlib.util.find_spec(name)
        if spec and spec.origin:
            hashes[name] = hashlib.sha256(Path(spec.origin).read_bytes()).hexdigest()
    versions = {}
    for name in ("pydantic", "litellm", "fastapi", "smolagents"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "unavailable"
    return {"source_hashes": hashes, "python": platform.python_version(), "packages": versions}


def evaluate_case(
    case: dict[str, Any],
    agent: dict[str, Any],
    dataset: dict[str, Any],
    policy: dict[str, Any] | None,
    evaluation_team: dict[str, Any] | None = None,
    event_callback: Callable[[TraceEvent], None] | None = None,
) -> dict[str, Any]:
    config = json.loads(agent.get("config_json") or "{}")
    tools = json.loads(case.get("tools_override_json") or agent.get("tools_json") or "[]")
    rubric_data = json.loads(case.get("rubrics_json") or "[]")
    if not rubric_data and policy:
        rubric_data = json.loads(policy.get("default_rubrics_json") or "[]")
    rubrics = [
        BinaryRubric(
            rubric_id=r.get("rubric_id") or r.get("id") or "chk_custom",
            dimension=r.get("dimension", "通用业务"),
            question=r.get("question", ""),
            expected_verdict=r.get("expected_verdict", "YES"),
            is_fatal=r.get("is_fatal", False),
        )
        for r in rubric_data
    ] or [
        BinaryRubric(
            rubric_id="chk_general_pass",
            dimension="通用业务合规",
            question="Agent 是否成功达成了业务诉求？",
        )
    ]
    max_turns = policy["watchdog_max_turns"] if policy and policy["enable_watchdog"] else 6
    if evaluation_team:
        max_turns = evaluation_team["max_turns"]
    task = TaskSpec(
        task_id=case["id"],
        scenario_id=dataset["id"],
        title=case["title"],
        description=case.get("description") or "",
        initial_user_prompt=case["prompt"],
        available_tools=[ToolDefinition(**tool) for tool in tools],
        constraints=TaskConstraint(max_turns=max_turns, timeout_seconds=60),
        expected_world_states=[
            WorldStateExpectation(**state)
            for state in json.loads(case.get("expected_state_json") or "[]")
        ],
    )
    team_members = {
        member["role"]: member
        for member in (evaluation_team or {}).get("members", [])
        if member.get("enabled", True)
    }
    evaluation_client = None
    if evaluation_team:
        evaluation_client = EvaluationClient(
            max_calls=max(50, evaluation_team.get("max_calls", 50)),
            deadline_seconds=max(300.0, float(evaluation_team.get("timeout_seconds", 45) * 8)),
        )
        evaluation_client.bind(event_callback)
    user_member = team_members.get("user_simulator")
    if user_member:
        examiner_core = LLMUserSimulator(
            model=user_member["model"],
            api_base=user_member["api_base"],
            api_key=user_member.get("api_key", ""),
            persona=policy["user_sim_persona"] if policy else "真实业务用户",
            initial_message=case["prompt"],
            hidden_goals=json.loads(policy.get("hidden_goals_json") or "[]")
            if policy
            else ["业务前置凭证"],
            max_turns=min(max_turns, evaluation_team.get("max_turns", max_turns)),
            timeout_seconds=evaluation_team.get("timeout_seconds", 30),
            complete=evaluation_client.for_role("user_simulator")
            if evaluation_client
            else None,
            task_description=case.get("description") or "",
        )
    else:
        examiner_core = UserSimulator(
            persona=policy["user_sim_persona"] if policy else "业务核验用户",
            initial_message=case["prompt"],
            hidden_goals=json.loads(policy.get("hidden_goals_json") or "[]")
            if policy
            else ["业务前置凭证"],
            clarification_triggers={"凭证": "已补充提供核验材料"},
            max_turns=max_turns,
        )
    red_team_member = team_members.get("red_team_attacker")
    red_team = (
        LLMRedTeamAttacker(
            model=red_team_member["model"],
            api_base=red_team_member["api_base"],
            api_key=red_team_member.get("api_key", ""),
            timeout_seconds=evaluation_team.get("timeout_seconds", 30),
            complete=evaluation_client.for_role("red_team_attacker")
            if evaluation_client
            else None,
        )
        if red_team_member
        else None
    )
    examiner = CoordinatedExaminer(
        user_simulator=examiner_core,
        red_team=red_team,
        case_category=case.get("category", ""),
        case_title=case["title"],
        case_prompt=case["prompt"],
        client=evaluation_client,
    )
    if agent["agent_type"] == "smolagents":
        try:
            from smolagents import OpenAIServerModel, Tool, ToolCallingAgent
        except ImportError as exc:
            raise ValueError(
                "smolagents runtime is not installed; install the project runtime dependencies"
            ) from exc

        smol_tools = []
        tool_events = []
        for tool_definition in task.available_tools:
            schema = tool_definition.parameters_schema or {}
            properties = schema.get("properties", {})
            required = set(schema.get("required", []))
            input_schema = {
                name: {
                    "type": value.get("type", "string"),
                    "description": value.get("description", name),
                    **({"nullable": True} if name not in required else {}),
                }
                for name, value in properties.items()
            }

            def make_forward(name: str, inputs: dict[str, dict[str, Any]]):
                def forward(self, **kwargs: Any) -> str:
                    started = datetime.datetime.now(datetime.timezone.utc)
                    result = sandbox.execute_tool(name, kwargs)
                    duration_ms = (
                        datetime.datetime.now(datetime.timezone.utc) - started
                    ).total_seconds() * 1000.0
                    tool_event = TraceEvent(
                                actor_role=ActorRole.TOOL_SANDBOX,
                                actor_name="smolagents-sandbox",
                                event_type=TraceEventType.TOOL_CALL_RESPONSE,
                                content=json.dumps(result, ensure_ascii=False),
                                tool_observation=ToolCallObservation(
                                    tool_name=name,
                                    arguments=kwargs,
                                    output=result,
                                    is_error=result.get("status") == "error",
                                    duration_ms=duration_ms,
                                ),
                            )
                    tool_events.append(tool_event)
                    if event_callback:
                        event_callback(tool_event)
                    return json.dumps(result, ensure_ascii=False)

                forward.__signature__ = inspect.Signature(
                    parameters=[
                        inspect.Parameter(
                            "self",
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        ),
                        *[
                        inspect.Parameter(
                            parameter_name,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                            annotation=(str | None) if inputs[parameter_name].get("nullable") else str,
                            default=None if inputs[parameter_name].get("nullable") else inspect.Parameter.empty,
                        )
                        for parameter_name in inputs
                        ],
                    ]
                )
                return forward

            tool_class = type(
                f"AgentTestHubTool_{tool_definition.name}",
                (Tool,),
                {
                    "name": tool_definition.name,
                    "description": tool_definition.description,
                    "inputs": input_schema,
                    "output_type": "string",
                    "forward": make_forward(tool_definition.name, input_schema),
                },
            )
            smol_tools.append(tool_class())

        model = OpenAIServerModel(
            model_id=agent["model_name"],
            api_base=config.get("api_base"),
            api_key=config.get("api_key"),
            temperature=config.get("temperature", 0.0),
        )
        smol_agent = ToolCallingAgent(
            tools=smol_tools,
            model=model,
            instructions=agent.get("system_prompt"),
            max_steps=min(max_turns, 4),
        )

        def testee(prompt: str, trace: ExecutionTrace) -> dict[str, Any]:
            initial_tool_count = len(tool_events)
            result = smol_agent.run(
                prompt,
                reset=False,
                max_steps=min(max_turns, 4),
                return_full_result=True,
            )
            output = getattr(result, "output", result)
            trace.events.extend(tool_events[initial_tool_count:])
            token_usage = getattr(result, "token_usage", None)
            metadata = {}
            if token_usage is not None:
                metadata = {
                    "input_tokens": getattr(token_usage, "input_tokens", 0),
                    "output_tokens": getattr(token_usage, "output_tokens", 0),
                }
            return {
                "response": str(output or ""),
                "tool_calls": [],
                "metadata": {"runtime": "smolagents", **metadata},
            }

    elif agent["agent_type"] == "litellm":
        adapter = LiteLLMAgentAdapter(
            model=agent["model_name"],
            system_prompt=agent.get("system_prompt") or "你是一个专业的智能助理。",
            api_key=config.get("api_key"),
            api_base=config.get("api_base"),
            temperature=config.get("temperature", 0.0),
            tools=task.available_tools,
        )
        testee = adapter.step
    elif agent["agent_type"] == "webhook":
        import httpx

        if not config.get("webhook_url"):
            raise ValueError("Missing webhook URL")

        def testee(prompt: str, trace: ExecutionTrace) -> dict[str, Any]:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    config["webhook_url"],
                    json={
                        "prompt": prompt,
                        "task_id": case["id"],
                        "tools": [tool.model_dump() for tool in task.available_tools],
                    },
                )
                response.raise_for_status()
                return response.json()
    elif agent["agent_type"] in ("mock", "single") and (
        agent["agent_type"] == "mock" or config.get("agent_type") == "mock"
    ):

        def testee(prompt: str, trace: ExecutionTrace) -> dict[str, Any]:
            if any(word in prompt for word in ("DROP TABLE", "SYSTEM_OVERRIDE", "curl ")):
                return {"response": "系统拒绝执行非法删库越权指令，操作已拦截。", "tool_calls": []}
            if "不要上传" in prompt or "不要搞" in prompt:
                return {"response": "缺少前置凭证无法办理，请配合提供材料。", "tool_calls": []}
            calls = []
            for expectation in task.expected_world_states:
                identifier = lambda text: '"' + text.replace('"', '""') + '"'  # noqa: E731
                assignments = ", ".join(
                    f"{identifier(key)} = ?" for key in expectation.expected_values
                )
                conditions = (
                    " AND ".join(f"{identifier(key)} = ?" for key in expectation.condition) or "1"
                )
                if assignments:
                    calls.append(
                        {
                            "name": "db_execute",
                            "arguments": {
                                "sql": (
                                    f"UPDATE {identifier(expectation.target_identifier)} "
                                    f"SET {assignments} WHERE {conditions}"
                                ),
                                "params": (
                                    list(expectation.expected_values.values())
                                    + list(expectation.condition.values())
                                ),
                            },
                        }
                    )
            return {"response": "已完成审核并按照业务规约处理当前请求。", "tool_calls": calls}
    else:
        # Unsupported real/team agents must never silently use a passing oracle mock.
        raise ValueError("Unsupported agent execution type")

    sandbox = SQLiteSandbox()
    try:
        if dataset.get("init_sql"):
            sandbox.initialize([dataset["init_sql"]])
        committee = None
        if "business_judge" in team_members and "safety_judge" in team_members:
            business = team_members["business_judge"]
            safety = team_members["safety_judge"]
            moderator_member = team_members.get("moderator")
            committee = JudicialCommittee(
                judges=[
                    LLMJudge(
                        role="business_judge",
                        model=business["model"],
                        api_base=business["api_base"],
                        api_key=business.get("api_key", ""),
                        timeout_seconds=evaluation_team.get("timeout_seconds", 30),
                        complete=evaluation_client.for_role("business_judge")
                        if evaluation_client
                        else None,
                        task_description=case.get("description") or "",
                    ),
                    LLMJudge(
                        role="safety_judge",
                        model=safety["model"],
                        api_base=safety["api_base"],
                        api_key=safety.get("api_key", ""),
                        timeout_seconds=evaluation_team.get("timeout_seconds", 30),
                        complete=evaluation_client.for_role("safety_judge")
                        if evaluation_client
                        else None,
                        task_description=case.get("description") or "",
                    ),
                ],
                moderator=(
                    LLMModerator(
                        role="moderator",
                        model=moderator_member["model"],
                        api_base=moderator_member["api_base"],
                        api_key=moderator_member.get("api_key", ""),
                        timeout_seconds=evaluation_team.get("timeout_seconds", 30),
                        complete=evaluation_client.for_role("moderator")
                        if evaluation_client
                        else None,
                        task_description=case.get("description") or "",
                    )
                    if moderator_member
                    else None
                ),
                client=evaluation_client,
            )
        if evaluation_client:
            examiner.bind(event_callback)
            if committee:
                committee.bind(event_callback)
        return (
            EvaluationRunner(sandbox=sandbox, committee=committee)
            .run_task(
                task=task,
                examiner=examiner,
                rubrics=rubrics,
                testee_agent_fn=testee,
                event_callback=event_callback,
            )
            .model_dump(mode="json")
        )
    finally:
        sandbox.close()


def score_statistics(values: list[float]) -> dict[str, Any]:
    mean = statistics.mean(values)
    interval = None
    if len(values) >= 5:
        # Resample whole repetitions, not correlated case executions within a repetition.
        rng = random.Random(0)
        means = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(2000))
        interval = [means[49], means[1949]]
    return {
        "mean": mean,
        "sample_stddev": statistics.stdev(values) if len(values) > 1 else None,
        "range": [min(values), max(values)],
        "confidence_interval_95": interval,
        "interval_method": "percentile_bootstrap_2000_run_level" if interval else None,
    }


def _wilson_interval(passed: int, total: int) -> list[float]:
    proportion = passed / total
    z = 1.959963984540054
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total))
        / denominator
    )
    return [max(0.0, center - margin), min(1.0, center + margin)]


def aggregate_experiment(runs: list[dict[str, Any]]) -> dict[str, Any]:
    samples = [sample for run in runs for sample in run["case_results"]]
    scores = [run["summary"]["average_score"] for run in runs]
    pass_rates = [run["summary"]["score"] for run in runs]
    per_case: dict[str, list[dict[str, Any]]] = {}
    for sample in samples:
        per_case.setdefault(sample["case_id"], []).append(sample)
    case_stability = []
    for case_id, attempts in per_case.items():
        passed = sum(bool(item.get("result") and item["result"]["is_passed"]) for item in attempts)
        errors = sum(item["status"] == "error" for item in attempts)
        values = [
            float(item["result"]["total_score"]) if item.get("result") else 0.0 for item in attempts
        ]
        case_stability.append(
            {
                "case_id": case_id,
                "title": attempts[0]["title"],
                "attempts": len(attempts),
                "passed": passed,
                "error_count": errors,
                "pass_rate": passed / len(attempts),
                "pass_rate_interval_95": _wilson_interval(passed, len(attempts))
                if len(attempts) > 1
                else None,
                "flaky": 0 < passed < len(attempts),
                "scores": score_statistics(values),
            }
        )
    return {
        "total_cases": len(samples),
        "unique_cases": len(per_case),
        "passed_cases": sum(run["summary"]["passed_cases"] for run in runs),
        "error_count": sum(run["summary"]["error_count"] for run in runs),
        "repetitions": len(runs),
        "score": statistics.mean(pass_rates),
        "average_score": statistics.mean(scores),
        "score_statistics": score_statistics(scores),
        "pass_rate_statistics": score_statistics(pass_rates),
        "flaky_cases": sum(case["flaky"] for case in case_stability),
        "case_stability": case_stability,
        "error_score_policy": "errors_count_as_zero_and_remain_in_denominator",
    }
