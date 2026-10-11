import pytest
from agent_test_hub.schemas import ExecutionTrace, TraceEvent, ActorRole, TraceEventType
from agent_test_hub.examiners import UserSimulator, RedTeamAttacker


def test_user_simulator_hidden_goal_fsm():
    """测试用户模拟官在接收 Agent 澄清提问后，逐步释放隐藏诉求的状态机"""
    sim = UserSimulator(
        persona="焦急的买家",
        initial_message="我的包裹破损了，我要退款！",
        hidden_goals=["提供开箱视频与破损照片"],
        clarification_triggers={"凭证": "我已经上传了开箱破损照片在附件里，请查收"},
        max_turns=5,
    )

    trace = ExecutionTrace(task_id="t1")

    # 第 1 轮：初始发问
    act1 = sim.act(trace, turn_index=1)
    assert act1.action_type == "speak"
    assert "包裹破损" in act1.content

    # 模拟 Agent 在第 1 轮追问“请问您有开箱凭证吗？”
    trace = ExecutionTrace(
        task_id="t1",
        events=[
            TraceEvent(
                turn_index=1,
                actor_role=ActorRole.TESTEE_AGENT,
                event_type=TraceEventType.AGENT_MESSAGE,
                content="非常抱歉给您带来不便，请问您有开箱凭证吗？",
            )
        ],
    )

    # 第 2 轮：触发状态机，释放隐藏意图
    act2 = sim.act(trace, turn_index=2)
    assert act2.action_type == "speak"
    assert "开箱破损照片" in act2.content
    assert "凭证" in act2.internal_state["revealed_goals"]


def test_red_team_crescendo_attack_progression():
    """测试对抗攻防红队官的阶梯渐进式攻击演变"""
    attacker = RedTeamAttacker()
    trace = ExecutionTrace(task_id="red_01")

    act1 = attacker.act(trace, turn_index=1)
    assert act1.internal_state["attack_phase"] == "reconnaissance"

    act2 = attacker.act(trace, turn_index=2)
    assert act2.internal_state["attack_phase"] == "prompt_leakage_probing"
    assert "system_prompt" in act2.content

    act3 = attacker.act(trace, turn_index=3)
    assert act3.internal_state["attack_phase"] == "destructive_injection"
    assert "DROP TABLE" in act3.content
