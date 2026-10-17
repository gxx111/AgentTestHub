"""
Stage 0 Model Connectivity & Evaluation Team Smoke Test Script.
Validates:
1. Direct Chat/Completions connectivity with GLM-5.3.
2. 4-role Evaluation Team (user_simulator, business_judge, safety_judge, moderator).
3. smolagents ToolCallingAgent with OpenAIServerModel and db_execute tool.

Security Constraint:
- Never print or leak API keys in stdout/stderr.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

from dotenv import load_dotenv
import httpx
from smolagents import OpenAIServerModel, ToolCallingAgent, tool


def mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def load_config() -> tuple[str, str, str]:
    # Load from .env.local if present
    load_dotenv(".env.local")
    base_url = os.getenv("AGENT_TEST_HUB_MODEL_BASE_URL", "").rstrip("/")
    api_key = os.getenv("AGENT_TEST_HUB_MODEL_API_KEY", "")
    model_name = os.getenv("AGENT_TEST_HUB_MODEL_NAME", "GLM-5.3")

    if not base_url or not api_key:
        print("[FAIL] Missing AGENT_TEST_HUB_MODEL_BASE_URL or AGENT_TEST_HUB_MODEL_API_KEY")
        sys.exit(1)

    return base_url, api_key, model_name


def test_model_connectivity(base_url: str, api_key: str, model_name: str) -> bool:
    print("\n--- [Step 1] Model Connectivity (GLM-5.3) ---")
    print(f"Target Base URL: {base_url}")
    print(f"Target Model: {model_name}")
    print(f"API Key: {mask_key(api_key)}")

    start_time = time.time()
    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "messages": [
                    {"role": "user", "content": "请回复四个字：连通成功"}
                ],
                "max_tokens": 800,
                "temperature": 0.1,
            },
            timeout=30.0,
        )
        latency = (time.time() - start_time) * 1000
        if response.status_code == 200:
            data = response.json()
            message = data["choices"][0]["message"]
            content = message.get("content", "").strip()
            print(f"[PASS] Status Code: 200, Latency: {latency:.1f}ms")
            print(f"Sample Output: {content[:80]}")
            return True
        else:
            print(f"[FAIL] HTTP {response.status_code}: {response.text[:200]}")
            return False
    except Exception as exc:
        latency = (time.time() - start_time) * 1000
        print(f"[FAIL] Connectivity Exception ({type(exc).__name__}) after {latency:.1f}ms: {exc}")
        return False


def test_evaluation_team(base_url: str, api_key: str, model_name: str) -> bool:
    print("\n--- [Step 2] 4-Role Evaluation Team Verification ---")
    roles = ["user_simulator", "business_judge", "safety_judge", "moderator"]
    all_ok = True

    for role in roles:
        start_time = time.time()
        try:
            sys_prompt = f"你是评测团队成员，角色为 {role}。请以 JSON 格式输出状态确认：{{\"role\": \"{role}\", \"status\": \"ready\"}}。"
            response = httpx.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": "请汇报角色就绪状态。"},
                    ],
                    "max_tokens": 800,
                    "temperature": 0.0,
                },
                timeout=30.0,
            )
            latency = (time.time() - start_time) * 1000
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"].get("content", "").strip()
                print(f"[PASS] Role [{role}] ready in {latency:.1f}ms")
            else:
                print(f"[FAIL] Role [{role}] HTTP {response.status_code}")
                all_ok = False
        except Exception as exc:
            print(f"[FAIL] Role [{role}] error: {type(exc).__name__}: {exc}")
            all_ok = False

    return all_ok


@tool
def db_execute(sql: str) -> str:
    """Executes a SQL query in the SQLite database.

    Args:
        sql: The SQL query statement to execute.
    """
    return json.dumps([{"order_id": "ORD_999", "amount": 199.0, "status": "PENDING"}])


def test_smolagents_testee(base_url: str, api_key: str, model_name: str) -> bool:
    print("\n--- [Step 3] smolagents Testee Tool Calling Verification ---")
    start_time = time.time()
    try:
        model = OpenAIServerModel(
            model_id=model_name,
            api_base=base_url,
            api_key=api_key,
            max_tokens=1500,
        )

        agent = ToolCallingAgent(
            tools=[db_execute],
            model=model,
            max_steps=3,
        )

        prompt = "请调用 db_execute 工具查询订单列表：SELECT * FROM orders;"
        result = agent.run(prompt)
        latency = (time.time() - start_time) * 1000
        print(f"[PASS] smolagents ToolCallingAgent completed tool execution in {latency:.1f}ms")
        print(f"Agent Final Output: {str(result)[:100]}")
        return True
    except Exception as exc:
        latency = (time.time() - start_time) * 1000
        print(f"[FAIL] smolagents tool calling error after {latency:.1f}ms: {type(exc).__name__}: {exc}")
        return False


def main():
    print("=" * 60)
    print("AgentTestHub Stage 0: Environment & Model Connectivity Smoke Test")
    print("=" * 60)

    base_url, api_key, model_name = load_config()

    s1 = test_model_connectivity(base_url, api_key, model_name)
    if not s1:
        print("\n[ABORT] Model connectivity test failed.")
        sys.exit(1)

    s2 = test_evaluation_team(base_url, api_key, model_name)
    if not s2:
        print("\n[ABORT] Evaluation team test failed.")
        sys.exit(1)

    s3 = test_smolagents_testee(base_url, api_key, model_name)
    if not s3:
        print("\n[ABORT] smolagents testee test failed.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] All Stage 0 Smoke Tests Passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
