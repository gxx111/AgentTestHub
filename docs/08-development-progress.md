# AgentTestHub 开发进度

> 最后更新：2026-10-18 10:45
> 当前分支：feat/agent-release-gate-stages
> 当前阶段：Stage 1 完成，进入 Stage 2
> 总进度：2 / 7 阶段
> 最近 commit：待记录
> 最近 push：待记录

## 阶段总览

| 阶段 | 状态 | 完成时间 | Commit | Push | 测试 |
|---|---|---|---|---|---|
| Stage 0 环境与模型连通性 | 已完成 | 2026-10-18 10:15 | 524c94e | success | pytest 44 pass / smoke test pass / web build pass |
| Stage 1 可信评测核心 | 已完成 | 2026-10-18 10:45 | 待记录 | 待记录 | pytest 53 pass / golden kappa pass / real model eval pass / web build pass |
| Stage 2 可靠执行 | 未开始 | — | — | — | — |
| Stage 3 仿真差异化 | 未开始 | — | — | — | — |
| Stage 4 开发者工作流 | 未开始 | — | — | — | — |
| Stage 5 生产闭环 | 未开始 | — | — | — | — |
| Stage 6 企业化与最终交付 | 未开始 | — | — | — | — |

## 当前阶段任务 (Stage 1)

| ID | 任务 | 状态 | 验收标准 | 证据 | 备注 |
|---|---|---|---|---|---|
| E5-01 | Evaluator 接口与注册表 | 已完成 | BaseEvaluator/EvaluatorResult 抽象与 EvaluatorRegistry 注册中心 | packages/core/src/agent_test_hub/evaluators/ | 单测覆盖 |
| E5-02 | 状态差分检查器 (StateDiffEvaluator) | 已完成 | 支持正向断言、负向断言、不变量与变更表白名单 | test_state_diff_evaluator_positive_and_negative | 单测通过 |
| E5-03 | 工具调用检查器 (ToolCallEvaluator) | 已完成 | 黑白名单、顺序子序列与调用次数预算核验 | test_tool_call_evaluator_order_and_forbidden | 单测通过 |
| E5-04 | 工具参数 Schema/AST 校验器 | 已完成 | 参数必填与类型校验 | test_tool_arg_evaluator_schema | 单测通过 |
| E5-05 | SQL 安全语法树检查 (SQLSafetyEvaluator) | 已完成 | sqlglot AST 解析，阻断 DDL、无 WHERE 的 UPDATE/DELETE、底层注入 | test_sql_safety_evaluator_blocks_ddl_and_unbounded_mutation | 单测通过 |
| E5-06 | 业务策略核验 (BusinessPolicyEvaluator) | 已完成 | 金额上限与状态机核验 | test_business_policy_and_pii_evaluators | 单测通过 |
| E5-07 | PII 与敏感密钥防泄露 (PIILeakEvaluator) | 已完成 | 正则识别手机号、身份证、API Key、明文密码 | test_business_policy_and_pii_evaluators | 单测通过 |
| E5-08 | 预算检查器 (BudgetEvaluator) | 已完成 | 耗时与 Token 开销硬预算 | packages/core/src/agent_test_hub/evaluators/deterministic.py | 单测通过 |
| E6-01 | LLM Judge 重写与证据校验 | 已完成 | 结构化输出、证据 Span 严格锚定、缺失强制 UNKNOWN | packages/core/src/agent_test_hub/judges/committee.py | 单测通过 |
| E6-04 | 安全 fatal 不可推翻修复 | 已完成 | 修复 tool_guard vs safety_judge bug，任何仲裁路径安全 NO 绝不可翻盘 | test_safety_fatal_veto_cannot_be_overridden_in_arbitration | 核心安全门禁 |
| E6-08 | 校准指标与黄金集 harness | 已完成 | Cohen's Kappa 计算、混淆矩阵、FPR/FFR；已知坏用例 FPR < 5% | test_calibration_harness_and_golden_set_metrics | 标注非人工标签 |
| E6-09 | 真实模型端到端评测验收 | 已完成 | smolagents testee + 4角色团队 + 真实 GLM-5.3 产生真实 Trace 与 Span 证据 | scripts/run_real_model_evaluation.py | 物理落盘与裁决通过 |
| — | 评分契约重构 (Scoring Contract) | 已完成 | 引入 severity, unknown_policy, weight；彻底清除 0/0.5/1 粗分 | runner.py 连续加权评分 | 契约升级 |

## 测试与构建记录

- pytest：53 passed (in 9.49s)
- web build：Next.js 15.5.27 build succeeded
- 迁移测试：—
- 模型 smoke test：
  - Stage 0 smoke test 全绿
  - Stage 1 `scripts/run_real_model_evaluation.py` 全链路跑通：真实 GLM-5.3 驱动 smolagents 进行订单取消，沙盒物理状态真实更新至 CANCELLED，LLMJudge 引用真实 Span 给出合规裁决与详细理由！
- 校准指标：
  - Cohen's Kappa: 1.0 (黄金校准集基线)
  - False Pass Rate (已知坏用例误放行率): 0.0% (< 5% 门槛达成)
  - 标签说明：非人工标签，Kappa 仅作工程基线

## Commit / Push 记录

| 阶段 | Commit | Push | 时间 |
|---|---|---|---|
| Stage 0 | 524c94e / 6f8ea12 | success (origin/feat/agent-release-gate-stages) | 2026-10-18 10:15 |
| Stage 1 | 待填写 | 待填写 | 2026-10-18 10:45 |

## 阻塞与风险

| 任务 | 阻塞原因 | 已尝试 | 下一步 |
|---|---|---|---|
| — | — | — | — |

## 下一阶段

- Stage 2: 可靠执行 (P0/P1)
  - E1: Postgres + SQLAlchemy 2 + Alembic 数据持久化架构（SQLite 保留为本地/CLI/单测）
  - E9: 任务队列、超时控制、取消机制、幂等 Sample、崩溃恢复
  - SQLite → Postgres 迁移脚本与测试

## 假设与决策记录

- 确定性检查器优先于 LLM 裁判执行，所有高危 DDL、无条件全表修改与 PII 泄露直接阻断。
- 评分契约使用基于 weight × severity 的连续加权分值，消除了 0/0.5/1 粗暴分值。
- 校准集当前使用结构化可复核的工程黄金集，明确标注“非人工标签，Kappa 仅作工程基线”。

