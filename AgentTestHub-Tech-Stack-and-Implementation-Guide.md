# AgentTestHub 2.1: 技术选型、复用清单与敏捷工程落地蓝图

> **文档版本**：v1.0.0 (Engineering Implementation Blueprint)  
> **面向对象**：系统架构师、Agent 算法专家、全栈开发专家、前端/UI 专家  
> **核心战略**：**70% 复用全球顶级开源成熟轮子 + 30% 核心自研壁垒护城河**，拒绝从 0 重造平庸基础设施，4~6 周高效交付行业领先产品。

---

## 一、开源技术选型与复用清单 (The 70% Reuse Matrix)

**严格执行“能拿现成绝不硬写”原则**。以下底层技术直接选用全球事实标准库：

### 1.1 后端与算法基础设施选型

| 领域 | 选型组件与版本 | 开源仓库 / Star | 选型理由与复用价值 |
|---|---|---|---|
| **大模型调用网关** | `litellm >= 1.40.0` | BerriAI/litellm (20k★) | **严禁手写不同模型适配**！LiteLLM 以统一 OpenAI 规范抽象了 100+ 商业与开源模型（Claude, OpenAI, DeepSeek, Qwen 等），内置流式解析、重试退避与精确 Token 计费。 |
| **拓扑与图计算** | `networkx >= 3.2.0` | networkx/networkx (15k★) | 用于多 Agent 通信 DAG 建模、级联死锁环检测（`simple_cycles`）、最短路径计算与信息中心度度量。 |
| **数据契约与校验** | `pydantic >= 2.6.0` | pydantic/pydantic (22k★) | 基于 Rust 核心的超高性能类型校验，自动生成 OpenAPI / JSON Schema，作为前后端与 DSL 数据协议底座。 |
| **追踪与可观测性** | `opentelemetry-api` + `openinference-semantic-conventions` | Arize-ai/openinference (2k★) | 兼容全球开源大模型 Trace 语义标准，免去手写 Span/Trace 数据结构的繁琐工作。 |
| **容器沙盒交互** | `docker >= 7.0.0` (Python SDK) | docker/docker-py (6.5k★) | 管理轻量容器生命周期、端口挂载与物理状态快照（Commit / Rollback）。 |
| **语法解析与 AST** | `tree-sitter` / `ast` (Python 内置) | tree-sitter/tree-sitter | 极速解析工具调用传参与代码结构，实现阿里 Hop4 级别的参数抽象语法树精准校验。 |
| **测试执行引擎** | `pytest >= 8.0.0` | pytest-dev/pytest (12k★) | 原生复用 Pytest 的执行器、断言机制与插件生态，提供开发者零心智负担的 CLI 体验。 |

### 1.2 前端与可视化技术选型

| 领域 | 选型组件与版本 | 开源仓库 / Star | 选型理由与复用价值 |
|---|---|---|---|
| **前端全栈框架** | `Next.js 15 (App Router)` | vercel/next.js (130k★) | 现代化全栈框架，支持 Server Components、流式 SSR 与极简 API 路由。 |
| **拓扑节点流动图** | `@xyflow/react >= 12.0` (React Flow) | xyflow/xyflow (26k★) | **核心竞技场画布**：开箱即用的拖拽、实时动态边流动、自定义节点卡片（展示双 Agent 对战与状态流）。 |
| **UI 与组件库** | `shadcn/ui` + `Tailwind CSS` | shadcn/ui (75k★) | 行业公认最前沿的极简科技感设计语言，复制即用，代码 100% 掌握在自己手中。 |
| **图表可视化** | `recharts` / `visx` | recharts/recharts (24k★) | 绘制 7-Hop 逐跳时序瀑布流、多维度能力雷达图与因果故障归因树。 |

---

## 二、0-1 核心自研模块清单 (The 30% Core Moat Modules)

以下 5 大核心模块属于行业空白或独创发明，必须由我们团队 100% 深入自研：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AgentTestHub 核心自研五大包                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. packages/core/examiners/    - 考官团队动态协同与对抗博弈网络              │
│    • user_simulator/           - 状态化用户模拟官 (隐藏诉求状态机 FSM)       │
│    • red_team/                 - 对抗攻防红队官 (Crescendo 渐进式攻击算法)   │
│    • watchdog/                 - 环境监考官 (透明 MCP 拦截与故障注入引擎)    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. packages/core/judges/       - 美团升级版：二元化 Rubric 陪审团与辩论合议庭│
│    • binary_rubric.py          - 0/1/Unknown 事实检查项断言引擎              │
│    • debate_protocol.py        - 3 轮交叉质询与冲突仲裁协议                 │
│    • trace_anchor.py           - 强制日志 Trace Span ID 证据锚定校验器       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. packages/core/metrics/      - 阿里 7-Hop 全链路指标网格与 MAS 协同度量    │
│    • hop_pipeline/             - 阿里 Hop 1 ~ Hop 7 逐跳指标算子集           │
│    • mas/                      - 团队通信信噪比 (SNR)、角色漂移度、死锁检测  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. packages/core/diagnostics/  - 因果故障归因树推导引擎                      │
│    • causal_tree.py            - 基于 7-Hop 执行逆向推导根因与自动生成修复建议│
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. packages/cli & dsl/         - 声明式乐高 YAML 引擎与 Pytest 原生扩展      │
│    • loader.py                 - 声明式评测 YAML 解析与依赖装配              │
│    • pytest_plugin.py          - `@pytest.mark.agent_eval` 原生装饰器扩展    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、推荐代码仓库组织规范 (Monorepo Layout)

采用现代清晰的 Monorepo 代码结构，前后端及核心引擎各司其职：

```
AgentTestHub/
├── pyproject.toml                     # Python 全局依赖与工作区配置
├── pnpm-workspace.yaml                # 前端工作区配置
├── README.md
│
├── packages/                          # 核心自研 Python 包
│   ├── core/                          # 核心评测与调度引擎
│   │   ├── src/agent_test_hub/
│   │   │   ├── examiners/             # [自研] 考官网络 (用户模拟官 / 红队官)
│   │   │   ├── judges/                # [自研] 美团二元 Rubric 陪审团与辩论
│   │   │   ├── metrics/               # [自研] 阿里 7-Hop 算子 + MAS 协同算子
│   │   │   ├── diagnostics/           # [自研] 因果故障归因树引擎
│   │   │   ├── schemas/               # [契约] Pydantic 核心数据模型
│   │   │   └── runner.py              # 执行调度总线
│   │
│   ├── sandbox/                       # 沙盒虚拟化与驱动
│   │   ├── docker_sandbox.py          # Docker 容器驱动与镜像快照
│   │   ├── sqlite_sandbox.py          # 极速轻量内存 DB 沙盒驱动
│   │   └── mcp_proxy.py               # MCP 协议透明拦截与故障注入代理
│   │
│   └── cli/                           # 命令行工具与 Pytest 插件
│       ├── main.py                    # `agent-eval run` CLI 入口
│       └── pytest_plugin.py           # Pytest 自动化测试门禁集成
│
├── apps/                              # 应用层
│   └── web/                           # Next.js 15 现代化 Web 竞技场
│       ├── src/
│       │   ├── app/                   # App Router 页面 (Arena, Reports, Dashboard)
│       │   ├── components/
│       │   │   ├── arena-flow/        # React Flow 拓扑流竞技场组件
│       │   │   ├── debate-wall/       # 陪审团实时辩论回放墙组件
│       │   │   └── causal-tree/       # 因果归因故障树可视化组件
│       │   └── lib/                   # 前端工具函数与数据适配
│       ├── package.json
│       └── tailwind.config.js
│
├── benchmarks/                        # 官方预置场景库
│   ├── customer_support_refund/       # 示例：电商退款动态评测套件
│   ├── code_refactor_agent/           # 示例：代码重构 Agent 评测套件
│   └── mas_software_team/             # 示例：AutoGen 研发团队协作评测套件
│
└── tests/                             # 自测试用例 (Unit & Integration)
```

---

## 四、MVP 0.1 敏捷落地四周冲刺路线图 (The 4-Week Sprint)

遵循“垂直切片 (Walking Skeleton)”原则，用 4 周时间打通可运行的端到端系统：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       四周冲刺推进全景 (Sprint Roadmap)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Week 1: 契约先行与极简骨架 (Contract-First & Walking Skeleton)              │
│ • 后端：使用 Pydantic 定义核心数据模型 (TaskSpec, TraceEvent, ReportSpec)    │
│ • 框架：通过 LiteLLM 跑通基础的 Agent 访问网关                               │
│ • 产出：在本地终端跑通最简单的 Pytest 单测并生成一份 Mock JSON 报告          │
├─────────────────────────────────────────────────────────────────────────────┤
│ Week 2: 动态用户模拟官与环境状态差分 (User Sim & World State Delta)         │
│ • 考官：实现轻量级状态化用户模拟官 (User Simulator with Hidden Goal)         │
│ • 沙盒：实现 SQLite 内存级沙盒驱动，支持执行前后数据表 State Delta 差分计算   │
│ • 指标：落地阿里 Hop 4（参数 AST 语法树结构校验）                            │
│ • 产出：实现“用户模拟官提问 ➔ Agent 调工具改数据库 ➔ 物理状态断言”闭环      │
├─────────────────────────────────────────────────────────────────────────────┤
│ Week 3: 美团二元化 Rubric 陪审团与辩论裁决 (Binary Judicial Committee)      │
│ • 裁判：实现基于 0/1/Unknown 二元事实检查项的法官判定引擎                    │
│ • 辩论：实现法官分歧时的 3 轮辩论与证据 Trace Span ID 锚定协议               │
│ • 诊断：实现基础版因果故障归因树输出                                         │
│ • 产出：产出高可信、附带证据链条的结构化评测裁决报告                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Week 4: 前端 Web 竞技场与多智能体指标 (React Flow Arena & MAS Metrics)       │
│ • 前端：基于 Next.js 15 + React Flow 实现动态拓扑对战流动面板与辩论回放墙   │
│ • 协同：实现团队通信信噪比 (SNR) 与死锁环检测算法                            │
│ • 交付：在本地浏览器完整演示一套企业级 Agent 动态评测全流程！               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---
*文档归档路径：`D:\自动化工具开发\AI Agent学习资料\AgentTestHub\AgentTestHub-Tech-Stack-and-Implementation-Guide.md`*  
*签发组织：AgentTestHub Technical Architecture & Engineering Group*
