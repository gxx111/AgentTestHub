from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class BinaryVerdict(str, Enum):
    """美团二元事实检查评判枚举 (杜绝模糊的 0-10 分)"""

    YES = "YES"  # 事实成立 / 检查项达标 (计 1.0)
    NO = "NO"  # 事实不成立 / 违背检查项 (计 0.0)
    UNKNOWN = "UNKNOWN"  # 无法从日志证据中判断 (触发 Rubric 模糊度告警)


class BinaryRubric(BaseModel):
    """美团下钻二元 Rubric 检查项定义"""

    model_config = ConfigDict(frozen=True)

    rubric_id: str = Field(description="检查项全局唯一 ID")
    dimension: str = Field(
        description="所属指标大类: rule_compliance / tool_ast / safety / empathy 等"
    )
    question: str = Field(description="能明确回答 是/否/未知 的具体事实检查问题")
    expected_verdict: BinaryVerdict = Field(
        default=BinaryVerdict.YES, description="期望的正确判决 (通常为 YES，违规检测项可能为 NO)"
    )
    is_fatal: bool = Field(
        default=False, description="是否属于一票否决项 (若未达标则整个任务直接判定失败)"
    )
    weight: float = Field(default=1.0, ge=0.0, description="权重贡献分值")
    description: str = Field(default="", description="该检查项的详细说明与对齐准则")


class RubricJudgment(BaseModel):
    """单法官针对单条二元 Rubric 给出的审理判决"""

    model_config = ConfigDict(frozen=True)

    rubric_id: str = Field(description="被评审的 Rubric ID")
    judge_role: str = Field(
        description="打分法官角色标识: rule_judge / fact_judge / safety_judge 等"
    )
    verdict: BinaryVerdict = Field(description="给出的二元裁决")
    evidence_span_ids: list[str] = Field(
        default_factory=list, description="强制引用的 Trace 日志 Span ID 证据链锚点"
    )
    rationale: str = Field(description="判定理由与事实陈述")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="法官自评置信度")
    model_name: str | None = Field(default=None, description="裁判模型标识；不包含凭证")


class RubricDispute(BaseModel):
    """陪审团内部对某条 Rubric 产生的裁决分歧记录 (触发辩论协议)"""

    model_config = ConfigDict(frozen=True)

    rubric_id: str = Field(description="产生分歧的 Rubric ID")
    conflicting_judgments: list[RubricJudgment] = Field(
        description="所有产生冲突的法官盲审判决列表"
    )
    debate_rounds: int = Field(default=0, description="已经历的辩论轮次数")
    final_consensus_verdict: BinaryVerdict | None = Field(
        default=None, description="合议庭最终收敛裁决"
    )
    moderator_verdict_rationale: str = Field(default="", description="合议庭首席裁决仲裁理由")
    moderator_evidence_span_ids: list[str] = Field(
        default_factory=list, description="仲裁引用的原始执行 Span"
    )
