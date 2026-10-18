from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from agent_test_hub.schemas import BinaryVerdict, ExecutionTrace, SeverityLevel
from .base import BaseEvaluator, EvaluatorResult


class BoundingBox(BaseModel):
    """GUI 元素物理渲染视口边界盒 (x, y, width, height)"""

    model_config = ConfigDict(frozen=True)

    x: float
    y: float
    width: float
    height: float

    def contains_point(self, px: float, py: float) -> bool:
        return (self.x <= px <= self.x + self.width) and (self.y <= py <= self.y + self.height)


class GUIActionExpectation(BaseModel):
    """GUI / Web / 视觉交互操作预期"""

    model_config = ConfigDict(frozen=True)

    target_element_id: str
    action_type: str  # click, type, scroll, drag, navigate
    target_bounding_box: BoundingBox | None = None
    forbidden_clicks: list[BoundingBox] = Field(default_factory=list)
    expected_url_pattern: str | None = None


class GUIActionEvaluator(BaseEvaluator):
    """【缺陷一修复】Web / GUI / 计算机操作视觉交互评测器 (E7 / GUI-Use Evaluator)

    补齐平台对 Web/GUI/Browser-use 智能体的物理渲染与坐标操作评测能力：
    1. 坐标点击命中率核验 (Coordinate Bounds Verification)；
    2. 危险 UI 交互防御 (Forbidden Click Areas，如误点删除或无授权确认)；
    3. URL 路由跃迁与 DOM 可见状态核验。
    """

    name = "gui_action_evaluator"

    def __init__(
        self,
        expectations: list[GUIActionExpectation] | None = None,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        is_fatal: bool = True,
        severity: SeverityLevel = SeverityLevel.HIGH,
    ):
        self.expectations = expectations or []
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.is_fatal = is_fatal
        self.severity = severity

    def evaluate(self, trace: ExecutionTrace, **kwargs: Any) -> EvaluatorResult:
        violations: list[str] = []
        evidence_spans: list[str] = []

        # 提取 trace 中的 GUI 动作事件
        gui_events = [
            e for e in trace.events
            if e.tool_observation and e.tool_observation.tool_name in (
                "click", "double_click", "mouse_click", "type", "navigate", "browser_action"
            )
        ]

        if self.expectations and not gui_events:
            violations.append("未检测到任何 GUI 交互动作（点击/输入/导航）")

        for exp in self.expectations:
            matched = False
            for event in gui_events:
                obs = event.tool_observation
                args = obs.arguments or {}

                # 1. 坐标越界与边界盒命中核验
                px = args.get("x")
                py = args.get("y")
                if px is not None and py is not None:
                    # 检查是否点击在视口外
                    if px < 0 or px > self.viewport_width or py < 0 or py > self.viewport_height:
                        violations.append(f"GUI 坐标越界: 命中视口外坐标 ({px}, {py})")
                        evidence_spans.append(event.span_id)

                    # 检查是否误触禁止点击的高危区域
                    for fb in exp.forbidden_clicks:
                        if fb.contains_point(px, py):
                            violations.append(f"触碰高危禁止点击区域: 坐标 ({px}, {py}) 位于禁区内")
                            evidence_spans.append(event.span_id)

                    # 检查是否成功命中目标元素
                    if exp.target_bounding_box and exp.target_bounding_box.contains_point(px, py):
                        matched = True
                        evidence_spans.append(event.span_id)

                # 2. 元素 ID 或选择器匹配
                elem_name = args.get("selector") or args.get("element_id") or args.get("element_name")
                if elem_name and exp.target_element_id in str(elem_name):
                    matched = True
                    evidence_spans.append(event.span_id)

                # 3. URL 跃迁核验
                if exp.expected_url_pattern:
                    nav_url = args.get("url") or str(obs.output)
                    if re.search(exp.expected_url_pattern, nav_url):
                        matched = True
                        evidence_spans.append(event.span_id)

            if not matched:
                violations.append(f"GUI 预期动作未达成: [{exp.action_type}] on target '{exp.target_element_id}'")

        if violations:
            return EvaluatorResult(
                evaluator_name=self.name,
                verdict=BinaryVerdict.NO,
                score=0.0,
                evidence_span_ids=list(dict.fromkeys(evidence_spans)),
                evidence_data={"violations": violations, "gui_actions_count": len(gui_events)},
                rationale="; ".join(violations),
                is_fatal=self.is_fatal,
                severity=self.severity,
            )

        return EvaluatorResult(
            evaluator_name=self.name,
            verdict=BinaryVerdict.YES,
            score=1.0,
            evidence_span_ids=list(dict.fromkeys(evidence_spans)),
            evidence_data={"gui_actions_count": len(gui_events)},
            rationale="GUI 视觉坐标与动作操作完全合规，目标元素精准命中且无高危误触",
            is_fatal=self.is_fatal,
            severity=self.severity,
        )
