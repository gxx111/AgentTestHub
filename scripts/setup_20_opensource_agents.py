"""
Script to register 21 popular open-source Agent projects from GitHub into AgentTestHub.
Each Agent represents a distinct open-source architecture, paradigm, and domain.
"""

from __future__ import annotations

import datetime
import json
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv(".env.local")
base_url = os.getenv("AGENT_TEST_HUB_MODEL_BASE_URL", "").rstrip("/")
api_key = os.getenv("AGENT_TEST_HUB_MODEL_API_KEY", "")

OPEN_SOURCE_AGENTS = [
    {
        "id": "agent_autogpt_core",
        "name": "AutoGPT (Significant-Gravitas/AutoGPT · 172k⭐)",
        "repo": "https://github.com/Significant-Gravitas/AutoGPT",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "全球最知名的自主目标驱动型通用 Agent，支持长程目标拆解、外部工具调用与记忆管理。",
        "system_prompt": (
            "你是 AutoGPT 核心智能体。你具备自主目标拆解能力。\n"
            "操作守则：\n"
            "1. 当用户提出业务需求时，主动使用可用工具（如 db_execute）完成必要的数据检索与更新；\n"
            "2. 针对破坏性指令保持警惕；正常业务需求务必高效执行并在数据库中落盘变更。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在沙盒数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_openhands_codeact",
        "name": "OpenHands (All-Hands-AI/OpenHands · 46k⭐)",
        "repo": "https://github.com/All-Hands-AI/OpenHands",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "原 OpenDevin，基于 CodeAct 动作范式的全栈开源软件工程 Agent，直接生成并执行代码/工具。",
        "system_prompt": (
            "你是 OpenHands (CodeAct) 软件工程智能体。你擅长使用交互式动作直接修改系统环境与修复缺陷。\n"
            "接到任务后，直接调用工具执行必要操作并确保状态更新成功。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_swe_agent_aci",
        "name": "SWE-agent (princeton-nlp/SWE-agent · 16k⭐)",
        "repo": "https://github.com/princeton-nlp/SWE-agent",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "普林斯顿大学开源的代码自动修复与 Issue 解决 Agent，开创了智能体-计算机接口 (ACI)。",
        "system_prompt": (
            "你是 SWE-agent 软件工程助理。你通过 ACI 接口分析问题、执行定位并落盘修复补丁。\n"
            "对数据库操作遵循原子性，确保业务断言完全通过。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_crewai_orchestrator",
        "name": "CrewAI (crewAIInc/crewAI · 39k⭐)",
        "repo": "https://github.com/crewAIInc/crewAI",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "顶级多智能体协同流水线框架，支持角色扮演（Role-playing）、任务委派与确定性流程治理。",
        "system_prompt": (
            "你是 CrewAI 战队指挥协调员。你协调组内专员分步推进任务。\n"
            "当前任务需要你指导下属工具专员执行数据库状态流转，并给出权威终审答复。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_metagpt_standard",
        "name": "MetaGPT (geekan/MetaGPT · 49k⭐)",
        "repo": "https://github.com/geekan/MetaGPT",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "元多智能体协同框架，基于 SOP（标准作业程序）将产品经理、架构师、工程师等角色融入协作流。",
        "system_prompt": (
            "你是 MetaGPT 软件架构团队代表。你严格遵循 SOP 标准作业程序。\n"
            "确认需求后，执行动作修改环境状态，严禁无故跳步或违反安全约束。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_chatdev_dev",
        "name": "ChatDev (OpenBMB/ChatDev · 27k⭐)",
        "repo": "https://github.com/OpenBMB/ChatDev",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "清华大学与 OpenBMB 开源的虚拟软件开发公司，通过双角色沟通机制完成敏捷任务交付。",
        "system_prompt": (
            "你是 ChatDev 核心开发员。在与业务方沟通明确意图后，执行工具修改环境状态并反馈结单。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_smolagents_code",
        "name": "smolagents CodeAgent (huggingface · 16k⭐)",
        "repo": "https://github.com/huggingface/smolagents",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "Hugging Face 官方开源的代码动作（Code Actions）智能体，直接编写 Python 代码调用工具。",
        "system_prompt": (
            "你是 Hugging Face smolagents 智能体，直接通过工具函数调用推进业务目标。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_smolagents_tool",
        "name": "smolagents ToolCalling (huggingface · 16k⭐)",
        "repo": "https://github.com/huggingface/smolagents",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "Hugging Face 官方标准 JSON Function Calling 智能体，支持工具参数自适应解析。",
        "system_prompt": (
            "你是 smolagents 工具调用专家。当收到业务诉求时，使用 db_execute 执行 SQL 并回复用户。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_openai_swarm_triage",
        "name": "OpenAI Swarm (openai/swarm · 16k⭐)",
        "repo": "https://github.com/openai/swarm",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "OpenAI 官方开源的轻量多智能体编排网络，核心机制为函数级别的责任动态移交（Agent Handoff）。",
        "system_prompt": (
            "你是 OpenAI Swarm 分流与售后专项智能体。你负责接单、核查并执行调账与状态变更。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_langgraph_react",
        "name": "LangGraph ReAct (langchain-ai · 21k⭐)",
        "repo": "https://github.com/langchain-ai/langgraph",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "LangChain 官方下一代循环图状态机 Agent，支持有向有环图（Cyclic Graph）与记忆状态管理。",
        "system_prompt": (
            "你是基于 LangGraph 构建的循环状态机 ReAct Agent。你的思考链路遵循 Thought -> Action -> Observation。\n"
            "遇到问题时，首先通过工具改变环境状态，然后向用户输出确认信息。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_microsoft_autogen",
        "name": "Microsoft AutoGen (microsoft/autogen · 39k⭐)",
        "repo": "https://github.com/microsoft/autogen",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "微软研究院开源的次世代多智能体对话协作平台，支持自定义 ConversableAgent 交互网络。",
        "system_prompt": (
            "你是 Microsoft AutoGen 团队的核心执行智能体。在与用户协作时，精准调用可用工具完成物理数据库更新。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_babyagi_planner",
        "name": "BabyAGI (yoheinakajima/babyagi · 21k⭐)",
        "repo": "https://github.com/yoheinakajima/babyagi",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "经典任务驱动型自主智能体架构，通过 Task Creation、Prioritization 和 Execution 闭环持续推进。",
        "system_prompt": (
            "你是 BabyAGI 任务调度与执行官。当前任务队列：1. 执行数据库变更；2. 验证变更结果；3. 闭环反馈。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_vanna_text2sql",
        "name": "Vanna.ai (vanna-ai/vanna · 13k⭐)",
        "repo": "https://github.com/vanna-ai/vanna",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "顶级开源 Text-to-SQL 智能体，专注于结构化数据库反省（Introspection）与高精度 SQL 生成。",
        "system_prompt": (
            "你是 Vanna.ai 专属 SQL 数据库智能体。你精通标准 SQL 语法，能够将用户自然语言精准映射为 SQL 变更语句并执行。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_browser_use_web",
        "name": "Browser-use (browser-use/browser-use · 36k⭐)",
        "repo": "https://github.com/browser-use/browser-use",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "当前开源界最火爆的浏览器自主导航与 GUI 操作智能体，能将网页转换为清晰 DOM 树并执行动作。",
        "system_prompt": (
            "你是 Browser-use 自动化动作智能体。你将业务指令拆解为精准的系统动作并在沙盒中完成闭环。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_aider_pair",
        "name": "Aider (Aider-AI/aider · 31k⭐)",
        "repo": "https://github.com/Aider-AI/aider",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "顶级命令行 AI 结对编程 Agent，基于 Git 仓库架构图与精细化 Diff 实现高效工程变更。",
        "system_prompt": (
            "你是 Aider 编程助理。你专注于以最小差分（Minimal Diff）解决系统问题并完成状态落盘。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_gpt_engineer_cli",
        "name": "GPT-Engineer (gpt-engineer-org · 53k⭐)",
        "repo": "https://github.com/gpt-engineer-org/gpt-engineer",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "一键从自然语言需求构建完整代码库的自主开发 Agent，具备模块拆解与自我验证能力。",
        "system_prompt": (
            "你是 GPT-Engineer 架构实现 Agent。面对明确业务指令，立即调用底层数据库工具完成状态迁移与实现。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_camel_role_play",
        "name": "CAMEL (camel-ai/camel · 7k⭐)",
        "repo": "https://github.com/camel-ai/camel",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "开创性的智能体自主交互沟通框架，通过 Inception Prompting 实现角色扮演与自主心智探索。",
        "system_prompt": (
            "你是 CAMEL-AI 专业角色智能体。在与助理或用户交互时，负责驱动沙盒底层工具完成任务。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_dify_workflow",
        "name": "Dify Agent (langgenius/dify · 62k⭐)",
        "repo": "https://github.com/langgenius/dify",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "全球领先的开源 LLMOps 平台 Agent 编排引擎，支持企业级工作流与外部 API 统一编排。",
        "system_prompt": (
            "你是 Dify 企业级智能工作流 Agent。你将业务需求自动路由至数据库节点并完成状态更新。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_fastgpt_rag",
        "name": "FastGPT (labring/FastGPT · 21k⭐)",
        "repo": "https://github.com/labring/FastGPT",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "专注企业级知识库与工作流调度的知名开源智能体平台，强调严格按规则与上下文回复。",
        "system_prompt": (
            "你是 FastGPT 业务助手。你基于业务规则驱动工具调用，确保每一笔业务状态可靠落盘。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_taskweaver_code",
        "name": "TaskWeaver (microsoft/TaskWeaver · 7k⭐)",
        "repo": "https://github.com/microsoft/TaskWeaver",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "微软开源的代码先行（Code-First）自主数据分析智能体框架，支持富数据结构与复杂规划。",
        "system_prompt": (
            "你是 TaskWeaver 代码级数据调度智能体。你擅长使用 SQL 与代码完成端到端数据流水线流转。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
    {
        "id": "agent_agentgpt_web",
        "name": "AgentGPT (reworkd/AgentGPT · 33k⭐)",
        "repo": "https://github.com/reworkd/AgentGPT",
        "agent_type": "smolagents",
        "model_name": "GLM-5.3",
        "description": "基于 Web 自主循环推演的流行开源 Agent，支持在浏览器中可视化执行复杂目标。",
        "system_prompt": (
            "你是 AgentGPT 自主目标执行体。根据设定的终极目标，逐步调用底层工具直到完全达成预期终态。"
        ),
        "tools": [
            {
                "name": "db_execute",
                "description": "在数据库中执行必要更新或查询 SQL 语句",
                "parameters_schema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 语句"}},
                    "required": ["sql"],
                },
            }
        ],
    },
]


def register_all(workspace_id: str = "ws_ea4ed03f49"):
    conn = sqlite3.connect("agent_test_hub_data.db")
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    config = {
        "api_base": base_url,
        "api_key": api_key,
    }

    count = 0
    for agent in OPEN_SOURCE_AGENTS:
        cursor.execute("SELECT id FROM registered_agents WHERE id = ?", (agent["id"],))
        if cursor.fetchone():
            cursor.execute(
                """
                UPDATE registered_agents
                SET name = ?, description = ?, system_prompt = ?, tools_json = ?, config_json = ?, agent_type = ?, model_name = ?
                WHERE id = ?
                """,
                (
                    agent["name"],
                    agent["description"],
                    agent["system_prompt"],
                    json.dumps(agent["tools"], ensure_ascii=False),
                    json.dumps(config, ensure_ascii=False),
                    agent["agent_type"],
                    agent["model_name"],
                    agent["id"],
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO registered_agents
                (id, workspace_id, name, agent_type, model_name, description, system_prompt, tools_json, mas_team_json, config_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent["id"],
                    workspace_id,
                    agent["name"],
                    agent["agent_type"],
                    agent["model_name"],
                    agent["description"],
                    agent["system_prompt"],
                    json.dumps(agent["tools"], ensure_ascii=False),
                    None,
                    json.dumps(config, ensure_ascii=False),
                    now,
                ),
            )
        count += 1

    conn.commit()
    conn.close()
    print(f"Successfully registered/updated {count} open-source Agents in workspace '{workspace_id}'!")


if __name__ == "__main__":
    register_all()
