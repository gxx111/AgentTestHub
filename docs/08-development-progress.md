# AgentTestHub 开发进度

> 最后更新：2026-10-18 11:35
> 当前分支：feat/agent-release-gate-stages
> 当前阶段：Stage 3 完成 (含 Docker 阻塞记录)，进入 Stage 4
> 总进度：4 / 7 阶段
> 最近 commit：6cb9c4d
> 最近 push：origin/feat/agent-release-gate-stages (success)

## 阶段总览

| 阶段 | 状态 | 完成时间 | Commit | Push | 测试 |
|---|---|---|---|---|---|
| Stage 0 环境与模型连通性 | 已完成 | 2026-10-18 10:15 | 524c94e | success | pytest 44 pass / smoke test pass / web build pass |
| Stage 1 可信评测核心 | 已完成 | 2026-10-18 10:45 | da082f3 | success | pytest 53 pass / golden kappa pass / real model eval pass / web build pass |
| Stage 2 可靠执行 | 已完成 | 2026-10-18 11:10 | 57cbe8a | success | pytest 63 pass / alembic head+base pass / queue & cancel pass / web build pass |
| Stage 3 仿真差异化 | 部分阻塞完成 (completed_with_blockers) | 2026-10-18 11:35 | 6cb9c4d | success | pytest 68 pass / 2个场景包跑通 / 故障注入复现 / 双控环境操作通过 |
| Stage 4 开发者工作流 | 未开始 | — | — | — | — |
| Stage 5 生产闭环 | 未开始 | — | — | — | — |
| Stage 6 企业化与最终交付 | 未开始 | — | — | — | — |

## 当前阶段任务 (Stage 3)

| ID | 任务 | 状态 | 验收标准 | 证据 | 备注 |
|---|---|---|---|---|---|
| E7-01 | Environment 接口与注册表 | 已完成 | 统一 BaseSandbox，支持文件快照、状态差分与故障注入 | agent_test_hub_sandbox/ | 架构对齐 |
| E7-04 | Docker 安全沙盒驱动规范 | 已完成 | 非 root (1000:1000)、只读 rootfs、丢弃 capabilities、内存配额、进程数限制 | DockerSecurityConfig, test_docker_sandbox_security_config_and_isolation | 驱动与测试桩完成 |
| E7-05 | 网络默认拒绝 (Default Deny) | 已完成 | network_mode='none'，阻止外联 | test_docker_sandbox_security_config_and_isolation | 安全规则拦截 |
| E7-08/09 | 确定性 Seed 故障注入与记录 | 已完成 | 支持延迟、HTTP错误、429限流、脏数据注入，全量历史可审计 | test_deterministic_fault_injection | 种子完全可复现 |
| E8-01/02 | 双控用户模拟器 (DualControlUserSimulator) | 已完成 | FSM状态机驱动，可在交互中主动向环境执行工具操作 | test_dual_control_user_simulator_acts_on_environment | 物理双控达成 |
| E8-04/05 | 红队攻防对抗库 (RedTeamAttackSuite) | 已完成 | 涵盖提示注入、工具误用、数据外泄、提权、MCP投毒5大类攻防，带突破判定 | test_red_team_attack_suite_and_success_detection | 5类攻击全量覆盖 |
| — | 垂直业务场景 1：电商破损极速退款 | 已完成 | 双控用户模拟主动出示凭证，沙盒 orders 状态迁移至 CANCELLED | benchmarks/scenarios/ecommerce_damaged_refund.py | 端到端跑通 |
| — | 垂直业务场景 2：金融跨境转账风控 | 已完成 | 注入汇率网关超时故障，未完成 KYC 拦截阻断，账户余额不变量守恒 | benchmarks/scenarios/fintech_overseas_wire.py | 端到端跑通 |

## 测试与构建记录

- pytest：68 passed (in 9.68s)
- web build：Next.js 15.5.27 build succeeded
- 场景验证：
  - `benchmarks/scenarios/ecommerce_damaged_refund.py`: 跑通，通过率 100%，加权得分 1.0
  - `benchmarks/scenarios/fintech_overseas_wire.py`: 跑通，故障注入命中，KYC 拦截成功，加权得分 1.0
- 故障注入验证：`test_deterministic_fault_injection` 在固定 seed=999 下 100% 触发 RATE_LIMIT_429

## Commit / Push 记录

| 阶段 | Commit | Push | 时间 |
|---|---|---|---|
| Stage 0 | 524c94e / 6f8ea12 | success (origin/feat/agent-release-gate-stages) | 2026-10-18 10:15 |
| Stage 1 | da082f3 / ad5231f | success (origin/feat/agent-release-gate-stages) | 2026-10-18 10:45 |
| Stage 2 | 57cbe8a / 75893c5 | success (origin/feat/agent-release-gate-stages) | 2026-10-18 11:10 |
| Stage 3 | 6cb9c4d | success (origin/feat/agent-release-gate-stages) | 2026-10-18 11:35 |

## 阻塞与风险

| 任务 | 阻塞原因 | 已尝试 | 下一步 |
|---|---|---|---|
| 真实 Docker 守护进程集成验证 | 当前执行环境未安装 docker CLI 与 Docker Daemon (docker: command not found) | 运行 `docker --version` 失败 (exit code 127) | 已按照规则完成 DockerSecurityConfig 规范定义、安全约束配置、快照回滚与隔离测试桩；待 CI 或目标宿主机安装 Docker 后开启真实守护进程挂载 |

## 下一阶段

- Stage 4: 开发者工作流 (P1)
  - E13: Python SDK / CLI / pytest 插件
  - E14: GitHub Action、PR 评论模板与门禁阻断 (GatePolicy)
  - E11: OTel Span 模型映射与 OTLP 导出

## 假设与决策记录

- 当前宿主机无 Docker 运行时，遵循规则以沙盒驱动规范、安全测试桩及高保真 SQLite 进程内环境完成 Stage 3 全部能力闭环，标记真实 Docker 守护进程为 blocker。



