# AgentTestHub 开发进度

> 最后更新：2026-10-18 10:15
> 当前分支：feat/agent-release-gate-stages
> 当前阶段：Stage 0 完成，进入 Stage 1
> 总进度：1 / 7 阶段
> 最近 commit：待记录
> 最近 push：待记录

## 阶段总览

| 阶段 | 状态 | 完成时间 | Commit | Push | 测试 |
|---|---|---|---|---|---|
| Stage 0 环境与模型连通性 | 已完成 | 2026-10-18 10:15 | 待记录 | 待记录 | pytest 44 pass / smoke test pass / web build pass |
| Stage 1 可信评测核心 | 未开始 | — | — | — | — |
| Stage 2 可靠执行 | 未开始 | — | — | — | — |
| Stage 3 仿真差异化 | 未开始 | — | — | — | — |
| Stage 4 开发者工作流 | 未开始 | — | — | — | — |
| Stage 5 生产闭环 | 未开始 | — | — | — | — |
| Stage 6 企业化与最终交付 | 未开始 | — | — | — | — |

## 当前阶段任务 (Stage 0)

| ID | 任务 | 状态 | 验收标准 | 证据 | 备注 |
|---|---|---|---|---|---|
| S0-01 | 环境变量配置与密钥隔离 | 已完成 | .env.local 写入模型配置且被 .gitignore 忽略 | git check-ignore 确认命中第 68 行 | 密钥隔离成功，无提交泄露风险 |
| S0-02 | 模型连通性 smoke test 脚本 | 已完成 | 调用 Chat/Completions 成功，输出延迟，脱敏密钥 | scripts/smoke_test_model.py 运行通过，延迟 3533.9ms | 使用 GLM-5.3 |
| S0-03 | 4 角色评测团队配置验证 | 已完成 | user_simulator, business_judge, safety_judge, moderator 全部成功初始化并能协同 | 4 角色并发就绪测试全部 200 OK | 统一配置与系统提示词 |
| S0-04 | smolagents 被测 Agent 工具调用验证 | 已完成 | ToolCallingAgent 可调用 db_execute 等测试工具 | smolagents.ToolCallingAgent 成功调用 db_execute 并产生最终回答 | 原生支持 Tool Calling，无需降级 |

## 测试与构建记录

- pytest：44 passed (in 16.96s)
- web build：Next.js 15.5.27 build succeeded (11/11 static pages generated)
- 迁移测试：—
- 模型 smoke test：`scripts/smoke_test_model.py` 全绿通过：
  - Step 1: Model Connectivity (GLM-5.3) -> 200 OK (3533.9ms)
  - Step 2: 4-Role Team -> 4 角色全部通过 (user_simulator: 3488.1ms, business_judge: 4199.6ms, safety_judge: 5975.9ms, moderator: 4056.7ms)
  - Step 3: smolagents ToolCallingAgent -> Tool 'db_execute' 调用成功并在 2 步内输出最终答案 (12914.2ms)
- 其他：已确认 GLM-5.3 输出带有 reasoning_content，max_tokens 设置需预留充足预算（推荐 >= 1000）。

## Commit / Push 记录

| 阶段 | Commit | Push | 时间 |
|---|---|---|---|
| Stage 0 | 待填写 | 待填写 | 2026-10-18 10:15 |

## 阻塞与风险

| 任务 | 阻塞原因 | 已尝试 | 下一步 |
|---|---|---|---|
| — | — | — | — |

## 下一阶段

- Stage 1: 可信评测核心 (P0)
  - E5 确定性 Evaluator：状态差分、工具 Schema/AST、SQL 安全（sqlglot）、PII、策略检查
  - E6 LLM/Agent Judge 与校准：证据校验、UNKNOWN、多模型评审团、Kappa 黄金集、安全 fatal 不可推翻
  - 评分契约：weight / severity / unknown_policy / fatal，彻底删除 0/0.5/1 粗分
  - 修复安全否决与仲裁 bug

## 假设与决策记录

- GLM-5.3 具备 reasoning_content 思维链输出，token 预算设定需考虑思考阶段消耗。
- 网关具备标准 OpenAI Function Calling 能力，smolagents ToolCallingAgent 运行正常。
