from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .rubric import RubricJudgment
from .trace import ExecutionTrace


class AttributionNode(BaseModel):
    """阿里 7-Hop 故障因果归因树节点"""

    model_config = ConfigDict(frozen=True)

    node_id: str = Field(description="节点 ID")
    hop_stage: str = Field(description="故障发生的链路跳数 (Hop1 ~ Hop7 或 MAS)")
    failure_category: str = Field(description="故障大类: AST 校验失败 / 路由错误 / 死锁 / 越权")
    evidence_span_id: str | None = Field(default=None, description="定罪证据 Trace Span ID")
    root_cause_explanation: str = Field(description="根本原因因果推导说明")
    suggested_action: str = Field(description="针对性修复建议 (如优化 Prompt / 拓扑解耦)")


class RadarDimension(BaseModel):
    """雷达图能力维度评分"""

    model_config = ConfigDict(frozen=True)

    dimension_name: str = Field(description="维度名 (如 Tool Calling, Planning, Safety, MAS)")
    score: float = Field(ge=0.0, le=1.0, description="归一化得分 (0.0 ~ 1.0)")
    total_checks: int = Field(ge=0, description="该维度检查项总数")
    passed_checks: int = Field(ge=0, description="该维度通过检查项数")


class TaskEvaluationResult(BaseModel):
    """单任务评测完整裁决结果"""

    model_config = ConfigDict(frozen=True)

    task_id: str = Field(description="任务 ID")
    is_passed: bool = Field(description="综合裁决是否通过")
    total_score: float = Field(ge=0.0, le=1.0, description="加权总分 (0.0 ~ 1.0)")

    # 状态差分核验结果
    world_state_passed: bool = Field(default=True, description="物理世界真实状态是否完全达标")
    world_state_diff: dict[str, Any] = Field(default_factory=dict, description="真实状态差分详情")

    # 美团二元 Rubric 评审结果汇总
    rubric_judgments: list[RubricJudgment] = Field(
        default_factory=list, description="二元检查项裁判明细"
    )
    unknown_rubric_count: int = Field(
        default=0, description="被判为 UNKNOWN 的检查项数量 (大于0触发模糊告警)"
    )

    # 归因树 (仅在未通过时产出)
    attribution_tree: list[AttributionNode] = Field(
        default_factory=list, description="故障因果推导链路"
    )

    # 完整执行轨迹事件流
    trace: ExecutionTrace | None = Field(default=None, description="完整执行轨迹日志")

    # 性能与开销指标
    total_tokens: int = Field(default=0, ge=0)
    total_duration_ms: float = Field(default=0.0, ge=0.0)


class EvaluationReport(BaseModel):
    """评测套件全局综合报告 (终极输出 deliverable)"""

    model_config = ConfigDict(frozen=True)

    suite_name: str = Field(description="评测套件名称")
    target_agent_id: str = Field(description="被测 Agent 标识")
    timestamp: str = Field(description="评测生成时间")

    # 宏观总体指标
    pass_rate: float = Field(ge=0.0, le=1.0, description="总体任务通过率")
    average_score: float = Field(ge=0.0, le=1.0, description="总体平均得分")
    total_tasks: int = Field(ge=0, description="评测用例总数")
    passed_tasks: int = Field(ge=0, description="通过用例数")

    # 可视化维度雷达
    radar_dimensions: list[RadarDimension] = Field(
        default_factory=list, description="能力雷达图数据"
    )

    # 细粒度任务详情
    task_results: list[TaskEvaluationResult] = Field(
        default_factory=list, description="逐个任务执行裁决"
    )

    # 宏观优化建议汇总
    top_recommendations: list[str] = Field(default_factory=list, description="系统级优化建议Top-N")
