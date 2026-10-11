from __future__ import annotations

from typing import Any

from agent_test_hub.schemas import ExecutionTrace

from ..base import BaseMetric, MetricResult


class ToolArgumentASTMetric(BaseMetric):
    """阿里 Hop 4: 工具调用参数抽象语法树 (AST) 结构与类型合规性校验"""

    name: str = "hop4_arg_ast_validation"
    dimension: str = "Hop4_Argument_AST"

    def __init__(self, required_schema: dict[str, dict[str, Any]] | None = None):
        # 格式: {tool_name: {param_name: expected_type_str}}
        self.required_schema = required_schema or {}

    def evaluate(
        self, trace: ExecutionTrace, context: dict[str, Any] | None = None
    ) -> MetricResult:
        tool_calls = trace.get_tool_calls()
        if not tool_calls:
            return MetricResult(
                metric_name=self.name,
                dimension=self.dimension,
                score=1.0,
                is_passed=True,
                rationale="本用例未发生工具调用，跳过 AST 校验",
            )

        total_checked = 0
        valid_count = 0
        violations: list[str] = []

        for call in tool_calls:
            total_checked += 1
            tool_name = call.tool_name
            args = call.arguments

            # 1. 验证传参是否为合法字典
            if not isinstance(args, dict):
                violations.append(f"工具 {tool_name} 传入了非字典参数: {args}")
                continue

            # 2. 若配置了 Schema，进行类型与必填项 AST 验证
            if tool_name in self.required_schema:
                expected = self.required_schema[tool_name]
                has_error = False
                for field, expected_type in expected.items():
                    if field not in args:
                        has_error = True
                        violations.append(f"工具 {tool_name} 遗漏必填字段 '{field}'")
                        break

                    val = args[field]
                    if expected_type == "int" and not isinstance(val, int):
                        has_error = True
                        violations.append(
                            f"工具 {tool_name} 字段 '{field}' 类型应为 int，实为 {type(val).__name__}"
                        )
                        break
                    elif expected_type == "str" and not isinstance(val, str):
                        has_error = True
                        violations.append(
                            f"工具 {tool_name} 字段 '{field}' 类型应为 str，实为 {type(val).__name__}"
                        )
                        break

                if not has_error:
                    valid_count += 1
            else:
                valid_count += 1

        score = valid_count / total_checked if total_checked > 0 else 1.0
        return MetricResult(
            metric_name=self.name,
            dimension=self.dimension,
            score=score,
            is_passed=(score == 1.0),
            details={
                "total_calls": total_checked,
                "valid_calls": valid_count,
                "violations": violations,
            },
            rationale="所有工具参数 AST 校验均合规"
            if score == 1.0
            else f"发现 {len(violations)} 处参数语法/类型违规",
        )
