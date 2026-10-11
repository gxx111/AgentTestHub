from __future__ import annotations

import pathlib
from typing import Any
import yaml
from agent_test_hub.schemas import (
    BinaryRubric,
    BinaryVerdict,
    TaskConstraint,
    TaskSpec,
    ToolDefinition,
    WorldStateExpectation,
)


class DeclarativeYAMLLoader:
    """声明式 YAML 评测套件加载器"""

    @classmethod
    def load_from_file(cls, yaml_path: str | pathlib.Path) -> dict[str, Any]:
        path = pathlib.Path(yaml_path)
        with open(path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        # 1. 解析任务规范 TaskSpec
        raw_task = raw_data.get("task", {})
        tools = [
            ToolDefinition(**t) for t in raw_task.get("tools", [])
        ]
        expectations = [
            WorldStateExpectation(**e) for e in raw_task.get("expected_world_states", [])
        ]
        constraints = TaskConstraint(**raw_task.get("constraints", {}))

        task_spec = TaskSpec(
            task_id=raw_task.get("task_id", "unnamed_task"),
            scenario_id=raw_task.get("scenario_id", "default_scenario"),
            title=raw_task.get("title", ""),
            description=raw_task.get("description", ""),
            initial_user_prompt=raw_task.get("initial_user_prompt", ""),
            available_tools=tools,
            constraints=constraints,
            expected_world_states=expectations,
        )

        # 2. 解析美团二元 Rubric 列表
        raw_rubrics = raw_data.get("rubrics", [])
        rubrics = []
        for r in raw_rubrics:
            exp_verdict = BinaryVerdict(r.get("expected_verdict", "YES"))
            rubrics.append(
                BinaryRubric(
                    rubric_id=r["id"],
                    dimension=r.get("dimension", "general"),
                    question=r["question"],
                    expected_verdict=exp_verdict,
                    is_fatal=r.get("is_fatal", False),
                    weight=r.get("weight", 1.0),
                )
            )

        return {
            "suite_name": raw_data.get("suite_name", "Default Test Suite"),
            "task": task_spec,
            "rubrics": rubrics,
            "examiner_config": raw_data.get("examiner", {}),
            "init_sql": raw_data.get("init_sql", []),
        }
