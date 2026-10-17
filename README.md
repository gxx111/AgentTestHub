# AgentTestHub

**企业 Agent 的发布门禁：用可复现的仿真环境、带证据的轨迹裁决和 CI 集成，在发布前回答"这个版本能不能上线"。**

AgentTestHub 面向中大型企业的 AI 平台团队与测试团队，覆盖从 Agent 资产、数据集、评测实验、沙盒交互、评委裁决到发布门禁的完整工作流。项目当前处于 **beta**：真实模型闭环已验证，正在按 [开发路线](./docs/04-roadmap.md) 重建可信评测核心与生产级执行环境。

---

## 当前能力（与代码一致）

| 能力 | 状态 | 说明 |
|---|---|---|
| 真实模型接入 | 已实现 | LiteLLM、smolagents、Webhook |
| 多轮用户模拟 | 已实现 | 规则状态机 + LLM 模拟器 |
| 评测团队 | 已实现 | 用户模拟、红队、业务/安全评委、仲裁，带调用预算 |
| SQLite 沙盒 | 已实现 | 状态快照、差分、危险 SQL 拦截、故障注入 |
| 实验与重复统计 | 已实现 | Wilson / Bootstrap、flaky、成本/延迟 |
| Trace 回放 | 已实现 | 事件流、Realtime、失败证据 |
| 工作区与资产 | 已实现 | 登录、工作区、Agent/数据集 CRUD、密钥加密 |
| 确定性检查 + 校准评委 | 进行中 | 当前评委仍含启发式规则，P0 正在替换 |
| Docker / MCP 沙盒 | 实验性 | 当前为模拟实现，未接入主链路 |
| MAS 协同指标 | 实验性 | 指标类已存在，未接入主链路 |
| 在线评估 / 标注 / OTel | 规划中 | 见路线图 |
| 企业 SSO / RBAC / 审计 | 规划中 | 见路线图 |

> 详细差距与证据见 [真实评测报告](./docs/validation/REAL-EVALUATION-REPORT-2026-10-13.md)。对外沟通请只使用"已实现"能力。

---

## 快速开始

### 1. 安装

```bash
git clone https://github.com/gxx111/AgentTestHub.git
cd AgentTestHub

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. 运行测试

```bash
pytest tests/ -q
```

### 3. 启动全栈

Windows：

```cmd
run_dev.bat
```

Linux / macOS：

```bash
chmod +x run_dev.sh
./run_dev.sh
```

- Web 控制台：http://localhost:3005
- API 文档：http://127.0.0.1:8005/docs

### 4. 运行一个场景

```bash
agent-eval run benchmarks/ecommerce_refund/refund_benchmark.yaml --output report.json
```

---

## 文档

所有设计与交付文档统一在 [`docs/`](./docs/README.md)：

- [产品定位](./docs/00-product-positioning.md)
- [系统架构](./docs/01-architecture.md)
- [技术方案](./docs/02-technical-design.md)
- [落地方案](./docs/03-implementation-plan.md)
- [开发路线](./docs/04-roadmap.md)
- [开发清单](./docs/05-development-checklist.md)
- [真实评测基线](./docs/validation/REAL-EVALUATION-REPORT-2026-10-13.md)

根目录旧版设计稿已移除；历史版本可在 git 历史中查看。

---

## 仓库结构

```text
AgentTestHub/
├── apps/
│   └── web/                 # Next.js 控制台
├── packages/
│   ├── core/                # 领域模型、Runner、评委、模拟器、指标
│   ├── sandbox/             # SQLite / Docker / MCP 沙盒驱动
│   ├── server/              # FastAPI 控制面 + 实验服务
│   └── cli/                 # agent-eval CLI
├── benchmarks/              # 预置业务场景
├── docs/                    # 唯一设计文档来源
├── scripts/                 # 迁移/验证脚本
└── tests/                   # 单元 / 集成测试
```

目标结构（Phase 1）见 [技术方案](./docs/02-technical-design.md#2-目标仓库结构)。

---

## 设计原则

1. **Evidence-first**：每个结论必须能指向 Span 或状态差分。
2. **Deterministic-first**：能确定性判断的，绝不交给 LLM。
3. **OTel-first**：Trace 与 OpenTelemetry GenAI 语义对齐，不锁定。
4. **Reproducible**：版本、快照、种子、校准全部可追溯。
5. **Private by default**：私有化、数据不出域、最小权限。

---

## 贡献

- 开发前先读 [开发清单](./docs/05-development-checklist.md) 与对应 Epic。
- 每个 PR 必须更新文档、测试与变更日志。
- 不接受未经验证的能力声明；"实验性"功能必须在 README 标注。

## 许可证

Apache-2.0（待法务最终确认；核心 Runner/SDK 计划开源，企业治理功能商业授权）。
