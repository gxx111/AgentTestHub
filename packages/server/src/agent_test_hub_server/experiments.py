from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
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
from agent_test_hub.examiners import UserSimulator
from agent_test_hub.runner import EvaluationRunner
from agent_test_hub.schemas import (
    BinaryRubric,
    ExecutionTrace,
    TaskConstraint,
    TaskSpec,
    ToolDefinition,
    TraceEvent,
    WorldStateExpectation,
)
from agent_test_hub_sandbox import SQLiteSandbox


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def _secret_key(key: str) -> bool:
    normalized = "".join(char for char in key.lower() if char.isalnum())
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
    for name in ("pydantic", "litellm", "fastapi"):
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
    examiner = UserSimulator(
        persona=policy["user_sim_persona"] if policy else "业务核验用户",
        initial_message=case["prompt"],
        hidden_goals=json.loads(policy.get("hidden_goals_json") or "[]")
        if policy
        else ["业务前置凭证"],
        clarification_triggers={"凭证": "已补充提供核验材料"},
        max_turns=max_turns,
    )
    if agent["agent_type"] == "litellm":
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
        return (
            EvaluationRunner(sandbox=sandbox)
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
