# AgentTestHub: 标准化研发流程与工程开发规范指南

> **文档版本**：v1.0.0 (Engineering Workflow & Quality Governance)  
> **适用对象**：系统架构师、后端研发工程师、Agent 算法工程师、前端工程师、测试开发工程师  
> **制定宗旨**：**规范先行、契约驱动、测试兜底、质量内建**。杜绝游击队式随意编码，确保 AgentTestHub 从第一行代码起即达到工业级高可用与可维护标准。

---

## 一、Git 分支管理与协同工作流规范 (Git Workflow)

项目采用现代大厂普遍推行的 **轻量分支模型 (Trunk-Based / GitHub Flow)**，主分支严格保护，所有变更必须通过特性分支与自动化门禁合入。

### 1.1 分支生命周期规范

```
  main (受保护的生产/发布主分支，保证始终可运行、随时可发版)
   │
   ├─► [创建分支] feat/mvp-core-schemas
   │     │
   │     ├─ Commit 1: feat(schemas): add TaskSpec and WorldState models
   │     ├─ Commit 2: feat(schemas): add BinaryRubric and Dispute models
   │     └─ Commit 3: test(schemas): add unit tests for schema validation
   │     │
   │     ▼ (通过本地验证与自动化 CI 门禁)
   └─► [Pull Request / Merge] ──► 合入 main 分支
```

* **`main` 分支**：全局唯一受保护主干分支。禁止直接 `git push` 未经验证的实验性代码，每次合入必须保持 100% 测试通过。
* **特性分支命名规范**：
  - `feat/<模块名>-<简要特性>`：新功能开发（如 `feat/schemas-task-spec`）
  - `fix/<模块名>-<问题描述>`：Bug 修复（如 `fix/sandbox-sqlite-rollback`）
  - `test/<模块名>-<测试类型>`：补充测试（如 `test/judges-debate-protocol`）
  - `docs/<主题>`：纯文档更新（如 `docs/api-specification`）
  - `refactor/<模块名>`：重构且不改变外部行为（如 `refactor/runner-event-stream`）

---

### 1.2 Conventional Commits 语义化提交军规

严格遵守全球通行的 **Angular / Conventional Commits** 规范，提交信息必须清晰表明“影响范围”与“变更意图”。

#### Commit Message 统一格式：
```text
<type>(<scope>): <subject>

[可选 body: 详细说明为什么做这个修改、解决了什么痛点]
[可选 footer: 关联的 Issue 编号，如 Closes #12]
```

#### Type 类型枚举：
| Type | 语义说明 | 示例 |
|---|---|---|
| `feat` | 新增功能特性 | `feat(examiner): add UserSimulator hidden goal FSM` |
| `fix` | 修复缺陷或错误 | `fix(sandbox): resolve SQLite connection leak on timeout` |
| `docs` | 仅文档修改 | `docs(readme): update quickstart and architecture diagram` |
| `style` | 格式调整（不影响代码运行，如空格、缩进） | `style(core): apply ruff formatting` |
| `refactor` | 代码重构（既非新增特性也非修复 Bug） | `refactor(metrics): optimize SNR calculation algorithm` |
| `perf` | 提升性能的修改 | `perf(ast): cache parsed AST trees for repeated tool calls` |
| `test` | 增加或重构测试代码 | `test(schemas): add edge-case validation for TaskSpec` |
| `chore` | 构建流程、辅助工具或依赖项更新 | `chore(deps): bump litellm to 1.40.0` |

---

## 二、需求流转与完成定义 (Definition of Done, DoD)

为了避免“我以为开发完了，其实根本不能跑”的假完成现象，严格执行 **DoD 验收清单**。

### 2.1 任务卡流转四步法
1. **To Do（待办）**：需求输入，明确输入输出契约；
2. **In Progress（进行中）**：在独立的 `feat/*` 分支上编码；
3. **In Review / Verification（验证中）**：本地跑通类型检查与单元测试；
4. **Done（已完成）**：合入 `main` 分支，状态归档。

### 2.2 特性交付 DoD 铁律（合入 main 的必备门槛）
一个功能特性在被声明为“Done”之前，必须同时满足以下 **6 项条件**：
- [ ] **代码整洁**：通过 `ruff check` 与 `ruff format`，无语法与格式警告；
- [ ] **类型安全**：所有函数与公开类具备完整的 Python Type Hints，通过静态类型检查；
- [ ] **单元测试**：针对核心逻辑编写了对应的 Pytest 单元测试，核心函数覆盖率 $\ge 80\%$；
- [ ] **文档与契约同步**：若更改了数据模型或外部接口，同步更新对应文档与 Schema；
- [ ] **本地端到端绿灯**：本地执行 `pytest` 全量测试无任何 Error 或 Failure；
- [ ] **自包含提交**：Commit 历史清晰，语义符合规范。

---

## 三、代码工程规范与技术约束 (Coding Standards)

### 3.1 Python 核心规范
* **Python 版本基线**：统一采用 **Python 3.10+**（推荐 3.10 ~ 3.12），充分利用原生强类型系统（如 `list[str]`、`int | None`）。
* **数据建模原则**：
  - 核心传输对象一律继承自 `pydantic.BaseModel`；
  - 关键字段必须提供 `description` 与 `Field(ge=..., default=...)` 约束；
  - 默认开启 `model_config = ConfigDict(frozen=True)`（不可变数据流原则），避免对象被随意就地修改导致排查灾难。
* **异常处理分级规范**：
  - 严禁书写裸 `except:` 或 `except Exception: pass` 吞掉异常；
  - 所有平台级错误必须继承自根异常 `AgentTestHubError`，并明确区分：
    - `SchemaValidationError`：用户配置或数据格式非法；
    - `SandboxExecutionTimeoutError`：沙盒执行超时；
    - `ExaminerDisputeError`：法官辩论未能在限定轮次达成共识；
    - `MASDeadlockDetectedError`：多 Agent 依赖环死锁。

### 3.2 依赖管理与打包规范
* 使用统一的 `pyproject.toml` 管理依赖，遵循现代 PEP 621 标准；
* 核心引擎（`agent_test_hub`）严禁引入笨重的前端或非必要重型依赖，保持轻量高效。

---

## 四、测试分级金字塔与契约测试规范 (Testing Strategy)

评测平台本身的准确性是整个系统的生命线。测试严格划分为三个金字塔层级：

```
                    ▲
                   / \
                  /   \     L3: 端到端基准回归测试 (E2E Benchmark Tests)
                 / E2E \    • 运行完整电商退款/代码重构场景
                /───────\   • 校验全流程耗时、报告生成与状态差分
               / 模块集成 \  L2: 模块集成测试 (Integration Tests)
              /  测试     \ • Mock LLM 返回，验证陪审团辩论逻辑
             /─────────────\• 验证 SQLite 沙盒快照创建与回滚
            /   单元测试    \ L1: 单元测试 (Unit Tests, 执行毫秒级)
           /   (Unit Tests)  \• 验证 Pydantic Schema 校验边界
          /───────────────────\• 验证 NetworkX 死锁检测算法
```

* **L1 单元测试**：存放于 `tests/unit/`，不得发起外部网络请求或耗时 IO，执行时间必须控制在秒级；
* **L2 模块集成测试**：存放于 `tests/integration/`，通过 `pytest-mock` 模拟大模型返回，验证组件间通信；
* **L3 端到端基准测试**：存放于 `tests/e2e/`，定期触发或在发版前运行。

---

## 五、CI/CD 自动化门禁规划 (Continuous Integration)

在 GitHub 仓库中配置自动化的 GitHub Actions 工作流（`.github/workflows/ci.yml`），每次提交自动执行三道防线：

```yaml
# CI 门禁标准触发步骤流水线
name: CI Quality Gate
on: [push, pull_request]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      # 门禁 1: 静态语法与格式化检查
      - name: Lint and Format with Ruff
        run: |
          pip install ruff
          ruff check .
          ruff format --check .
      
      # 门禁 2: 全量单元测试与覆盖率门禁
      - name: Run Pytest Suite
        run: |
          pip install -e ".[dev]"
          pytest tests/unit --cov=src --cov-fail-under=80
```

---

## 六、MVP 0.1 研发节拍看板与第一棒执行计划 (Immediate Execution)

按照上述规范，我们即刻开启 **MVP 0.1 的第一个工程 Sprint**，具体任务拆解如下：

### 📋 当前 Sprint 任务卡清单 (Sprint 1: Schemas & Walking Skeleton)

| 任务编号 | 任务名称 | 责任包 / 路径 | 交付产物与验收标准 (DoD) | 状态 |
|---|---|---|---|---|
| **TASK-01** | 工程脚手架与 pyproject.toml 初始化 | 根目录配置 | 完成项目元数据、依赖项与格式化工具链配置 | `[Pending]` |
| **TASK-02** | 任务定义与沙盒状态契约 (`task.py`) | `packages/core/schemas/` | 完成 `TaskSpec`、`WorldState` 模型及校验 | `[Pending]` |
| **TASK-03** | 美团二元 Rubric 契约 (`rubric.py`) | `packages/core/schemas/` | 完成 `BinaryRubric`、0/1/Unknown 二元结果模型 | `[Pending]` |
| **TASK-04** | OpenInference 规范 Trace 契约 (`trace.py`)| `packages/core/schemas/` | 完成结构化执行事件流模型与证据锚点 | `[Pending]` |
| **TASK-05** | 裁决报告与因果归因契约 (`report.py`) | `packages/core/schemas/` | 完成包含雷达数据与二元检查清单的报告模型 | `[Pending]` |
| **TASK-06** | 编写 Schema 自动化单元测试 | `tests/unit/` | 执行 `pytest` 100% 通过，验证模型边界合法性 | `[Pending]` |

---
*文档归档路径：`D:\自动化工具开发\AI Agent学习资料\AgentTestHub\AgentTestHub-Engineering-Workflow-and-Standards.md`*  
*执行监督：AgentTestHub Technical Architecture & Engineering Group*
