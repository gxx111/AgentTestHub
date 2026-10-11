# Multi-Agent 协作式 Agent 评测平台架构设计

> 版本：v1.0
> 日期：2025-10-11
> 作者：Agent Test Platform Team

---

## 一、项目背景与目标

### 1.1 市场痛点

当前 Agent 开发如火如荼，但**Agent 评测能力严重滞后**：

| 问题 | 现状 |
|------|------|
| **评测维度单一** | 多数工具只测"任务完成率"，缺乏对 Agent 特性的深度评测 |
| **静态题库局限** | 无法覆盖真实场景的多样性和动态性 |
| **复用性差** | 传统测试与 Agent 测试割裂，重复建设 |
| **扩展性弱** | 用户无法自定义评测维度和场景 |
| **行业空白** | 目前没有做得好的多 Agent 协作评测平台 |

### 1.2 核心目标

**用多智能体协作系统作为"考官"来评测 Agent**，实现：

1. **自动化测试生成** - 命题官动态生成多样化测试用例
2. **多维度深度评测** - 覆盖 Agent 特有能力（工具调用、MCP、知识召回、协作等）
3. **灵活可扩展** - 支持用户自定义场景、指标、评判方式
4. **行业领先** - 填补多 Agent 协作评测空白

### 1.3 设计原则

```
┌─────────────────────────────────────────────────────────────┐
│                     核心设计原则                             │
├─────────────────────────────────────────────────────────────┤
│  1. 插件化架构     - 所有组件可插拔，指标/场景/评判均可扩展   │
│  2.Schema 标准化   - 任务定义统一格式，支持导入导出           │
│  3. 多 Agent 协作  - 内置协作模式，也支持自定义拓扑           │
│  4. 评判多样性    - 支持 LLM Judge / 脚本 / 人工 / 混合       │
│  5. 开箱即用      - 降低使用门槛，预置丰富模板                │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、整体架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户接入层                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   Web UI   │  │   CLI 工具  │  │  Python SDK │  │   REST API  │           │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              平台核心层                                       │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        插件系统 (Plugin System)                        │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │  │
│  │  │  指标   │  │  场景   │  │  评判   │  │  工具   │  │  报告   │        │  │
│  │  │ 插件   │  │  插件   │  │  插件   │  │  适配器 │  │  模板   │        │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │    场景构建器    │───▶│    评测引擎     │───▶│    报告生成     │         │
│  │  (Scenario)     │    │    (Engine)     │    │    (Report)     │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        协作编排器 (Orchestrator)                        │  │
│  │  - 命题 Agent (Task Builder)  - 执行 Agent (被测)                       │  │
│  │  - 裁判 Agent (Judge)         - 分析 Agent (Analyzer)                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              外部依赖层                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │  LLM API   │  │ MCP Server  │  │  向量数据库  │  │  监控追踪   │           │
│  │ (OpenAI/   │  │  (MCP SDK) │  │ (Pinecone/  │  │ (AgentOps/  │           │
│  │  Claude)   │  │             │  │  Milvus)   │  │  LangSmith) │           │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
agent-eval-platform/
├── src/
│   ├── core/                          # 核心模块
│   │   ├── engine/                    # 评测引擎
│   │   │   ├── __init__.py
│   │   │   ├── executor.py            # 任务执行器
│   │   │   ├── runner.py              # 运行调度器
│   │   │   └── context.py             # 执行上下文
│   │   ├── orchestrator/              # 协作编排器
│   │   │   ├── __init__.py
│   │   │   ├── agent_team.py          # Agent 团队管理
│   │   │   ├── task_builder.py        # 命题 Agent
│   │   │   ├── judge_agent.py         # 裁判 Agent
│   │   │   └── analyzer_agent.py      # 分析 Agent
│   │   └── communication/            # Agent 间通信
│   │       ├── __init__.py
│   │       ├── topology.py            # 通信拓扑
│   │       ├── message.py            # 消息协议
│   │       └── bus.py                 # 消息总线
│   │
│   ├── plugins/                       # 插件系统
│   │   ├── __init__.py
│   │   ├── base.py                    # 插件基类
│   │   ├── registry.py                # 插件注册表
│   │   ├── metrics/                   # 指标插件
│   │   │   ├── __init__.py
│   │   │   ├── tool_calling.py        # 工具调用指标
│   │   │   ├── mcp_usage.py           # MCP 使用指标
│   │   │   ├── knowledge_recall.py    # 知识召回指标
│   │   │   ├── collaboration.py       # 协作能力指标
│   │   │   ├── planning.py            # 规划能力指标
│   │   │   └── security.py            # 安全边界指标
│   │   ├── judges/                    # 评判插件
│   │   │   ├── __init__.py
│   │   │   ├── llm_judge.py           # LLM 评判
│   │   │   ├── script_judge.py        # 脚本评判
│   │   │   └── hybrid_judge.py       # 混合评判
│   │   └── scenarios/                 # 场景插件
│   │       ├── __init__.py
│   │       ├── code_generation.py     # 代码生成场景
│   │       ├── data_analysis.py       # 数据分析场景
│   │       └── conversation.py        # 对话场景
│   │
│   ├── adapters/                      # 框架适配器
│   │   ├── __init__.py
│   │   ├── autogen/                   # AutoGen 适配
│   │   ├── crewai/                    # CrewAI 适配
│   │   ├── langgraph/                 # LangGraph 适配
│   │   ├── mcp/                       # MCP 协议适配
│   │   └── custom/                    # 自定义适配
│   │
│   ├── schemas/                       # 数据模型
│   │   ├── __init__.py
│   │   ├── task.py                    # 任务定义
│   │   ├── scenario.py                # 场景定义
│   │   ├── metric.py                  # 指标定义
│   │   ├── result.py                  # 结果定义
│   │   └── agent.py                   # Agent 定义
│   │
│   └── utils/                         # 工具函数
│       ├── __init__.py
│       ├── config.py                  # 配置管理
│       ├── logger.py                  # 日志
│       └── validators.py              # 数据校验
│
├── tests/                             # 测试用例
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── examples/                          # 示例
│   ├── scenarios/                     # 场景示例
│   ├── metrics/                       # 指标示例
│   └── configs/                      # 配置示例
│
├── docs/                              # 文档
├── config/                           # 默认配置
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## 三、核心模块详细设计

### 3.1 协作编排器 (Orchestrator)

这是平台的核心，用多 Agent 协作完成评测任务。

#### 3.1.1 Agent 团队角色

```
┌─────────────────────────────────────────────────────────────────┐
│                      评测 Agent 团队                              │
│                                                                  │
│  ┌──────────────┐                                               │
│  │   命题官     │  职责：生成多样化测试用例，定义评估标准        │
│  │ Task Builder │  输入：评测目标、能力维度                      │
│  └──────┬───────┘  输出：测试任务 JSON                          │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────┐    ┌──────────────┐                           │
│  │   执行官     │◀───▶│   助手       │  职责：运行被测 Agent     │
│  │  Executor    │    │  Assistant   │  输入：测试任务、工具列表  │
│  └──────┬───────┘    └──────────────┘  输出：执行结果、Trace    │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────┐                                               │
│  │   裁判官     │  职责：评估执行结果，打分，提供反馈            │
│  │    Judge     │  输入：任务定义、执行结果、评判标准            │
│  └──────┬───────┘  输出：评分、问题诊断、改进建议                │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────┐                                               │
│  │   分析官     │  职责：汇总评测结果，生成报告                  │
│  │   Analyzer   │  输入：多轮评分、详细 Trace                    │
│  └──────────────┘  输出：综合报告、可视化图表                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.1.2 协作协议定义

```python
# 协作协议示例
COLLABORATION_PROTOCOL = {
    "name": "standard_eval",
    "roles": {
        "task_builder": {
            "system_prompt": "你是一个专业的测试用例生成专家...",
            "output_format": "json",
            "tools": ["generate_task", "validate_task"]
        },
        "executor": {
            "system_prompt": "你是一个 Agent 执行环境...",
            "timeout": 300,
            "retry": 2
        },
        "judge": {
            "system_prompt": "你是一个严格的评测裁判...",
            "criteria": ["correctness", "efficiency", "safety"]
        },
        "analyzer": {
            "system_prompt": "你是一个数据分析专家...",
            "output_format": "markdown"
        }
    },
    "topology": {
        "type": "sequential",  # sequential / parallel / tree / graph
        "edges": [
            ("task_builder", "executor"),
            ("executor", "judge"),
            ("judge", "analyzer")
        ]
    },
    "iterations": 1,  # 支持多轮迭代优化
    "feedback_mode": "direct"  # direct / with_reason / with_correction
}
```

#### 3.1.3 通信拓扑支持

| 拓扑类型 | 说明 | 适用场景 |
|----------|------|----------|
| `sequential` | 链式：TaskBuilder → Executor → Judge → Analyzer | 简单评测流程 |
| `parallel` | 并行：多个 Executor 同时执行同一任务 | 交叉验证 |
| `tree` | 树状：TaskBuilder 分发任务给多个 Executor | 大规模评测 |
| `graph` | 图状：任意 Agent 间可通信 | 复杂协作模式 |
| `debate` | 辩论：多个 Judge 对抗性评估 | 对抗性评测 |

```python
# 通信拓扑代码
class Topology(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    TREE = "tree"
    GRAPH = "graph"
    DEBATE = "debate"

class AgentCommunication:
    def __init__(self, topology: Topology):
        self.topology = topology
        self.message_bus = MessageBus()
        self.agent_registry = AgentRegistry()

    def send_message(self, from_agent: str, to_agent: str, message: Message):
        """发送消息"""
        if self._validate_path(from_agent, to_agent):
            self.message_bus.publish(f"{from_agent}->{to_agent}", message)

    def broadcast(self, from_agent: str, message: Message):
        """广播消息"""
        valid_targets = self._get_valid_targets(from_agent)
        for target in valid_targets:
            self.message_bus.publish(f"{from_agent}->{target}", message)
```

### 3.2 插件系统 (Plugin System)

#### 3.2.1 插件基类设计

```python
# 指标插件基类
class MetricPlugin(ABC):
    """所有评测指标的基类"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.version = "1.0.0"

    @abstractmethod
    def compute(
        self,
        scenario: Scenario,
        output: Dict[str, Any],
        trace: Trace
    ) -> MetricResult:
        """计算指标值"""
        pass

    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证配置是否合法"""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """返回指标元信息"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.__doc__,
            "dimensions": self.dimensions
        }

# 评判插件基类
class JudgePlugin(ABC):
    """评判器基类"""

    @abstractmethod
    def judge(
        self,
        task: Task,
        output: Any,
        criteria: List[Criterion]
    ) -> JudgmentResult:
        """执行评判"""
        pass

# 场景插件基类
class ScenarioPlugin(ABC):
    """评测场景基类"""

    @abstractmethod
    def generate_tasks(self, config: ScenarioConfig) -> List[Task]:
        """生成测试任务"""
        pass

    @abstractmethod
    def validate_completion(self, task: Task, result: Any) -> bool:
        """验证任务完成情况"""
        pass
```

#### 3.2.2 插件注册机制

```python
# 插件注册表
class PluginRegistry:
    _instance = None

    def __init__(self):
        self.metrics = {}
        self.judges = {}
        self.scenarios = {}
        self._load_builtin_plugins()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_metric(self, name: str, plugin_class: Type[MetricPlugin]):
        """注册指标插件"""
        self.metrics[name] = plugin_class

    def register_judge(self, name: str, plugin_class: Type[JudgePlugin]):
        """注册评判插件"""
        self.judges[name] = plugin_class

    def register_scenario(self, name: str, plugin_class: Type[ScenarioPlugin]):
        """注册场景插件"""
        self.scenarios[name] = plugin_class

    def get_metric(self, name: str) -> Type[MetricPlugin]:
        return self.metrics.get(name)

    def load_custom_plugin(self, module_path: str):
        """加载用户自定义插件"""
        spec = importlib.util.spec_from_file_location("custom", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # 从模块中提取插件类并注册
```

### 3.3 评测维度 (Metrics)

#### 3.3.1 内置评测维度

| 维度 | 说明 | 指标项 |
|------|------|--------|
| **Tool Calling** | 工具调用能力 | 选择准确率、参数正确率、错误恢复率 |
| **MCP Usage** | MCP 协议使用 | 协议合规性、工具链调用、状态管理 |
| **Knowledge Recall** | 知识召回 | 召回率、准确率、相关性排序 |
| **Collaboration** | 多 Agent 协作 | 任务分解、信息传递、共识达成 |
| **Planning** | 规划能力 | 步骤完整性、自我纠错、回溯能力 |
| **Safety** | 安全边界 | 越权操作检测、信息泄露、注入攻击 |
| **Efficiency** | 效率指标 | 执行时间、Token 消耗、成本 |

#### 3.3.2 指标实现示例

```python
# 工具调用指标
class ToolCallingMetric(MetricPlugin):
    dimensions = ["precision", "recall", "param_accuracy", "recovery"]

    def compute(self, scenario, output, trace) -> MetricResult:
        tool_calls = self._extract_tool_calls(trace)

        results = {
            "precision": self._calc_precision(scenario, tool_calls),
            "recall": self._calc_recall(scenario, tool_calls),
            "param_accuracy": self._calc_param_accuracy(tool_calls),
            "recovery": self._calc_recovery_rate(trace)
        }

        return MetricResult(
            dimension="tool_calling",
            scores=results,
            weight={"precision": 0.3, "recall": 0.3, "param_accuracy": 0.2, "recovery": 0.2}
        )

# MCP 使用指标
class MCPUsageMetric(MetricPlugin):
    """评估 Agent 对 MCP 协议的使用能力"""

    def compute(self, scenario, output, trace) -> MetricResult:
        mcp_calls = self._extract_mcp_calls(trace)

        results = {
            "protocol_compliance": self._check_protocol(mcp_calls),
            "tool_chain_execution": self._eval_tool_chain(mcp_calls),
            "state_management": self._check_state_handling(mcp_calls),
            "error_handling": self._eval_error_handling(mcp_calls)
        }

        return MetricResult(dimension="mcp_usage", scores=results)

# 协作能力指标
class CollaborationMetric(MetricPlugin):
    """评估多 Agent 协作能力"""

    def compute(self, scenario, output, trace) -> MetricResult:
        results = {
            "task_division": self._eval_task_division(trace),
            "info_propagation": self._eval_info_flow(trace),
            "consensus_achievement": self._eval_consensus(trace),
            "context_isolation": self._eval_context_leak(trace),  # 参考 AgentCollabBench CLC
            "constraint_maintenance": self._eval_constraint(trace)  # 参考 AgentCollabBench IDR
        }

        return MetricResult(dimension="collaboration", scores=results)
```

### 3.4 场景定义 (Scenario)

#### 3.4.1 场景 Schema

```yaml
# scenario_example.yaml
name: "代码审查评测"
description: "评估 Agent 在代码审查场景下的表现"
category: "code_quality"

# 场景配置
config:
  difficulty: "medium"  # easy / medium / hard
  language: "python"    # python / javascript / go / ...

# 被测 Agent 配置
agent_under_test:
  type: "code_reviewer"
  tools:
    - name: "read_file"
      description: "读取文件内容"
    - name: "search_code"
      description: "搜索代码"
    - name: "write_comment"
      description: "添加评论"

# 协作团队配置（可选）
team:
  roles:
    - id: "reviewer"
      prompt: "你是一个严格的代码审查员..."
    - id: "author"
      prompt: "你提交了一段代码供审查..."
  topology: "sequential"

# 评测维度
metrics:
  - name: "tool_calling"
    weight: 0.3
  - name: "code_understanding"
    weight: 0.3
  - name: "safety"
    weight: 0.2
  - name: "efficiency"
    weight: 0.2

# 评判配置
judge:
  type: "hybrid"
  llm_judge:
    provider: "openai"
    model: "gpt-4"
  script_checks:
    - name: "no_placeholder"
      description: "不能有空实现"
    - name: "proper_summary"
      description: "需要给出审查总结"
```

#### 3.4.2 任务 Schema

```json
// task_example.json
{
  "task_id": "code_review_001",
  "scenario": "code_review",
  "difficulty": "medium",
  "description": "审查以下代码的安全漏洞",
  "context": {
    "language": "python",
    "code_snippet": "...",
    "requirements": ["SQL注入检测", "XSS检测"]
  },
  "expected_outcome": {
    "security_issues_found": ["SQL注入在第23行", "XSS在第45行"],
    "has_summary": true,
    "has_suggestions": true
  },
  "ground_truth": {
    "issues": [
      {"line": 23, "type": "sql_injection", "severity": "high"},
      {"line": 45, "type": "xss", "severity": "medium"}
    ]
  },
  "time_limit": 120,
  "token_budget": 5000
}
```

### 3.5 评判系统 (Judge)

#### 3.5.1 评判类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| **LLM Judge** | 用大模型评判 | 开放式任务、代码质量、内容评估 |
| **Script Judge** | 用脚本校验 | 有明确答案的客观评测 |
| **Human Judge** | 人工审核 | 高价值场景、需要主观判断 |
| **Hybrid Judge** | 混合模式 | 结合多种方式取最优 |

#### 3.5.2 LLM Judge 实现

```python
class LLMJudge(JudgePlugin):
    def __init__(self, provider: str, model: str, criteria: List[Criterion]):
        self.provider = LLMProviderFactory.get(provider)
        self.model = model
        self.criteria = criteria

    def judge(self, task: Task, output: Any, context: Dict) -> JudgmentResult:
        prompt = self._build_judge_prompt(task, output, context)

        response = self.provider.generate(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )

        parsed = self._parse_response(response)

        return JudgmentResult(
            scores={c.name: parsed[c.name] for c in self.criteria},
            feedback=parsed.get("feedback"),
            suggestions=parsed.get("suggestions")
        )

    def _build_judge_prompt(self, task, output, context) -> str:
        return f"""
你是一个严格的评测裁判。请评估以下任务完成情况：

任务描述：{task.description}
任务要求：{task.requirements}
执行结果：{output}

评分标准：
{chr(10).join([f"- {c.name}: {c.description}" for c in self.criteria])}

请以 JSON 格式返回评分：
{{
    "scores": {{"标准名": 分数(0-1)}},
    "feedback": "详细反馈",
    "suggestions": "改进建议"
}}
"""
```

### 3.6 框架适配器 (Adapters)

#### 3.6.1 支持的框架

| 框架 | 适配器 | 说明 |
|------|--------|------|
| **AutoGen** | `autogen/` | Microsoft 多 Agent 框架 |
| **CrewAI** | `crewai/` | 角色扮演 Agent 框架 |
| **LangGraph** | `langgraph/` | LangChain 状态机 |
| **MCP** | `mcp/` | Model Context Protocol |
| **自定义** | `custom/` | 用户自己的 Agent 实现 |

#### 3.6.2 适配器接口

```python
class AgentAdapter(ABC):
    """Agent 适配器基类"""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """初始化 Agent"""
        pass

    @abstractmethod
    def execute(self, task: Task) -> ExecutionResult:
        """执行任务"""
        pass

    @abstractmethod
    def get_trace(self) -> Trace:
        """获取执行轨迹"""
        pass

    @abstractmethod
    def get_available_tools(self) -> List[Tool]:
        """获取可用工具列表"""
        pass

# MCP 适配器示例
class MCPAdapter(AgentAdapter):
    def __init__(self, config: Dict[str, Any]):
        self.server_config = config["mcp_server"]
        self.tools = []

    def initialize(self, config):
        # 连接 MCP 服务器
        self.client = MCPClient(self.server_config)
        self.tools = self.client.list_tools()

    def execute(self, task: Task) -> ExecutionResult:
        # 通过 MCP 协议执行
        return self.client.call_tool(task.tool_name, task.params)

    def get_trace(self) -> Trace:
        return self.client.get_session_trace()

    def get_available_tools(self) -> List[Tool]:
        return [Tool.from_mcp(t) for t in self.tools]
```

---

## 四、评测流程

### 4.1 标准评测流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           评测执行流程                                       │
│                                                                              │
│  1. 初始化                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • 加载场景配置    • 初始化被测 Agent    • 初始化评测团队              │   │
│  │ • 加载指标插件    • 初始化评判器        • 建立通信连接                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  2. 任务生成 (Task Builder)                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 输入: 评测目标 + 能力维度                                              │   │
│  │ 处理: 生成多样化测试用例                                              │   │
│  │ 输出: Task List                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  3. 执行评测 (Executor)                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 输入: Task + Agent                                                   │   │
│  │ 处理: 运行被测 Agent，收集 Trace                                      │   │
│  │ 输出: Execution Result + Trace                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  4. 评判打分 (Judge)                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 输入: Task + Result + Criteria                                        │   │
│  │ 处理: 多维度评分                                                      │   │
│  │ 输出: Scores + Feedback                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  5. 结果分析 (Analyzer)                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 输入: All Scores + Traces                                            │   │
│  │ 处理: 汇总统计 + 问题诊断 + 报告生成                                  │   │
│  │ 输出: Evaluation Report                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  6. 结果输出                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • 控制台输出    • JSON 报告    • 可视化图表    • 对比分析              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 多 Agent 协作流程

```
                        Task Builder
                            │
                            ▼
                   ┌─────────────────┐
                   │   生成任务列表   │
                   └────────┬────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
      ┌──────────┐    ┌──────────┐    ┌──────────┐
      │ Executor1 │    │ Executor2 │    │ Executor3 │
      │ (Agent 1) │    │ (Agent 2) │    │ (Agent 3) │
      └────┬─────┘    └────┬─────┘    └────┬─────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                   ┌─────────────────┐
                   │   结果汇总      │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   多 Judge 评判  │
                   │ (交叉验证模式)   │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   综合分析报告   │
                   └─────────────────┘
```

### 4.3 迭代优化流程（可选）

```python
# 支持多轮迭代优化
ITERATION_CONFIG = {
    "enabled": True,
    "max_iterations": 3,
    "stop_condition": {
        "score_threshold": 0.9,  # 达到 90% 即可停止
        "no_improvement": 2     # 连续 2 轮无提升则停止
    },
    "feedback_mode": "with_correction"  # Judge 给出修正建议
}

# 迭代流程
def iterative_evaluation(task, agent):
    best_result = None
    best_score = 0

    for i in range(max_iterations):
        result = execute(task, agent)
        score, feedback = judge(task, result)

        if score > best_score:
            best_result = result
            best_score = score

        if stop_condition_met(score, i):
            break

        # 将反馈提供给 Agent 进行修正
        agent.refine(feedback)

    return best_result, best_score
```

---

## 五、API 设计

### 5.1 Python SDK

```python
from agent_eval_platform import (
    Platform,
    Scenario,
    Metric,
    AgentAdapter,
    JudgeConfig
)

# 初始化平台
platform = Platform()

# 加载场景
scenario = platform.load_scenario("code_review")

# 配置被测 Agent
agent = platform.register_agent(
    adapter=AgentAdapter.AutoGen,
    config={"model": "gpt-4", "tools": [...]}
)

# 配置评测指标
metrics = [
    Metric.tool_calling(weight=0.3),
    Metric.mcp_usage(weight=0.2),
    Metric.collaboration(weight=0.3),
    Metric.safety(weight=0.2)
]

# 配置评判器
judge = JudgeConfig.llm_judge(
    provider="openai",
    model="gpt-4",
    criteria=["correctness", "efficiency", "safety"]
)

# 执行评测
result = platform.evaluate(
    scenario=scenario,
    agent=agent,
    metrics=metrics,
    judge=judge,
    iterations=1
)

# 获取报告
print(result.summary())
result.save("report.json")
result.plot_radar_chart("radar.html")
```

### 5.2 CLI 命令

```bash
# 基本用法
agent-eval run --scenario code_review --agent my_agent.py

# 指定指标
agent-eval run --scenario code_review --metrics tool_calling,mcp_usage,safety

# 指定评判方式
agent-eval run --scenario code_review --judge llm --judge-model gpt-4

# 批量评测
agent-eval batch --scenarios-dir ./scenarios --output ./results

# 生成报告
agent-eval report --input ./results/eval_001.json --format html

# 插件管理
agent-eval plugin list
agent-eval plugin install ./my_metric.py
agent-eval plugin uninstall my_custom_metric
```

### 5.3 REST API

```
POST   /api/v1/evaluations          # 创建评测任务
GET    /api/v1/evaluations/{id}     # 获取评测结果
POST   /api/v1/agents               # 注册被测 Agent
GET    /api/v1/scenarios            # 获取场景列表
POST   /api/v1/plugins              # 上传自定义插件
GET    /api/v1/reports/{eval_id}    # 获取报告
```

---

## 六、评测维度详解

### 6.1 Tool Calling（工具调用）

| 指标 | 说明 | 计算方式 |
|------|------|----------|
| **选择准确率** | 是否选择了正确的工具 | 正确选择数 / 总选择数 |
| **参数正确率** | 调用参数是否正确 | 正确参数数 / 总参数数 |
| **调用时序** | 工具调用顺序是否合理 | 拓扑相似度计算 |
| **错误恢复** | 工具调用失败后是否正确恢复 | 恢复次数 / 错误次数 |

### 6.2 MCP Usage（MCP 使用）

| 指标 | 说明 | 参考标准 |
|------|------|----------|
| **协议合规性** | 是否正确遵循 MCP 协议 | MCP 规范检查 |
| **工具链执行** | 多工具协同调用能力 | 依赖图匹配度 |
| **状态管理** | 会话状态维护能力 | 状态一致性 |
| **错误处理** | MCP 错误响应处理 | 错误分类准确率 |

### 6.3 Knowledge Recall（知识召回）

| 指标 | 说明 | 计算方式 |
|------|------|----------|
| **召回率** | 相关知识被召回的比例 | 相关召回 / 全部相关 |
| **准确率** | 召回知识的准确程度 | 准确召回 / 全部召回 |
| **相关性排序** | 知识按相关性排序的能力 | NDCG 分数 |
| **幻觉检测** | 是否产生幻觉内容 | 幻觉语句占比 |

### 6.4 Collaboration（协作能力）

| 指标 | 说明 | 来源 |
|------|------|------|
| **任务分解** | 分解任务的合理性 | 自定义 |
| **信息传递** | Agent 间信息传递完整性 | AgentCollabBench RTD |
| **共识达成** | 团队共识形成的质量 | 自定义 |
| **上下文隔离** | 任务间上下文不泄露 | AgentCollabBench CLC |
| **约束保持** | 不受压力影响保持约束 | AgentCollabBench IDR |
| **共识污染** | 虚假信息不扩散 | AgentCollabBench CPR |

### 6.5 Planning（规划能力）

| 指标 | 说明 | 计算方式 |
|------|------|----------|
| **步骤完整性** | 完成任务所需步骤的完整度 | 步骤覆盖率 |
| **自我纠错** | 发现并修正错误的能力 | 修正次数 / 错误次数 |
| **回溯能力** | 错误后回退到正确状态 | 回溯操作占比 |
| **资源规划** | Token/时间预算管理 | 预算使用效率 |

### 6.6 Safety（安全边界）

| 指标 | 说明 | 检测方式 |
|------|------|----------|
| **越权操作** | 是否尝试执行未授权操作 | 权限矩阵检查 |
| **信息泄露** | 是否泄露敏感信息 | 敏感信息检测 |
| **注入攻击** | 是否尝试 Prompt 注入 | 注入模式检测 |
| **数据破坏** | 是否意外修改/删除数据 | 数据完整性检查 |

---

## 七、参考项目汇总

| 项目 | GitHub | 关键参考点 |
|------|--------|------------|
| **AgentCollabBench** | ariora741/AgentCollabBench | 多 Agent 协作指标体系（IDR/RTD/CPR/CLC） |
| **AgentBench** | THUDM/AgentBench | 分布式架构、容器化部署 |
| **MCPBench** | arXiv | MCP 协议评测维度 |
| **BFCL** | Vellum-ai/bfcl | 函数调用评测 |
| **AgentOps** | agentops-ai/agentops | Agent 追踪监控 |
| **multi-agent-assessment** | bgagandeep/multi-agent-assessment-framework | 框架对比思路 |

---

## 八、实施计划建议

### 阶段一：核心框架（4 周）
- [ ] 项目结构搭建
- [ ] 插件系统实现
- [ ] 基础评测引擎
- [ ] 内置指标实现（Tool Calling、MCP Usage）

### 阶段二：协作功能（4 周）
- [ ] Agent 团队管理
- [ ] 通信拓扑实现
- [ ] 协作指标（基于 AgentCollabBench）
- [ ] LLM Judge

### 阶段三：平台能力（3 周）
- [ ] Web UI
- [ ] CLI 工具
- [ ] REST API
- [ ] 报告生成

### 阶段四：生态建设（持续）
- [ ] 更多指标插件
- [ ] 更多场景模板
- [ ] 框架适配器
- [ ] 社区贡献

---

## 九、总结

本设计文档提供了一个**完整的、可扩展的多 Agent 协作式 Agent 评测平台**架构：

### 核心优势

1. **全面覆盖** - 覆盖 Agent 特有能力（工具/MCP/协作/规划/安全）
2. **灵活扩展** - 插件化架构支持用户自定义
3. **协作评测** - 创新的多 Agent "命题-执行-评判" 模式
4. **行业领先** - 填补多 Agent 协作评测空白

### 关键设计

- **插件化架构** - 指标、评判、场景均可插拔
- **Schema 标准化** - 任务定义统一，支持导入导出
- **多 Agent 协作** - 内置协作协议，支持自定义拓扑
- **混合评判** - LLM + 脚本 + 人工组合

---

*文档版本：v1.0*
*最后更新：2025-10-11*
