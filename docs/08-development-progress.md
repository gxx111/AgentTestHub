# AgentTestHub 开发进度

> 最后更新：2026-10-18 11:55
> 当前分支：feat/agent-release-gate-stages
> 当前阶段：Stage 4 完成，进入 Stage 5
> 总进度：5 / 7 阶段
> 最近 commit：待记录
> 最近 push：待记录

## 阶段总览

| 阶段 | 状态 | 完成时间 | Commit | Push | 测试 |
|---|---|---|---|---|---|
| Stage 0 环境与模型连通性 | 已完成 | 2026-10-18 10:15 | 524c94e | success | pytest 44 pass / smoke test pass / web build pass |
| Stage 1 可信评测核心 | 已完成 | 2026-10-18 10:45 | da082f3 | success | pytest 53 pass / golden kappa pass / real model eval pass / web build pass |
| Stage 2 可靠执行 | 已完成 | 2026-10-18 11:10 | 57cbe8a | success | pytest 63 pass / alembic head+base pass / queue & cancel pass / web build pass |
| Stage 3 仿真差异化 | 部分阻塞完成 (completed_with_blockers) | 2026-10-18 11:35 | 6cb9c4d | success | pytest 68 pass / 2个场景包跑通 / 故障注入复现 / 双控环境操作通过 |
| Stage 4 开发者工作流 | 已完成 | 2026-10-18 11:55 | 待记录 | 待记录 | pytest 73 pass / SDK本地评测 / 门禁阻断与PR评论 / OTel导出 / web build pass |
| Stage 5 生产闭环 | 未开始 | — | — | — | — |
| Stage 6 企业化与最终交付 | 未开始 | — | — | — | — |

## 当前阶段任务 (Stage 4)

| ID | 任务 | 状态 | 验收标准 | 证据 | 备注 |
|---|---|---|---|---|---|
| E13-01 | Python SDK (AgentTestHubClient) | 已完成 | 封装本地/远端评测调用、门禁判定与结果对象 | agent_test_hub_sdk/client.py | 10分钟快速接入 |
| E13-02 | ath CLI 命令行工具链 | 已完成 | ath init, ath eval, ath gate 完整支持，退出码准确 (0=通过, 1=门禁拦截) | agent_test_hub_cli/main.py, test_ath_cli_commands | CLI测试全通过 |
| E13-03 | pytest 插件与门禁断言辅助函数 | 已完成 | assert_gate_passed, assert_sql_safety, assert_no_pii_leaked 及 fixture | agent_test_hub_sdk/pytest_plugin.py | 报错含详细报告 |
| E13-04/05 | 本地运行模式与远端调度适配 | 已完成 | 本地无需启动服务端即可评测，远端支持 HTTP API | test_sdk_local_evaluation_and_gate_check | 双模支持 |
| E14-01/02 | ReleaseGate 门禁策略与决策引擎 | 已完成 | 综合通过率、均分、一票否决与耗时判定 PASS/BLOCK | agent_test_hub_domain/gate.py, test_ci_gate_blocking_and_pr_comment | 规则严谨 |
| E14-03/04 | GitHub Action 与 PR 评论 Markdown 模板 | 已完成 | 自动化门禁工作流定义，输出直观 Markdown 评审看板 | .github/workflows/agent-eval-gate.yml, ReleaseGateEvaluator | CI就绪 |
| E14-05 | JUnit XML 测试报表输出 | 已完成 | 生成符合标准 testsuite/testcase/failure 规范的 XML 报表 | ReleaseGateEvaluator._render_junit_xml | 兼容 CI 渲染 |
| E11-01~05 | OTel GenAI 标准 Trace 导出与脱敏 | 已完成 | 符合 OpenInference / OTel GenAI 语义约定，自动脱敏手机号、身份证、密钥、密码 | agent_test_hub/telemetry/, test_otel_span_exporter_and_sanitization | 兼容 Jaeger/Tempo |
| — | 3 个框架适配器 | 已完成 | SmolagentsAdapter, LangChainAdapter, OpenAICompatAdapter | agent_test_hub_sdk/adapters.py, test_framework_adapters | 主流框架兼容 |

## 测试与构建记录

- pytest：73 passed (in 9.87s)
- web build：Next.js 15.5.27 build succeeded
- 门禁阻断验证：`test_ci_gate_blocking_and_pr_comment` 验证未达标用例 100% 触发 BLOCK 决策，输出阻断原因与 JUnit XML
- OTel 导出验证：`test_otel_span_exporter_and_sanitization` 成功导出符合 OpenTelemetry GenAI 规范的 spans，且脱敏机制生效
- 命令行验证：`test_ath_cli_commands` 成功执行 `ath init`, `ath eval`, `ath gate`

## Commit / Push 记录

| 阶段 | Commit | Push | 时间 |
|---|---|---|---|
| Stage 0 | 524c94e / 6f8ea12 | success (origin/feat/agent-release-gate-stages) | 2026-10-18 10:15 |
| Stage 1 | da082f3 / ad5231f | success (origin/feat/agent-release-gate-stages) | 2026-10-18 10:45 |
| Stage 2 | 57cbe8a / 75893c5 | success (origin/feat/agent-release-gate-stages) | 2026-10-18 11:10 |
| Stage 3 | 6cb9c4d / cf68079 | success (origin/feat/agent-release-gate-stages) | 2026-10-18 11:35 |
| Stage 4 | 待填写 | 待填写 | 2026-10-18 11:55 |

## 阻塞与风险

| 任务 | 阻塞原因 | 已尝试 | 下一步 |
|---|---|---|---|
| 真实 Docker 守护进程集成验证 (Stage 3 遗留) | 当前执行环境未安装 docker CLI 与 Docker Daemon | 运行 `docker --version` 失败 (exit code 127) | 保持测试桩验证；CI/生产环境有 Docker 时直接切换 |

## 下一阶段

- Stage 5: 生产闭环 (P2)
  - E15: 生产 Trace 在线监控、智能采样 (Sampling)、异常告警、Trace 自动回流沉淀为用例数据集 (Trace -> Dataset)
  - E16: 人工标注队列与争议仲裁、双人盲审一致性校验、校准集持续回流

## 假设与决策记录

- 发布门禁 CLI (ath) 默认集成 GatePolicy，阻断时返回 exit code 1，与各类 CI/CD (GitHub Actions, GitLab CI, Jenkins) 原生契合。
- OTel 导出器默认执行双向隐私脱敏，避免真实生产凭证或客户隐私泄露至追踪存储后端。




