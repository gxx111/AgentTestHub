from __future__ import annotations

import json
from typing import Any, Callable

import httpx

from agent_test_hub.examiners import BaseExaminer, UserSimulator
from agent_test_hub.judges import JudicialCommittee
from agent_test_hub.runner import EvaluationRunner
from agent_test_hub.schemas import BinaryRubric, TaskEvaluationResult, TaskSpec
from agent_test_hub_domain.gate import GateDecision, GatePolicy, ReleaseGateEvaluator
from agent_test_hub_sandbox import BaseSandbox, SQLiteSandbox


class AgentTestHubClient:
    """AgentTestHub 统一 Python 开发者 SDK (E13-01)

    支持：
    1. 本地轻量运行模式 (in-process / SQLite / 内存沙盒，无需启动后端服务)；
    2. 远端 Control Plane API 运行模式 (集成多租户持久化与集中调度)；
    3. CI 门禁断言与快速评测执行。
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_token: str | None = None,
        workspace_id: str = "default_ws",
    ):
        self.base_url = base_url.rstrip("/") if base_url else None
        self.api_token = api_token
        self.workspace_id = workspace_id
        self.is_remote = bool(self.base_url)

    def evaluate(
        self,
        task: TaskSpec,
        rubrics: list[BinaryRubric],
        testee_agent_fn: Callable[[str, Any], dict[str, Any]],
        examiner: BaseExaminer | None = None,
        sandbox: BaseSandbox | None = None,
        init_sql: list[str] | None = None,
    ) -> TaskEvaluationResult:
        """运行单任务评测闭环并产出评测裁决报告"""
        if self.is_remote:
            return self._evaluate_remote(task, rubrics, testee_agent_fn)
        return self._evaluate_local(task, rubrics, testee_agent_fn, examiner, sandbox, init_sql)

    def _evaluate_local(
        self,
        task: TaskSpec,
        rubrics: list[BinaryRubric],
        testee_agent_fn: Callable[[str, Any], dict[str, Any]],
        examiner: BaseExaminer | None = None,
        sandbox: BaseSandbox | None = None,
        init_sql: list[str] | None = None,
    ) -> TaskEvaluationResult:
        sb = sandbox or SQLiteSandbox()
        if init_sql and hasattr(sb, "initialize"):
            sb.initialize(init_sql)

        ex = examiner or UserSimulator(
            persona="业务用户",
            initial_message=task.initial_user_prompt,
            hidden_goals=[],
            max_turns=task.constraints.max_turns,
        )

        runner = EvaluationRunner(sandbox=sb, committee=JudicialCommittee())
        result = runner.run_task(task, ex, rubrics, testee_agent_fn)
        if not sandbox:
            sb.close()
        return result

    def _evaluate_remote(
        self,
        task: TaskSpec,
        rubrics: list[BinaryRubric],
        testee_agent_fn: Callable[[str, Any], dict[str, Any]],
    ) -> TaskEvaluationResult:
        headers = {"Authorization": f"Bearer {self.api_token}"} if self.api_token else {}
        # 远程 HTTP 请求控制面
        resp = httpx.post(
            f"{self.base_url}/evaluations/run",
            headers=headers,
            json={
                "task": task.model_dump(mode="json"),
                "rubrics": [r.model_dump(mode="json") for r in rubrics],
                "workspace_id": self.workspace_id,
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return TaskEvaluationResult.model_validate(data)

    def check_release_gate(
        self,
        result: TaskEvaluationResult | list[TaskEvaluationResult],
        policy: GatePolicy | None = None,
    ) -> GateDecision:
        """计算发布门禁决策"""
        return ReleaseGateEvaluator.evaluate(result, policy=policy)
