import pytest
from agent_test_hub.runner import EvaluationRunner
from agent_test_hub.examiners import UserSimulator
from agent_test_hub_sandbox import SQLiteSandbox
from agent_test_hub_cli.yaml_loader import DeclarativeYAMLLoader


def test_end_to_end_ecommerce_refund_benchmark():
    """端到端集成测试：加载官方电商退款场景，执行全流程评测并校验裁决"""
    yaml_path = "benchmarks/ecommerce_refund/refund_benchmark.yaml"
    config = DeclarativeYAMLLoader.load_from_file(yaml_path)

    task = config["task"]
    rubrics = config["rubrics"]
    ex_cfg = config["examiner_config"]

    sandbox = SQLiteSandbox()
    sandbox.initialize(config["init_sql"])

    examiner = UserSimulator(
        persona=ex_cfg["persona"],
        initial_message=task.initial_user_prompt,
        hidden_goals=ex_cfg["hidden_goals"],
        clarification_triggers=ex_cfg["clarification_triggers"],
        max_turns=task.constraints.max_turns,
    )

    # 模拟一个高质量、符合美团/阿里大厂标准的被测客服 Agent
    def realistic_support_agent(user_prompt: str, trace):
        # 第 1 轮：检测到包裹破损，主动索取开箱凭证
        if "破损" in user_prompt and "凭证" not in user_prompt:
            return {
                "response": "非常抱歉给您带来不便，请问您是否有开箱破损凭证？上传后我立刻为您办理退款！",
                "tool_calls": [],
            }
        # 第 2 轮：用户提供了凭证，执行沙盒数据库退款
        return {
            "response": "已收到您的开箱凭证并核验通过，已为您办理退款取消！",
            "tool_calls": [
                {
                    "name": "db_execute",
                    "arguments": {
                        "sql": "UPDATE orders SET status = 'CANCELLED' WHERE order_id = 'ORD_1001';"
                    },
                }
            ],
        }

    runner = EvaluationRunner(sandbox=sandbox)
    result = runner.run_task(task, examiner, rubrics, realistic_support_agent)

    # 验证最终各项断言
    assert result.is_passed is True
    assert result.world_state_passed is True
    assert result.total_score == 1.0
    # 2 项 Rubric × 2 位异构盲审法官 (RuleJudge + SafetyJudge) = 4 条审理明细
    assert len(result.rubric_judgments) == 4
    # 状态差分记录确实更新了 orders 表
    assert len(result.world_state_diff["modified_records"]) == 1
    assert result.world_state_diff["modified_records"][0]["new"]["status"] == "CANCELLED"
    sandbox.close()
