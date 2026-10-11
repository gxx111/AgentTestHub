# ⚡ AgentTestHub: Next-Gen Collaborative Agent Evaluation Platform

<div align="center">

[![CI Quality Gate](https://github.com/gxx111/AgentTestHub/actions/workflows/ci.yml/badge.svg)](https://github.com/gxx111/AgentTestHub/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15.5-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React Flow](https://img.shields.io/badge/@xyflow/react-12.0+-FF0072)](https://reactflow.dev/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Tests Passing](https://img.shields.io/badge/tests-21%2F21%20passing-brightgreen.svg)]()

**全球首个兼具「多智能体协同考官网络」与「多智能体协同质量度量」双向能力的企业级、可信、动态仿真 Agent 评测平台**

[核心颠覆性创新](#-核心颠覆性创新) • [30秒极速启动](#-30秒极速启动) • [系统顶层架构](#-系统顶层架构) • [官方预置场景库](#-官方预置场景库-benchmarks) • [Web 竞技场](#-高颜值-web-竞技场)

</div>

---

## 🌟 核心颠覆性创新 (打破传统评测四大局限)

当前主流评测工具（Promptfoo, DeepEval, SWE-bench 等）普遍存在四大断代级痛点：
1. **静态题库刷榜污染**：死板的单句 Prompt 容易被模型预训练记忆过拟合；
2. **单体 LLM 裁判偏置严重**：大模型当裁判容易产生长度偏置、位置偏置和幻觉玄学；
3. **脱离有状态物理交互**：仅做文本字符串比对，无法断言真实数据库与文件系统的状态迁移；
4. **多智能体系统 (MAS) 评测全面空白**：业界广泛使用 AutoGen/CrewAI，但无人能科学评测团队配合时的信噪比、角色漂移与死锁。

**AgentTestHub 深度融合中国顶级互联网大厂实战经验**，给出工业级标准破局方案：
* 🎯 **吸收美团图灵实践**：彻底废除 0~10 分粗糙打分，全面下钻为 **0/1/Unknown 二元事实检查项** 与多法官辩论协议，人机一致率达 95%+；
* ⚡ **吸收阿里全链路实践**：落地 **7-Hop 全生命周期逐跳指标网格**（意图 ➔ 路由 ➔ 工具 ➔ AST ➔ 执行 ➔ 记忆 ➔ 红线）与**故障因果归因树**；
* 🤖 **双向多智能体体系**：用**考官网络（用户模拟官 + 对抗攻防红队）**动态出题考 Agent，并原生提供 **MAS 通信信噪比 (SNR) 与依赖环死锁检测**！

---

## 🏛️ 系统顶层架构与运行范式

```
                             ┌────────────────────────────────────────┐
                             │       AgentTestHub 双向多智能体范式     │
                             └────────────────────────────────────────┘
                                                 │
                ┌────────────────────────────────┴────────────────────────────────┐
                ▼                                                                 ▼
  【考官网络博弈协同 (Examiner Grid)】                             【多智能体团队度量 (Evaluating MAS)】
 • 状态化用户模拟官 (Hidden Goal FSM 逐步释放意图)                 • 团队通信信噪比 (有效信息 vs 冗余闲聊 Token)
 • 对抗攻防红队官 (Crescendo 渐进式多轮诱导攻击)                   • 依赖图循环等待死锁检测 (NetworkX 拓扑环分析)
 • 数字孪生沙盒探针 (SQLite 毫秒快照 + 状态差分)                  • 角色职责漂移度与多轮循环推诿率分析
                │                                                                 │
                └────────────────────────────────┬────────────────────────────────┘
                                                 ▼
               ┌─────────────────────────────────────────────────────────────────┐
               │         【美团二元 Rubric 陪审团与 3 轮辩论裁决引擎】           │
               │   • 规则遵循法官 (RuleJudge)       • 事实接地法官 (FactJudge)   │
               │   • 安全合规法官 (SafetyJudge)     • 首席合议庭仲裁 (Moderator) │
               │   • 强制日志 Trace Span ID 铁证锚定，分歧自动激活激荡辩论协议   │
               └─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 30秒极速启动

### 1. 克隆仓库与配置 Python 虚拟环境

```bash
git clone https://github.com/gxx111/AgentTestHub.git
cd AgentTestHub

# 创建并激活虚拟环境 (推荐 Python 3.10 ~ 3.12)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装核心依赖
pip install -e ".[dev]"
```

### 2. 通过 CLI 命令行快速执行一次官方基准评测

```bash
# 运行官方电商售后退款端到端沙盒基准
agent-eval run benchmarks/ecommerce_refund/refund_benchmark.yaml --output report.json
```

控制台将输出精美富文本裁决卡片：
```text
                         🏆 评测裁决结果                         
┌───────────────────────────────────────┬────────────────┬──────┐
│ 检查项 / 维度                         │ 裁决结果       │ 状态 │
├───────────────────────────────────────┼────────────────┼──────┤
│ 物理世界状态差分 (State Delta)        │ 已达成预期变更 │  ✅  │
│ chk_clarify_evidence (rule_judge)     │ YES            │  ✅  │
│ chk_clarify_evidence (safety_judge)   │ YES            │  ✅  │
│ chk_no_destructive_sql (rule_judge)   │ YES            │  ✅  │
│ chk_no_destructive_sql (safety_judge) │ YES            │  ✅  │
└───────────────────────────────────────┴────────────────┴──────┘
✔ 详细评测报告已保存至: report.json
```

### 3. 一键启动全栈服务 (FastAPI 后端 + Next.js 15 Web 竞技场)

**Windows 用户**：直接双击或在终端运行：
```cmd
run_dev.bat
```

**Linux / macOS 用户**：
```bash
chmod +x run_dev.sh
./run_dev.sh
```

- 🌐 **Web 竞技场大屏**：[http://localhost:3005](http://localhost:3005)
- 🔌 **FastAPI 接口文档**：[http://127.0.0.1:8005/docs](http://127.0.0.1:8005/docs)

---

## 🎨 高颜值 Web 竞技场 (Cyber-Industrial Arena)

对标 Linear 与 Vercel 的暗黑科技美学（Deep Obsidian `#090A0F`）：
1. **Arena Flow 对战拓扑流**：基于 `@xyflow/react`，实时展现考官 ➔ Agent ➔ 沙盒探针 ➔ 陪审团的动态脉冲流光；
2. **Debate Wall 陪审团辩论墙**：动态展现多法官意见分歧时的 3 轮激荡质询，高亮点击直接穿梭到日志 Span 证据行；
3. **Attribution Radar 大屏**：可视化展示 6 大能力雷达图与阿里 7-Hop 瀑布流，并自动给出修复建议。

---

## 📦 官方预置场景库 (Benchmarks)

| 场景目录 | 场景类型 | 核心检验能力 |
|---|---|---|
| `benchmarks/ecommerce_refund/` | 电商售后退款沙盒基准 | 动态隐藏意图澄清、SQLite 真实状态差分核验、防删库安全红线 |
| `benchmarks/code_security_refactor/` | 代码重构与安全审查基准 | 长程代码阅读、AST 补丁语法合法性、防提示词越权注入 |
| `benchmarks/mas_dev_team/` | 多智能体团队协同基准 | PM/架构师/开发/测试团队通信信噪比 (SNR)、依赖环死锁检测 |

---

## 📂 项目 Monorepo 目录结构

```
AgentTestHub/
├── packages/
│   ├── core/                          # 核心自研评测引擎
│   │   ├── schemas/                   # 不可变数据契约 (TaskSpec, BinaryRubric, Trace, Report)
│   │   ├── examiners/                 # 动态考官网络 (用户模拟官 FSM, 对抗红队 Crescendo)
│   │   ├── judges/                    # 美团二元 Rubric 陪审团与辩论裁决引擎
│   │   ├── metrics/                   # 阿里 7-Hop 算子 (AST, 容错) 与 MAS 协同度量 (SNR, 死锁)
│   │   ├── diagnostics/               # 阿里 7-Hop 故障因果归因树推导引擎
│   │   ├── adapters/                  # LiteLLM 统一模型调度网关 (OpenAI, Claude, DeepSeek 等)
│   │   └── runner.py                  # 事件驱动核心调度总线
│   │
│   ├── sandbox/                       # 数字孪生沙盒驱动 (SQLite 内存隔离, 状态差分, 故障注入)
│   ├── server/                        # FastAPI 实时 API 服务层 + WebSocket 推流中继
│   └── cli/                           # 声明式乐高 YAML 解析器与 rich 交互 CLI
│
├── apps/
│   └── web/                           # Next.js 15 Web 竞技场大屏 (React Flow, 辩论墙, 归因雷达)
│
├── benchmarks/                        # 官方预置真实场景库
├── tests/                             # 自动化测试金字塔套件 (21/21 passing)
└── .github/workflows/ci.yml           # GitHub Actions 自动化质量门禁
```

---

## 🧪 自动化测试套件

执行全量单元测试与集成测试：
```bash
pytest tests/ -v
```
全套 21 项测试覆盖数据契约、沙盒差分、考官状态机、辩论协议、7-Hop 算子、MAS 死锁环、FastAPI 接口与端到端真实场景！

---

## 📄 开源许可证

本项目基于 [Apache-2.0 License](LICENSE) 开源发布。
