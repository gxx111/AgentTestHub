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
    """声明式 YAML 评测套件加载器 (支持单任务与多用例数据集两种模式)"""

    @classmethod
    def _parse_rubrics(cls, raw_rubrics: list[dict[str, Any]]) -> list[BinaryRubric]:
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
        return rubrics

    @classmethod
    def load_from_file(cls, yaml_path: str | pathlib.Path) -> dict[str, Any]:
        path = pathlib.Path(yaml_path)
        with open(path, encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        suite_name = raw_data.get("suite_name", "Default Test Suite")
        init_sql = raw_data.get("init_sql", [])

        # 检查是否为多用例模式 (test_cases 模式)
        if "test_cases" in raw_data and isinstance(raw_data["test_cases"], list):
            parsed_cases = []
            for item in raw_data["test_cases"]:
                tools = [ToolDefinition(**t) for t in item.get("tools", [])]
                expectations = [
                    WorldStateExpectation(**e) for e in item.get("expected_world_states", [])
                ]
                constraints = TaskConstraint(**item.get("constraints", {}))

                task_spec = TaskSpec(
                    task_id=item.get("id", "case_001"),
                    scenario_id=item.get("scenario_id", "default_scenario"),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    initial_user_prompt=item.get("initial_user_prompt", item.get("prompt", "")),
                    category=item.get("category", "general"),
                    available_tools=tools,
                    constraints=constraints,
                    expected_world_states=expectations,
                )

                rubrics = cls._parse_rubrics(item.get("rubrics", []))
                examiner_cfg = item.get("examiner", {})

                parsed_cases.append(
                    {
                        "id": task_spec.task_id,
                        "title": task_spec.title,
                        "category": task_spec.category,
                        "description": task_spec.description,
                        "prompt": task_spec.initial_user_prompt,
                        "task": task_spec,
                        "rubrics": rubrics,
                        "examiner_config": examiner_cfg,
                    }
                )

            # 默认主任务取第一个
            first_case = parsed_cases[0]
            return {
                "suite_name": suite_name,
                "init_sql": init_sql,
                "test_cases": parsed_cases,
                # 兼容旧单任务接口
                "task": first_case["task"],
                "rubrics": first_case["rubrics"],
                "examiner_config": first_case["examiner_config"],
            }

        # 兼容传统单任务 (task 模式)
        raw_task = raw_data.get("task", {})
        tools = [ToolDefinition(**t) for t in raw_task.get("tools", [])]
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

        rubrics = cls._parse_rubrics(raw_data.get("rubrics", []))
        examiner_cfg = raw_data.get("examiner", {})

        single_case = {
            "id": task_spec.task_id,
            "title": task_spec.title,
            "category": task_spec.category,
            "description": task_spec.description,
            "prompt": task_spec.initial_user_prompt,
            "task": task_spec,
            "rubrics": rubrics,
            "examiner_config": examiner_cfg,
        }

        return {
            "suite_name": suite_name,
            "task": task_spec,
            "rubrics": rubrics,
            "examiner_config": examiner_cfg,
            "init_sql": init_sql,
            "test_cases": [single_case],
        }
