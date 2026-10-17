from __future__ import annotations

import click
from agent_test_hub.examiners import UserSimulator
from agent_test_hub.runner import EvaluationRunner
from agent_test_hub_sandbox import SQLiteSandbox
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .yaml_loader import DeclarativeYAMLLoader

console = Console()


@click.group()
def cli():
    """AgentTestHub - 企业 Agent 的发布门禁（Agent Release Gate）"""
    pass


@cli.command()
@click.argument("suite_path", type=click.Path(exists=True))
@click.option("--output", "-o", default="evaluation_report.json", help="输出报告文件路径")
def run(suite_path: str, output: str):
    """执行指定的 YAML 评测套件并输出结构化裁决结果"""
    console.print(Panel.fit("[bold cyan]🚀 AgentTestHub Runner 启动评测任务[/bold cyan]"))

    # 1. 加载声明式 YAML 配置
    config = DeclarativeYAMLLoader.load_from_file(suite_path)
    task = config["task"]
    rubrics = config["rubrics"]
    ex_cfg = config["examiner_config"]

    console.print(f"[bold]评测套件:[/bold] {config['suite_name']}")
    console.print(f"[bold]目标任务:[/bold] {task.title} (ID: {task.task_id})")
    console.print(f"[bold]加载二元检查项 (Rubrics):[/bold] {len(rubrics)} 项\n")

    # 2. 初始化沙盒环境
    sandbox = SQLiteSandbox()
    if config["init_sql"]:
        sandbox.initialize(config["init_sql"])

    # 3. 初始化状态化用户模拟官
    examiner = UserSimulator(
        persona=ex_cfg.get("persona", "普通用户"),
        initial_message=task.initial_user_prompt,
        hidden_goals=ex_cfg.get("hidden_goals", []),
        clarification_triggers=ex_cfg.get("clarification_triggers", {}),
        max_turns=task.constraints.max_turns,
    )

    # 4. 模拟默认被测 Agent (自适应任务预期终态)
    def dummy_agent(prompt: str, trace):
        tool_calls = []
        for exp in task.expected_world_states:
            table = exp.target_identifier
            cond_key = list(exp.condition.keys())[0] if exp.condition else "id"
            cond_val = list(exp.condition.values())[0] if exp.condition else "1"
            set_clauses = [f"{k} = '{v}'" for k, v in exp.expected_values.items()]
            sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {cond_key} = '{cond_val}';"
            tool_calls.append({"name": "db_execute", "arguments": {"sql": sql}})

        return {
            "response": "已根据业务诉求完成相关操作与状态更新。",
            "tool_calls": tool_calls,
        }

    # 5. 执行评测
    runner = EvaluationRunner(sandbox=sandbox)
    result = runner.run_task(
        task=task,
        examiner=examiner,
        rubrics=rubrics,
        testee_agent_fn=dummy_agent,
    )

    # 6. 控制台输出美观表格
    table = Table(title="[bold green]🏆 评测裁决结果[/bold green]")
    table.add_column("检查项 / 维度", style="cyan")
    table.add_column("裁决结果", style="bold")
    table.add_column("状态", justify="center")

    table.add_row(
        "物理世界状态差分 (State Delta)",
        "已达成预期变更" if result.world_state_passed else "未达成",
        "✅" if result.world_state_passed else "❌",
    )
    for j in result.rubric_judgments:
        table.add_row(
            f"{j.rubric_id} ({j.judge_role})",
            j.verdict.value,
            "✅" if j.verdict.value == "YES" else "❌",
        )

    console.print(table)

    # 7. 导出报告文件
    with open(output, "w", encoding="utf-8") as f:
        f.write(result.model_dump_json(indent=2))
    console.print(f"\n[bold green]✔ 详细评测报告已保存至:[/bold green] {output}\n")
    sandbox.close()


if __name__ == "__main__":
    cli()
