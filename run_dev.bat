@echo off
chcp 65001 >nul
echo ========================================================
echo   AgentTestHub 2.1 全栈服务一键启动脚本 (Windows)
echo ========================================================
echo.

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo [1/2] 正在启动 FastAPI 后端服务 (端口: 8005)...
start "AgentTestHub Backend (FastAPI)" cmd /k ".venv\Scripts\python.exe -m uvicorn agent_test_hub_server.app:app --host 127.0.0.1 --port 8005 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] 正在启动 Next.js Web 竞技场 (端口: 3005)...
start "AgentTestHub Web Arena (Next.js)" cmd /k "cd apps\web && pnpm dev -p 3005"

echo.
echo ========================================================
echo   服务已就绪！请访问以下地址：
echo   - Web 竞技场大屏:   http://localhost:3005
echo   - FastAPI API 文档: http://127.0.0.1:8005/docs
echo ========================================================
echo.
pause
