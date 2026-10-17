# AgentTestHub 文档中心

本目录是 AgentTestHub 唯一的设计与交付文档来源。根目录旧版设计稿已移除，历史内容可在 git 历史中查看。

## 文档地图

| 文档 | 内容 | 主要读者 |
|---|---|---|
| [00-product-positioning.md](./00-product-positioning.md) | 产品定位、目标客户、竞争策略、商业模式 | 产品、创始人、市场 |
| [01-architecture.md](./01-architecture.md) | 系统架构、领域模型、运行时流程、部署拓扑 | 架构师、后端、前端 |
| [02-technical-design.md](./02-technical-design.md) | 技术栈、数据模型、评测契约、沙盒、评委、统计、API | 工程师 |
| [03-implementation-plan.md](./03-implementation-plan.md) | 落地方案、里程碑、90 天计划、迁移、运维 | 研发负责人、PM |
| [04-roadmap.md](./04-roadmap.md) | 12 个月开发路线、季度目标、KPI、决策门 | 全员 |
| [05-development-checklist.md](./05-development-checklist.md) | 可执行的开发清单与验收标准 | 工程师、PM |
| [06-engineering-process.md](./06-engineering-process.md) | 标准研发流程、测试策略、评审、发布与复盘 | 全员 |
| [07-frontend-architecture.md](./07-frontend-architecture.md) | 前端信息架构、设计系统、代码结构与验收标准 | 前端、设计、PM |
| [08-development-progress.md](./08-development-progress.md) | 开发阶段与任务进度追踪、测试证据与变更记录 | 全员、研发负责人 |
| [validation/REAL-EVALUATION-REPORT-2026-10-13.md](./validation/REAL-EVALUATION-REPORT-2026-10-13.md) | 当前 MVP 的真实评测基线（证据，不是承诺） | 全员、设计伙伴 |

## 阅读顺序

1. 新成员：`00` → `01` → `04` → `05`
2. 后端/架构：`01` → `02` → `03` → `05`
3. 产品/售前：`00` → `04` → `validation`
4. 前端：`01` → `02` 的 API/领域模型 → `05`

## 文档规则

1. **单一事实来源**：产品能力、架构、接口、路线图只在本目录维护，不再在根目录或代码注释里复制整套设计。
2. **可验证**：任何对外能力声明必须有代码、测试或评测数据支撑。没有证据的能力只能写成"规划中"。
3. **与代码同 PR**：接口、数据模型、评测语义变更时，同步更新对应文档。
4. **ADR**：重大架构决策记录在 `01-architecture.md` 的 ADR 表中；被推翻的决策保留记录，不删除。
5. **不写空话**：每一条路线图任务都要有验收标准、负责人角色和依赖。

## 当前状态

- 阶段：MVP 已验证，进入"可信度修复 + 差异化 MVP"阶段。
- 代码基线：Python 3.10+ / FastAPI / Next.js 15；当前 44 个测试通过。
- 主要缺口：评委效度、评分契约、真实沙盒、MAS 指标接线、任务队列、OTel/SDK、在线评估、企业治理。
- 详细差距见 [validation/REAL-EVALUATION-REPORT-2026-10-13.md](./validation/REAL-EVALUATION-REPORT-2026-10-13.md) 与 `05-development-checklist.md` 的 P0 项。
