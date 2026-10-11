#!/usr/bin/env bash
set -e

echo "========================================================"
echo "  AgentTestHub 2.1 全栈服务一键启动脚本 (Linux/macOS)"
echo "========================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 优雅退出钩子
cleanup() {
    echo ""
    echo "正在停止所有服务..."
    kill $(jobs -p) 2>/dev/null || true
    echo "服务已停止。"
}
trap cleanup EXIT INT TERM

echo "[1/2] 正在启动 FastAPI 后端服务 (端口: 8005)..."
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD -m uvicorn agent_test_hub_server.app:app --host 127.0.0.1 --port 8005 --reload &
BACKEND_PID=$!

sleep 2

echo "[2/2] 正在启动 Next.js Web 竞技场 (端口: 3005)..."
cd apps/web && pnpm dev -p 3005 &
FRONTEND_PID=$!

echo ""
echo "========================================================"
echo "  服务已启动！请在浏览器中访问："
echo "  - Web 竞技场大屏:   http://localhost:3005"
echo "  - FastAPI 接口文档: http://127.0.0.1:8005/docs"
echo "  (按 Ctrl+C 停止所有服务)"
echo "========================================================"
echo ""

wait
