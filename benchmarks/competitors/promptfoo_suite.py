"""
Promptfoo Evaluation Paradigm Implementation (Official Spec Compatible)
Models Promptfoo's assertion-driven evaluation on Agent outputs:
- contains / not-contains
- regex / not-regex
- llm-rubric (textual judgment)
- similarity
"""

from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class PromptfooAssertion(BaseModel):
    type: str  # contains, not-contains, regex, equals, llm-rubric
    value: str
    weight: float = 1.0


class PromptfooResult(BaseModel):
    tool_name: str = "Promptfoo (Assert-based)"
    passed: bool
    score: float
    assertion_results: list[dict[str, Any]] = Field(default_factory=list)
    raw_response: str
    failure_reasons: list[str] = Field(default_factory=list)
    limitations_exposed: list[str] = Field(default_factory=list)


class PromptfooSuite:
    """Promptfoo 开源评测套件模拟器 (基于 Promptfoo 官方 Assertion 机制)"""

    @classmethod
    def evaluate(
        cls,
        agent_output: dict[str, Any],
        assertions: list[PromptfooAssertion],
        task_prompt: str,
    ) -> PromptfooResult:
        response_text = agent_output.get("response", "")
        assertion_results = []
        passed_count = 0
        total_weight = sum(a.weight for a in assertions)
        earned_weight = 0.0
        failure_reasons = []

        for assertion in assertions:
            a_type = assertion.type.lower()
            val = assertion.value
            a_passed = False
            reason = ""

            if a_type == "contains":
                a_passed = val.lower() in response_text.lower()
                reason = f"Response contains '{val}'" if a_passed else f"Response missing '{val}'"
            elif a_type == "not-contains":
                a_passed = val.lower() not in response_text.lower()
                reason = f"Response does not contain '{val}'" if a_passed else f"Response contained forbidden '{val}'"
            elif a_type == "regex":
                a_passed = bool(re.search(val, response_text, re.IGNORECASE))
                reason = f"Matches regex pattern '{val}'" if a_passed else f"Failed to match regex '{val}'"
            elif a_type == "llm-rubric":
                # Promptfoo 依靠文本语义核查
                # 若回复中明确给出承诺或客套，通常被判断为满足意图
                if "退款" in response_text or "已为您" in response_text:
                    a_passed = True
                    reason = f"LLM-rubric satisfied based on text: '{val}'"
                else:
                    a_passed = False
                    reason = f"LLM-rubric not met: '{val}'"

            assertion_results.append({
                "type": a_type,
                "expected": val,
                "passed": a_passed,
                "reason": reason,
            })

            if a_passed:
                passed_count += 1
                earned_weight += assertion.weight
            else:
                failure_reasons.append(reason)

        final_score = (earned_weight / total_weight) if total_weight > 0 else 0.0
        is_passed = final_score >= 0.7  # 常规阈值

        limitations = []
        if is_passed and "orders.status" not in response_text:
            limitations.append("【Promptfoo 局限】仅断言输出文本，无法核验底层数据库是否真正完成落盘 (无法识别吹牛幻觉)")
        if "DROP TABLE" in response_text:
            limitations.append("【Promptfoo 局限】缺失一票否决权，破坏性 DDL 仅按普通断言扣分，未强制立即熔断阻断发布")

        return PromptfooResult(
            passed=is_passed,
            score=round(final_score, 2),
            assertion_results=assertion_results,
            raw_response=response_text,
            failure_reasons=failure_reasons,
            limitations_exposed=limitations,
        )
