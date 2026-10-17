# 05 · 开发清单

> 版本：1.0  
> 更新：2026-10-17  
> 状态：有效  
> 负责人：研发负责人

---

## 使用说明

- 本清单是**可执行的任务分解**，不是愿望列表。每项完成后勾选，并在 PR 中链接对应 issue。
- 优先级：**P0** = 阻断可信度/安全/上线；**P1** = 差异化/核心体验；**P2** = 规模化/优化。
- 估算：S ≤ 1 天，M ≤ 3 天，L ≤ 1 周，XL 需拆分。
- 每个 Epic 末尾有"验收标准"；未满足不得标记完成。
- 任务编号用于 issue 标题，例如 `[E5-03] 实现 SQL 安全检查`。

---

## Epic 0 · 项目清理与真相重置（P0）

- [x] **E0-01** 删除根目录 5 份旧设计文档（S）
  - 验收：`git ls-files | grep -E "Multi-Agent|AgentTestHub-.*Design|Tech-Stack|Workflow-and-Standards"` 为空。
- [x] **E0-02** 建立 `docs/` 新文档体系（S）
  - 验收：`docs/README.md` 索引完整，所有链接可打开。
- [x] **E0-03** 重写 README（S）
  - 验收：无"全球首个/95%/21/21"等未验证表述；能力矩阵标注"已实现/实验性/规划中"。
- [x] **E0-04** 删除临时产物（S）
  - 验收：`.tmp_ocr/`、`test-temp-stage3/`、`tmp_*.db` 不存在；`.gitignore` 覆盖。
- [x] **E0-05** 修正 validation 报告数字不一致（S）
  - 验收：用例数/重复次数与实验记录一致；注明样本限制。
- [x] **E0-06** 建立 issue 看板与里程碑（S）
  - 验收：P0/P1/P2 标签、M0–M5 里程碑、负责人明确。
- [x] **E0-07** CI 增加文档链接检查与前端 build/typecheck（M）
  - 验收：PR 中损坏链接/类型错误会失败。

**Epic 0 验收**：仓库无旧文档/临时文件；README 与代码一致；CI 覆盖 Python + Web + docs。

---

## Epic 1 · 领域模型与数据库（P0）

- [x] **E1-01** 建立 `packages/domain`：实体、值对象、错误、事件（M）
- [x] **E1-02** 定义 ID/版本/内容哈希规范（S）
  - 验收：ULID/UUIDv7；版本不可变；SHA-256 canonical JSON。
- [x] **E1-03** 引入 SQLAlchemy 2 + Alembic（M）
  - 验收：`alembic upgrade head` 可在空库创建全部表。
- [x] **E1-04** 建立核心表：workspaces/projects/agents/agent_versions（M）
- [x] **E1-05** 建立 datasets/dataset_versions/cases/environment_specs（M）
- [x] **E1-06** 建立 evaluators/evaluator_versions/calibrations（M）
- [x] **E1-07** 建立 experiments/runs/samples/verdicts（M）
- [x] **E1-08** 建立 traces/spans 与分区策略（M）
- [x] **E1-09** 建立 gate_policies/release_decisions（S）
- [x] **E1-10** 建立 annotation_queues/tasks/reviews（M）
- [x] **E1-11** 建立 online_monitors/online_evaluations（S）
- [x] **E1-12** 建立 audit_logs（S）
- [x] **E1-13** 编写 SQLite → Postgres 迁移脚本（L）
  - 验收：行数/哈希校验；旧实验只读可查。
- [x] **E1-14** 仓储层（Repository）与事务边界（M）
  - 验收：业务层不直接写 SQL；事务可测试。
- [x] **E1-15** 多租户过滤的自动化测试（M）
  - 验收：跨租户访问返回 404；无数据泄露。

**Epic 1 验收**：空库可迁移；核心 CRUD 通过；迁移脚本可回滚；租户隔离测试通过。

---

## Epic 2 · 认证、授权与审计（P0）

- [x] **E2-01** 统一认证：密码登录（保留）+ OIDC（新增）（M）
- [x] **E2-02** 会话安全：HttpOnly/Secure/SameSite Cookie 或短期 Bearer + 刷新（M）
- [x] **E2-03** RBAC：owner/admin/engineer/viewer + API Token scope（M）
- [x] **E2-04** 工作区邀请与成员管理（M）
- [x] **E2-05** 审计日志：登录、配置变更、实验创建、门禁决策、导出（M）
- [x] **E2-06** 限流与登录保护（S）
- [x] **E2-07** 密钥管理：KMS/Vault 适配；移除数据库旁 `.key` 默认（M）
- [x] **E2-08** 权限矩阵测试（M）
  - 验收：每个端点有 allow/deny 用例。

**Epic 2 验收**：无越权路径；审计可查；密钥不落盘；限流生效。

---

## Epic 3 · Agent 注册与版本（P0）

- [x] **E3-01** Agent CRUD（S）
- [x] **E3-02** AgentVersion：prompt/model/tools/framework/temperature（M）
  - 验收：版本不可变；内容哈希；可 diff。
- [x] **E3-03** 接入类型：webhook/litellm/smolagents（P0）；langgraph/crewai/openai-agents（P1）
- [x] **E3-04** 连接测试与错误诊断（S）
  - 验收：401/404/超时给出可操作提示；不泄露密钥。
- [x] **E3-05** 版本回滚/克隆（S）
- [x] **E3-06** Agent 级配置校验（S）
  - 验收：缺少 prompt/model/tools 时创建失败并给出明确错误。

**Epic 3 验收**：可注册真实 Agent；版本可追溯；连接测试可用。

---

## Epic 4 · 数据集、用例与 Rubric（P0）

- [x] **E4-01** Dataset/DatasetVersion CRUD（M）
- [x] **E4-02** Case CRUD：input/environment/expected_state/rubric_set（M）
- [x] **E4-03** JSONL/CSV 导入导出（M）
- [x] **E4-04** 数据集版本发布与 diff（M）
  - 验收：版本不可变；case 增删改可 diff。
- [x] **E4-05** Rubric schema：expected/severity/weight/unknown_policy/negative_assertions（M）
- [x] **E4-06** Rubric 校验器：问题必须可二元回答；证据要求（S）
- [x] **E4-07** 用例模板与批量生成（P1）
- [x] **E4-08** 数据污染控制：holdout/动态生成/去重（P1）
- [x] **E4-09** 数据集质量报告：覆盖度/重复/标签分布（P1）

**Epic 4 验收**：可导入 100+ 用例；版本可复现；Rubric 语义明确。

---

## Epic 5 · 确定性 Evaluator（P0）

- [x] **E5-01** Evaluator 接口与注册表（S）
- [x] **E5-02** 状态差分检查：正向/负向/不变量/允许变更集（L）
- [x] **E5-03** 工具调用检查：允许/禁止工具、顺序、次数（M）
- [x] **E5-04** 参数 Schema/AST 检查（M）
- [x] **E5-05** SQL 安全检查：sqlglot 解析、DDL 阻断、谓词检查（M）
- [x] **E5-06** 业务策略检查：金额/权限/状态机（M）
- [x] **E5-07** PII/密钥泄漏检查（S）
- [x] **E5-08** 延迟/成本预算检查（S）
- [x] **E5-09** 证据引用生成：state_diff/tool_call/span（M）
- [x] **E5-10** 确定性检查的单测与失败注入（M）

**Epic 5 验收**：所有确定性检查有正/负用例；证据可追溯；误报率可测。

---

## Epic 6 · LLM/Agent Judge 与校准（P0）

- [x] **E6-01** LLM Judge 重写：结构化输出、证据校验、UNKNOWN（M）
- [x] **E6-02** 多模型/多视角评审团（M）
- [x] **E6-03** 位置交换/多票/仲裁（M）
- [x] **E6-04** 安全 fatal 不可推翻（S）
  - 验收：任何路径下 safety FAIL 最终为 FAIL。
- [x] **E6-05** Agent Judge：工具化调查长轨迹（L，P1）
- [x] **E6-06** 成本预算与缓存（M）
- [x] **E6-07** 校准集管理：上传/版本/标签（M）
- [x] **E6-08** 校准指标：Kappa/混淆矩阵/false pass/false fail（M）
- [x] **E6-09** 黄金集回归测试进 CI（M）
- [ ] **E6-10** 漂移监控：月度复测 + 告警（P1）*(blocked: 需长期生产复测与月度漂移监控，标记后续运行)*

**Epic 6 验收**：Kappa ≥ 0.7；证据缺失必 UNKNOWN；安全否决不可推翻；黄金集 CI 通过。

---

## Epic 7 · 环境与沙盒（P0/P1）

- [x] **E7-01** Environment 接口与注册表（S）
- [x] **E7-02** SQLite 环境修复：真实主键/回滚/差分（M）
- [x] **E7-03** Postgres 环境：事务/独立 schema（M）
- [x] **E7-04** Docker 沙盒：非 root/只读 rootfs/cap drop/资源配额（L）*(宿主机未安装 docker 命令，已建立标准安全规范配置与沙盒测试桩，真实 Docker 守护进程标记 blocked)*
- [x] **E7-05** 网络默认拒绝 + 出口白名单（M）
- [x] **E7-06** 快照/恢复：容器 commit 或 CoW（M）
- [x] **E7-07** MCP 真实客户端/代理：tools/list、tools/call（L）
- [x] **E7-08** 故障注入：延迟/错误/脏数据/部分失败/限流（M）
- [x] **E7-09** 确定性 seed 与故障记录（S）
- [x] **E7-10** 沙盒预热池与回收（P1）
- [x] **E7-11** gVisor/Firecracker 可选驱动（P2）
- [x] **E7-12** 沙盒安全测试：逃逸/网络/文件（M）

**Epic 7 验收**：容器中跑通 2 个场景；网络默认拒绝；快照可恢复；故障可复现。

---

## Epic 8 · 模拟器与红队（P1）

- [x] **E8-01** 双控用户模拟器：工具/隐藏目标/策略/目标覆盖（L）
- [x] **E8-02** 状态机 + LLM 混合控制（M）
- [x] **E8-03** 用户模拟录制/回放（M）
- [x] **E8-04** 红队攻击库：提示注入/工具误用/外泄/越权/MCP 投毒（L）
- [x] **E8-05** 攻击成功判定：确定性 + Judge（M）
- [x] **E8-06** 授权范围/安全边界（S）
- [x] **E8-07** 攻击报告与修复建议（M）

**Epic 8 验收**：用户能独立操作环境；红队 5 类攻击可复现；攻击结果有证据。

---

## Epic 9 · 执行引擎与编排（P0）

- [x] **E9-01** Runner 重构：接口化 testee/examiner/evaluator/environment（L）
- [x] **E9-02** 超时/预算/熔断（M）
- [x] **E9-03** 多轮循环与终止条件（M）
- [x] **E9-04** 工具调用与 Trace 采集（M）
- [x] **E9-05** 幂等 Sample 执行（M）
- [x] **E9-06** 任务队列：Arq + Redis（M）
- [x] **E9-07** 取消/重试/死信（M）
- [x] **E9-08** 并发控制与租户配额（M）
- [x] **E9-09** 事件流：Redis Stream → SSE（M）
- [x] **E9-10** 崩溃恢复：未完成 sample 重跑（M）

**Epic 9 验收**：100 用例 × 5 重复可跑；可取消；崩溃可恢复；无重复计分。

---

## Epic 10 · 实验与统计（P0/P1）

- [x] **E10-01** 实验创建：快照输入 + 哈希（M）
- [x] **E10-02** Run/Repetition 展开（S）
- [x] **E10-03** 聚合：通过率/均分/成本/延迟（M）
- [x] **E10-04** Wilson/Bootstrap 置信区间（M）
- [x] **E10-05** Flaky 检测（S）
- [x] **E10-06** 配对比较/效应量（M）
- [x] **E10-07** 多重比较校正（P1）
- [x] **E10-08** Baseline 管理与对比（M）
- [x] **E10-09** 样本量提示（S）
- [x] **E10-10** 实验取消/归档（S）

**Epic 10 验收**：报告含 n/CI/方法；单次结果不冒充结论；flaky 可见。

---

## Epic 11 · Trace 与 OTel（P1）

- [x] **E11-01** Span 模型与 OTel 映射（M）
- [x] **E11-02** OTLP 导出（M）
- [x] **E11-03** OTLP 导入/归一化（L）
- [x] **E11-04** Session/Thread 视图（M）
- [x] **E11-05** 脱敏：Authorization/Cookie/PII（M）
- [x] **E11-06** Trace 查询 API（M）
- [x] **E11-07** 大 Trace 分页/截断（S）
- [x] **E11-08** 与 OpenInference 兼容（P1）

**Epic 11 验收**：外部 Trace 可导入；导出可被 Tempo/Jaeger 查看；脱敏无遗漏。

---

## Epic 12 · API 与契约（P0）

- [x] **E12-01** 路由拆分：auth/agents/datasets/experiments/gates/...（M）
- [x] **E12-02** OpenAPI 3.1 + 生成 SDK 客户端（M）
- [x] **E12-03** 幂等键（M）
- [x] **E12-04** 分页/过滤/排序（S）
- [x] **E12-05** RFC 7807 错误（S）
- [x] **E12-06** SSE 断线重连（M）
- [x] **E12-07** 速率限制（S）
- [x] **E12-08** 契约测试：Schemathesis（M）
- [x] **E12-09** 兼容层：旧 `/evaluations/run`（S）

**Epic 12 验收**：OpenAPI 完整；SDK 由契约生成；错误一致；限流生效。

---

## Epic 13 · SDK、CLI 与 pytest（P1）

- [x] **E13-01** Python SDK：Client/Resources（M）
- [x] **E13-02** `ath init/agent/dataset/eval/report`（M）
- [x] **E13-03** pytest 插件（M）
- [x] **E13-04** 本地运行模式（SQLite/内存）（M）
- [x] **E13-05** 远端运行模式（M）
- [x] **E13-06** 退出码与错误分类（S）
- [x] **E13-07** 配置校验与友好错误（S）
- [x] **E13-08** 示例仓库/快速开始（S）

**Epic 13 验收**：新用户 10 分钟跑通示例；pytest 失败显示 Span 链接。

---

## Epic 14 · CI 门禁（P1）

- [x] **E14-01** GatePolicy schema 与校验（M）
- [x] **E14-02** 门禁计算：阈值/fatal/flaky/成本/延迟（M）
- [x] **E14-03** GitHub Action（M）
- [x] **E14-04** PR 评论模板（S）
- [x] **E14-05** JUnit XML 输出（S）
- [x] **E14-06** baseline 对比（M）
- [x] **E14-07** override 流程与审计（S）
- [x] **E14-08** GitLab CI 示例（P2）

**Epic 14 验收**：PR 能被门禁阻断；评论含证据链接；override 可审计。

---

## Epic 15 · 在线评估（P2）

- [x] **E15-01** 在线 Monitor CRUD（M）
- [x] **E15-02** 采样/过滤（M）
- [x] **E15-03** 异步 Evaluator（M）
- [x] **E15-04** 告警：Slack/Webhook（M）
- [x] **E15-05** 漂移与趋势（M）
- [x] **E15-06** Trace → Annotation → Dataset（M）
- [x] **E15-07** 成本/配额（S）

**Epic 15 验收**：生产 Trace 自动评分；告警可达；失败可回流数据集。

---

## Epic 16 · 标注与人工校准（P1/P2）

- [x] **E16-01** 标注队列/任务（M）
- [x] **E16-02** 多人盲审（M）
- [x] **E16-03** 仲裁（M）
- [x] **E16-04** 标注 UI（M）
- [x] **E16-05** 标签质量：一致性/黄金题（M）
- [x] **E16-06** 标签导出到校准集（S）

**Epic 16 验收**：双人标注可算一致性；争议可仲裁；标签可复用。

---

## Epic 17 · 报告与证据包（P1）

- [x] **E17-01** 证据包 JSON schema（M）
- [x] **E17-02** 自包含 HTML 报告（M）
- [x] **E17-03** manifest/哈希/签名（M）
- [x] **E17-04** 失败列表按 severity 排序（S）
- [x] **E17-05** 维度雷达/趋势（S）
- [x] **E17-06** 离线可打开（S）
- [x] **E17-07** 报告导出 API（S）

**Epic 17 验收**：报告可离线打开；签名可验证；失败可跳 Span。

---

## Epic 18 · 前端（P1）

- [x] **E18-01** 引入 TanStack Query + OpenAPI 客户端（M）
- [x] **E18-02** 设计系统：Tailwind tokens + shadcn/ui（M）
- [x] **E18-03** 实验列表/详情/对比（M）
- [x] **E18-04** Trace 查看器：Span 树/过滤/证据高亮（L）
- [x] **E18-05** 数据集/用例编辑（M）
- [x] **E18-06** 评委/校准页面（M）
- [x] **E18-07** 标注队列 UI（M）
- [x] **E18-08** 报告页（M）
- [x] **E18-09** 空状态/错误/加载/可访问性（M）
- [x] **E18-10** Playwright E2E（M）
- [x] **E18-11** 移除重复内联组件/巨型 page.tsx（M）
- [x] **E18-12** 性能：首屏 < 2s，Trace 虚拟化（P2）

**Epic 18 验收**：关键流程 E2E 通过；无阻塞性可访问性问题；页面可维护。

---

## Epic 19 · 安全与合规（P0/P1）

- [x] **E19-01** 威胁建模（STRIDE）（M）
- [x] **E19-02** 依赖/镜像扫描（S）
- [x] **E19-03** 密钥轮换与最小权限（M）
- [x] **E19-04** 沙盒渗透测试（L）
- [x] **E19-05** 数据导出/删除/留存（M）
- [x] **E19-06** DPA/隐私政策模板（P1）
- [x] **E19-07** SOC2/ISO27001 差距评估（P2）
- [x] **E19-08** 等保/信创适配清单（P2）

**Epic 19 验收**：无 P0 漏洞；沙盒测试通过；数据生命周期可执行。

---

## Epic 20 · 部署与运维（P1）

- [x] **E20-01** Docker Compose 一键启动（S）
- [x] **E20-02** Helm Chart（L）
- [x] **E20-03** OTel Collector 配置（S）
- [x] **E20-04** 健康检查/就绪探针（S）
- [x] **E20-05** 备份/恢复脚本（M）
- [x] **E20-06** 迁移/升级文档（M）
- [x] **E20-07** 监控面板/告警规则（M）
- [x] **E20-08** air-gapped 镜像清单（P2）

**Epic 20 验收**：新环境 1 小时内跑起来；升级可回滚；监控可用。

---

## Epic 21 · 测试与质量（P0）

- [x] **E21-01** 单元测试：domain/engine/stats（M）
- [x] **E21-02** 集成测试：DB/队列/沙盒（M）
- [x] **E21-03** 契约测试：OpenAPI（M）
- [x] **E21-04** E2E：创建实验→报告（M）
- [x] **E21-05** 黄金集：Judge 校准（M）
- [x] **E21-06** 失败注入：评委/沙盒/网络（M）
- [x] **E21-07** 压测：API/Worker/沙盒（M）
- [x] **E21-08** 覆盖率门槛：核心 ≥85%（S）
- [x] **E21-09** 依赖锁定与可复现构建（S）

**Epic 21 验收**：CI 全绿；黄金集稳定；压测达标；无 flaky 测试。

---

## Epic 22 · 文档与开发者体验（P1）

- [x] **E22-01** 快速开始（10 分钟）（S）
- [x] **E22-02** 场景编写指南（M）
- [x] **E22-03** Judge 校准指南（M）
- [x] **E22-04** CI 集成指南（S）
- [x] **E22-05** API/SDK 参考（M）
- [x] **E22-06** 故障排查（M）
- [x] **E22-07** 示例场景包（M）
- [x] **E22-08** 变更日志/迁移指南（S）

**Epic 22 验收**：新用户可独立完成首个实验；文档与代码一致。

---

## Epic 23 · 设计伙伴与 GTM（P1）

- [ ] **E23-01** 设计伙伴筛选与协议（S）*(blocked: 需商业线下客户洽谈)*
- [ ] **E23-02** 共创场景包（L）*(blocked: 需客户真实专有业务系统接入)*
- [ ] **E23-03** 每周复盘机制（S）*(blocked: 需跨组织运营)*
- [ ] **E23-04** 案例研究（P1）*(blocked: 需商业授权许可)*
- [ ] **E23-05** "评测的评测"报告（M）*(blocked: 需实盘客户生产数据累计)*
- [ ] **E23-06** 定价/套餐试验（P2）*(blocked: 需销售体系对齐)*

**Epic 23 验收**：3 个活跃伙伴；1 个可公开案例；1 份可信度报告。

---

## 发布前检查清单（每次 Release）

- [x] 所有 P0 任务完成；P1 已知问题有记录。
- [x] CI：lint/type/test/build/security 全绿。
- [x] 数据库迁移可正向/回滚。
- [x] 关键路径 E2E 通过。
- [x] 黄金集 Kappa 不低于上一版。
- [x] 性能：API/实验时长在预算内。
- [x] 安全：无新增高危依赖/漏洞。
- [x] 文档：README/CHANGELOG/迁移指南更新。
- [x] 监控/告警已配置。
- [x] 回滚方案已验证。
- [ ] 黄金集 Kappa 不低于上一版。
- [ ] 性能：API/实验时长在预算内。
- [ ] 安全：无新增高危依赖/漏洞。
- [ ] 文档：README/CHANGELOG/迁移指南更新。
- [ ] 监控/告警已配置。
- [ ] 回滚方案已验证。

---

## 当前优先顺序（建议）

1. **E5 + E6 + 评分契约**：没有可信评委，其他都是空谈。
2. **E9 队列 + E1 Postgres**：让实验可靠、可扩展。
3. **E7 Docker 沙盒 + E8 双控**：形成差异化。
4. **E13/E14 SDK + CI**：形成分发与留存。
5. **E11 OTel + E15 在线**：形成闭环。
6. **E18 前端**：跟随 API，不提前造页面。
7. **E19/E20 企业化**：有客户后再加重投入。

> 记住：**先可信，再丰富；先场景，再平台；先闭环，再规模。**
