# AgentTestHub 开发进度

> 最后更新：2026-10-18 11:10
> 当前分支：feat/agent-release-gate-stages
> 当前阶段：Stage 2 完成，进入 Stage 3
> 总进度：3 / 7 阶段
> 最近 commit：57cbe8a
> 最近 push：origin/feat/agent-release-gate-stages (success)

## 阶段总览

| 阶段 | 状态 | 完成时间 | Commit | Push | 测试 |
|---|---|---|---|---|---|
| Stage 0 环境与模型连通性 | 已完成 | 2026-10-18 10:15 | 524c94e | success | pytest 44 pass / smoke test pass / web build pass |
| Stage 1 可信评测核心 | 已完成 | 2026-10-18 10:45 | da082f3 | success | pytest 53 pass / golden kappa pass / real model eval pass / web build pass |
| Stage 2 可靠执行 | 已完成 | 2026-10-18 11:10 | 57cbe8a | success | pytest 63 pass / alembic head+base pass / queue & cancel pass / web build pass |
| Stage 3 仿真差异化 | 未开始 | — | — | — | — |
| Stage 4 开发者工作流 | 未开始 | — | — | — | — |
| Stage 5 生产闭环 | 未开始 | — | — | — | — |
| Stage 6 企业化与最终交付 | 未开始 | — | — | — | — |

## 当前阶段任务 (Stage 2)

| ID | 任务 | 状态 | 验收标准 | 证据 | 备注 |
|---|---|---|---|---|---|
| E1-01 | 建立 packages/domain | 已完成 | 实体、值对象、错误、事件分层清晰 | packages/domain/src/agent_test_hub_domain/ | 独立包架构 |
| E1-02 | ID/版本/内容哈希规范 | 已完成 | 规范化 ID 生成与 SHA-256 Canonical JSON 不可变内容哈希 | agent_test_hub_domain/ids.py | 单测覆盖 |
| E1-03 | SQLAlchemy 2 + Alembic 迁移 | 已完成 | alembic upgrade head 空库建表，downgrade base 干净回滚 | test_alembic_upgrade_head_and_downgrade_on_empty_db | 14张核心表全量支持 |
| E1-04~12 | 核心领域表完整定义 | 已完成 | workspaces, projects, agents, datasets, cases, experiments, runs, samples, verdicts, audit_logs | agent_test_hub_domain/models.py | ORM 关系级联健全 |
| E1-13 | SQLite → Postgres 迁移脚本 | 已完成 | 读取旧库表并注入新版本化模型，校验行数与哈希，支持 dry-run | scripts/migrate_sqlite_to_postgres.py, test_legacy_sqlite_migration | 演练与真实迁移通过 |
| E1-14 | 仓储层 Repository 抽象 | 已完成 | WorkspaceRepo, AgentRepo, DatasetRepo, ExperimentRepo, AuditRepo 事务边界封装 | agent_test_hub_domain/repository.py | 杜绝上层裸 SQL |
| E1-15 | 多租户隔离自动化测试 | 已完成 | 跨租户访问抛出 TenantAccessDeniedError (404 语义隔离) | test_multi_tenant_isolation_raises_access_denied | 安全隔离达成 |
| E9-02 | 超时熔断与重试机制 | 已完成 | 超过 timeout_seconds 自动熔断并执行可配置重试 | test_timeout_and_retry_mechanism | 队列自动调度 |
| E9-05 | 幂等 Sample 执行 | 已完成 | 基于 run_id:case_id:index 生成 sample_key，重复写入直接幂等返回 | test_experiment_idempotency_and_cancellation | 杜绝重复计分 |
| E9-07 | 实验取消机制 | 已完成 | 支持实时取消运行中的实验，排队与运行任务置为 CANCELLED | test_experiment_cancellation_in_queue | 即时生效 |
| E9-10 | 崩溃恢复机制 | 已完成 | 恢复挂起的 running/pending 任务为重新调度状态 | test_crash_recovery | 崩溃安全恢复 |

## 测试与构建记录

- pytest：63 passed (in 9.52s)
- web build：Next.js 15.5.27 build succeeded
- 迁移测试：`test_alembic_upgrade_head_and_downgrade_on_empty_db` (upgrade head -> 14张表建立成功 -> downgrade base 干净回滚 -> 再次 upgrade 成功)
- 旧库迁移测试：`test_legacy_sqlite_migration` (dry_run 模式回滚成功，真实迁移数据行数与版本映射完整)
- 队列与并发测试：`test_job_queue_enqueue_dequeue`, `test_timeout_and_retry_mechanism`, `test_experiment_cancellation_in_queue`, `test_crash_recovery` 全部通过

## Commit / Push 记录

| 阶段 | Commit | Push | 时间 |
|---|---|---|---|
| Stage 0 | 524c94e / 6f8ea12 | success (origin/feat/agent-release-gate-stages) | 2026-10-18 10:15 |
| Stage 1 | da082f3 / ad5231f | success (origin/feat/agent-release-gate-stages) | 2026-10-18 10:45 |
| Stage 2 | 57cbe8a | success (origin/feat/agent-release-gate-stages) | 2026-10-18 11:10 |

## 阻塞与风险

| 任务 | 阻塞原因 | 已尝试 | 下一步 |
|---|---|---|---|
| — | — | — | — |

## 下一阶段

- Stage 3: 仿真差异化 (P1)
  - E7: Docker 沙盒驱动接口、只读 rootfs、非 root、快照与回滚、故障注入引擎 (网络拒绝/延迟/错误)
  - E8: 双控用户模拟器 + 红队攻击库 (提示注入/工具越权/MCP投毒)
  - 2 个垂直业务场景包 (如金融电商核验与企业运维)

## 假设与决策记录

- 引入 SQLAlchemy 2 + Alembic 作为通用数据库持久化基座，PostgreSQL 用于生产与多租户 SaaS，SQLite 保留用于本地极速单测与 CLI 独立运行。
- Sample 执行使用唯一的 `sample_key` (`run_id:case_id:sample_index`) 强一致性约束，杜绝分布式或重试并发下的重复计分。


