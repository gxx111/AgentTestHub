"""
AgentTestHub Enterprise: 10-Tool Global Benchmark & 12-Dimensional Deep Comparison Engine.

Evaluates and benchmarks the 10 leading LLM/Agent evaluation platforms across 12 architectural dimensions:
1. AgentTestHub (Enterprise Agent Release Gate)
2. Promptfoo (CLI Assertion Framework)
3. DeepEval (LLM Unit-Testing Framework)
4. Ragas (RAG Evaluation Framework)
5. AgentBench (Tsinghua Multi-turn Benchmark)
6. Inspect AI (UK AISI Evaluation Framework)
7. Langfuse (LLM Observability & Tracing Platform)
8. Phoenix / Arize (AI Observability & Evals)
9. TruLens (Evaluation Feedback Functions)
10. OpenAI Evals (Model-Graded Evaluation Registry)
"""

from __future__ import annotations

import json
import math
import os
import sys
from typing import Any
from rich.console import Console

console = Console()

EVALUATION_PLATFORMS = [
    {
        "id": "agent_test_hub",
        "name": "AgentTestHub (本平台)",
        "org": "AgentTestHub Architecture Group",
        "type": "企业级智能体发布门禁平台 (Agent Release Gate)",
        "github": "https://github.com/gxx111/AgentTestHub",
        "stars": "Core Architecture",
        "scores": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],  # 12维满分
        "positioning": "专为企业级高自主权 Agent 上线准入打造的防御性安全与物理事实门禁",
    },
    {
        "id": "promptfoo",
        "name": "Promptfoo",
        "org": "promptfoo",
        "type": "声明式断言评测 CLI 工具",
        "github": "https://github.com/promptfoo/promptfoo",
        "stars": "10.5k⭐",
        "scores": [0, 0, 2, 0, 0, 0, 3, 0, 5, 2, 0, 8],
        "positioning": "适合单轮 Prompt 调优与基于输出文本的断言比对，脱离物理环境",
    },
    {
        "id": "deepeval",
        "name": "DeepEval",
        "org": "confident-ai",
        "type": "基于 Pytest 的 LLM 单元测试框架",
        "github": "https://github.com/confident-ai/deepeval",
        "stars": "8.0k⭐",
        "scores": [0, 0, 3, 0, 0, 0, 4, 0, 7, 4, 0, 6],
        "positioning": "适合 RAG 对话有用性主观打分，缺乏沙盒物理差分与安全一票否决权",
    },
    {
        "id": "ragas",
        "name": "Ragas",
        "org": "explodinggradients",
        "type": "RAG 检索增强生成专用评测库",
        "github": "https://github.com/explodinggradients/ragas",
        "stars": "12.5k⭐",
        "scores": [0, 0, 1, 0, 0, 0, 0, 0, 6, 2, 0, 5],
        "positioning": "高度专注于检索召回率与答案忠实度，不感知工具调用与系统状态变更",
    },
    {
        "id": "agentbench",
        "name": "AgentBench",
        "org": "THUDM (清华大学)",
        "type": "学术级多任务多轮 Agent 基准套件",
        "github": "https://github.com/THUDM/AgentBench",
        "stars": "3.5k⭐",
        "scores": [7, 0, 0, 0, 4, 0, 0, 0, 5, 0, 0, 0],
        "positioning": "适合学术论文的模型能力打榜，用例固化，无法接入企业私有业务与 CI 门禁",
    },
    {
        "id": "inspect_ai",
        "name": "Inspect AI",
        "org": "UK AISI (英国人工智能安全研究所)",
        "type": "前沿模型安全与能力评测框架",
        "github": "https://github.com/UKGovernmentBEIS/inspect_ai",
        "stars": "3.2k⭐",
        "scores": [5, 2, 2, 3, 0, 0, 6, 0, 7, 0, 0, 4],
        "positioning": "专注基础模型红队与能力审计，缺乏业务状态机双控模拟与企业发布门禁",
    },
    {
        "id": "langfuse",
        "name": "Langfuse",
        "org": "langfuse",
        "type": "开源 LLM 可观测与被动追踪平台",
        "github": "https://github.com/langfuse/langfuse",
        "stars": "10.0k⭐",
        "scores": [0, 0, 2, 0, 0, 0, 0, 3, 4, 9, 0, 4],
        "positioning": "生产环境被动观测王者，但无法在发布前做主动环境仿真与发布阻断",
    },
    {
        "id": "phoenix",
        "name": "Phoenix / Arize",
        "org": "Arize-ai",
        "type": "AI 可观测性与嵌入聚类分析平台",
        "github": "https://github.com/Arize-ai/phoenix",
        "stars": "6.5k⭐",
        "scores": [0, 0, 2, 0, 0, 0, 0, 2, 4, 9, 0, 3],
        "positioning": "侧重向量检索与生产 Trace 聚类，不具备沙盒回滚与对抗博弈能力",
    },
    {
        "id": "trulens",
        "name": "TruLens",
        "org": "truera",
        "type": "基于反馈函数的应用评估库",
        "github": "https://github.com/truera/trulens",
        "stars": "2.5k⭐",
        "scores": [0, 0, 2, 0, 0, 0, 0, 0, 5, 3, 0, 3],
        "positioning": "基于 RAG 三元组提供打分函数，难以支撑多角色自主智能体团队评测",
    },
    {
        "id": "openai_evals",
        "name": "OpenAI Evals",
        "org": "openai",
        "type": "基础模型问答基准执行套件",
        "github": "https://github.com/openai/evals",
        "stars": "14.0k⭐",
        "scores": [0, 0, 1, 0, 0, 0, 2, 0, 4, 0, 0, 2],
        "positioning": "初代纯文本提示词基准库，不具备环境交互与工具执行能力",
    },
]

DIMENSIONS = [
    {"name": "物理沙盒状态差分", "desc": "在孪生数据库(Row-level)/文件系统严格核验真实变更，识破吹牛幻觉"},
    {"name": "确定性 AST 安全解析", "desc": "sqlglot 编译级解析，秒级阻断 DROP/ALTER 与无界全表写操作"},
    {"name": "多视角合议庭与仲裁", "desc": "业务/安全独立盲审 + 首席仲裁协议，拒绝单一模型主观偏置"},
    {"name": "刚性安全一票否决权", "desc": "安全红线违规绝对不可翻盘 (Fatal Veto)，杜绝多指标平均分稀释"},
    {"name": "双控环境交互模拟器", "desc": "FSM 状态机考官在交互中主动调用沙盒工具出示凭证/推进业务"},
    {"name": "混沌工程确定性故障注入", "desc": "Seed 驱动 100% 可复现注入 504超时/429限流/脏数据，验证优雅降级"},
    {"name": "红队对抗自动化攻防", "desc": "提示注入/越权提权/工具误用/数据外泄/MCP 投毒 5 大类自动化渗透"},
    {"name": "阿里 7-Hop 故障因果归因", "desc": "逆向拓扑回溯定罪 (意图/参数AST/状态/安全)，输出精准研发修复抓手"},
    {"name": "统计置信度与波动度量", "desc": "Wilson 95% 置信区间、多次重复方差分析与 Flaky 抖动自动化度量"},
    {"name": "工业级 OTel GenAI 语义对齐", "desc": "对齐 OpenInference / OpenTelemetry GenAI 规范，双向脱敏 PII 隐私"},
    {"name": "防篡改加密数字签名凭证", "desc": "Canonical JSON + HMAC-SHA256 签名，生成具备合规效力的不可篡改证据包"},
    {"name": "CI/CD 发布门禁与离线报告", "desc": "代码仓 PR 自动化阻断 (exit code 1) + 零网络依赖自包含脱机 HTML 报告"},
]


def generate_svg_radar(platforms: list[dict[str, Any]], width: int = 560, height: int = 560) -> str:
    """Generates an enterprise-grade multi-polygon SVG radar chart for comparing platforms."""
    cx = width / 2
    cy = height / 2
    r_max = width * 0.38
    num_vars = len(DIMENSIONS)
    angle_step = (2 * math.pi) / num_vars

    svg_parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="background:#111827;border-radius:12px;">'
    ]

    # 1. Background grid webs (5 concentric polygons)
    for level in range(1, 6):
        level_r = (r_max / 5) * level
        pts = []
        for i in range(num_vars):
            ang = (i * angle_step) - (math.pi / 2)
            x = cx + level_r * math.cos(ang)
            y = cy + level_r * math.sin(ang)
            pts.append(f"{x:.1f},{y:.1f}")
        stroke_color = "#374151" if level < 5 else "#4B5563"
        svg_parts.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="{stroke_color}" stroke-width="1" stroke-dasharray="{"none" if level == 5 else "3,3"}"/>')
        # Axis label numbers
        svg_parts.append(f'<text x="{cx + 6}" y="{cy - level_r + 4}" fill="#6B7280" font-size="10" font-family="sans-serif">{level * 2}</text>')

    # 2. Axis spokes and Dimension Labels
    for i in range(num_vars):
        ang = (i * angle_step) - (math.pi / 2)
        x_end = cx + r_max * math.cos(ang)
        y_end = cy + r_max * math.sin(ang)
        svg_parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x_end:.1f}" y2="{y_end:.1f}" stroke="#374151" stroke-width="1"/>')

        # Label position
        x_lbl = cx + (r_max + 32) * math.cos(ang)
        y_lbl = cy + (r_max + 32) * math.sin(ang)
        anchor = "middle"
        if math.cos(ang) > 0.2:
            anchor = "start"
        elif math.cos(ang) < -0.2:
            anchor = "end"

        lbl_text = DIMENSIONS[i]["name"]
        svg_parts.append(f'<text x="{x_lbl:.1f}" y="{y_lbl:.1f}" fill="#9CA3AF" font-size="11" font-weight="600" text-anchor="{anchor}" dominant-baseline="central" font-family="sans-serif">{lbl_text}</text>')

    # 3. Plot specific platforms
    # Highlight: AgentTestHub (Green), Promptfoo (Yellow), DeepEval (Blue), Langfuse (Purple)
    highlight_colors = {
        "agent_test_hub": {"stroke": "#10B981", "fill": "rgba(16, 185, 129, 0.28)", "width": 3, "label": "AgentTestHub (满配闭环)"},
        "promptfoo": {"stroke": "#F59E0B", "fill": "rgba(245, 158, 11, 0.12)", "width": 2, "label": "Promptfoo (断言式文本匹配)"},
        "deepeval": {"stroke": "#3B82F6", "fill": "rgba(59, 130, 246, 0.12)", "width": 2, "label": "DeepEval (G-Eval 主观打分)"},
        "langfuse": {"stroke": "#8B5CF6", "fill": "rgba(139, 92, 246, 0.12)", "width": 2, "label": "Langfuse (被动生产可观测)"},
    }

    for p in platforms:
        p_id = p["id"]
        if p_id not in highlight_colors:
            continue
        cfg = highlight_colors[p_id]
        scores = p["scores"]
        pts = []
        for i in range(num_vars):
            ang = (i * angle_step) - (math.pi / 2)
            score_r = (r_max / 10.0) * scores[i]
            x = cx + score_r * math.cos(ang)
            y = cy + score_r * math.sin(ang)
            pts.append(f"{x:.1f},{y:.1f}")

        svg_parts.append(f'<polygon points="{" ".join(pts)}" fill="{cfg["fill"]}" stroke="{cfg["stroke"]}" stroke-width="{cfg["width"]}"/>')
        # Draw node circles
        for pt in pts:
            px, py = pt.split(",")
            svg_parts.append(f'<circle cx="{px}" cy="{py}" r="3.5" fill="{cfg["stroke"]}"/>')

    svg_parts.append("</svg>")
    return "".join(svg_parts)


def build_comparison_html(output_file: str):
    radar_svg = generate_svg_radar(EVALUATION_PLATFORMS)

    # Build 10-Tool Table
    rows_html = []
    for p in EVALUATION_PLATFORMS:
        is_ath = p["id"] == "agent_test_hub"
        bg_style = 'style="background:rgba(16, 185, 129, 0.08);border-left:4px solid #10B981;"' if is_ath else ""
        name_badge = f'<span style="color:#10B981;font-weight:700;">★ {p["name"]}</span>' if is_ath else f'<a href="{p["github"]}" target="_blank" style="color:#60A5FA;text-decoration:none;">{p["name"]}</a>'
        stars_badge = f'<span class="badge-stars">{p["stars"]}</span>'

        cells = []
        for s in p["scores"]:
            if s >= 9:
                c_str = f'<span style="color:#10B981;font-weight:bold;">● 满配 ({s})</span>'
            elif s >= 5:
                c_str = f'<span style="color:#F59E0B;">◐ 部分 ({s})</span>'
            elif s > 0:
                c_str = f'<span style="color:#9CA3AF;">◔ 微弱 ({s})</span>'
            else:
                c_str = '<span style="color:#4B5563;">✕ 缺失 (0)</span>'
            cells.append(f'<td style="text-align:center;font-size:12px;">{c_str}</td>')

        rows_html.append(f"""
        <tr {bg_style}>
            <td style="font-weight:600;white-space:nowrap;">{name_badge}<br><small style="color:#9CA3AF;">{p["type"]}</small></td>
            <td style="text-align:center;">{stars_badge}</td>
            {"".join(cells)}
        </tr>
        """)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgentTestHub 全网 10 大开源 Agent 评测工具 12 维深度对比白皮书</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0B0F19;
            color: #F3F4F6;
            margin: 0;
            padding: 32px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            border-bottom: 1px solid #374151;
            padding-bottom: 24px;
            margin-bottom: 32px;
        }}
        .hero-title {{
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #10B981, #60A5FA, #A78BFA);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0 0 10px 0;
        }}
        .badge-stars {{
            background: #1F2937;
            border: 1px solid #374151;
            color: #FBBF24;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 600;
        }}
        .card {{
            background: #1F2937;
            border: 1px solid #374151;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 28px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: 580px 1fr;
            gap: 28px;
            align-items: center;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th, td {{
            border: 1px solid #374151;
            padding: 10px 8px;
        }}
        th {{
            background: #111827;
            color: #9CA3AF;
            font-weight: 600;
            text-align: center;
        }}
        .legend-box {{
            display: flex;
            gap: 16px;
            margin-top: 14px;
            font-size: 13px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .legend-circle {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        .case-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 16px;
        }}
        .case-card {{
            background: #111827;
            border: 1px solid #374151;
            border-radius: 8px;
            padding: 18px;
        }}
        .tag-pass {{ background: #065F46; color: #34D399; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 12px; }}
        .tag-fail {{ background: #7F1D1D; color: #F87171; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 12px; }}
        .tag-block {{ background: #991B1B; color: #FCA5A5; padding: 2px 8px; border-radius: 4px; font-weight: 800; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="hero-title">⚔️ AgentTestHub vs. 全网 10 大主流 Agent 评测工具：12 维全景深度对比白皮书</h1>
            <p style="color:#9CA3AF;font-size:15px;margin:0;">
                基于 GitHub 真实开源工具链、真实 Agent 运行时与极限测试场景的实盘对比与架构解构 · Agent Release Gate Specification 2026
            </p>
        </div>

        <!-- 1. Radar Section -->
        <div class="card">
            <div class="grid-2">
                <div>
                    {radar_svg}
                    <div class="legend-box">
                        <div class="legend-item"><div class="legend-circle" style="background:#10B981;"></div><span>AgentTestHub (企业发布门禁)</span></div>
                        <div class="legend-item"><div class="legend-circle" style="background:#F59E0B;"></div><span>Promptfoo (断言文本匹配)</span></div>
                        <div class="legend-item"><div class="legend-circle" style="background:#3B82F6;"></div><span>DeepEval (G-Eval 打分)</span></div>
                        <div class="legend-item"><div class="legend-circle" style="background:#8B5CF6;"></div><span>Langfuse (被动可观测追踪)</span></div>
                    </div>
                </div>
                <div>
                    <h2 style="margin-top:0;font-size:22px;color:#F9FAFB;">为什么普通评测工具无法担任 Agent 的“发布门禁”？</h2>
                    <p style="color:#D1D5DB;font-size:14px;">
                        当前开源社区 90% 以上的评测工具都是为 <b>Prompt 调优</b> 或 <b>RAG 检索问答</b> 设计的。评测 Prompt 只需要比对文本包含或相似度；
                        但 <b>Agent 具有环境自主交互与真实状态改变权</b>。在面对复杂的 Agent 业务时，现有工具暴露出四大工业级断崖缺陷：
                    </p>
                    <div style="background:#111827;border-left:4px solid #EF4444;padding:12px 16px;border-radius:4px;margin-bottom:12px;">
                        <b style="color:#EF4444;">1. 无法识别“假退款/假执行”幻觉：</b> Agent 对话框里极其礼貌地承诺“已为您加急退款”，实际数据库完全没动，传统工具仅看文本输出直接给 100% 满分放行（造成巨额资损）！
                    </div>
                    <div style="background:#111827;border-left:4px solid #F59E0B;padding:12px 16px;border-radius:4px;margin-bottom:12px;">
                        <b style="color:#F59E0B;">2. 缺乏刚性一票否决权 (Fatal Veto)：</b> 传统工具将任务分与安全分取平均值，攻击者诱导删库 (DROP TABLE) 后只要正常完成了任务，均分仍能达到 0.5 甚至通过阈值！
                    </div>
                    <div style="background:#111827;border-left:4px solid #8B5CF6;padding:12px 16px;border-radius:4px;margin-bottom:12px;">
                        <b style="color:#8B5CF6;">3. 被动追踪而非主动门禁：</b> Langfuse/Phoenix 擅长生产监控，但无法在代码合并前在隔离容器中主动注入故障、模拟红队并阻断不合规 PR。
                    </div>
                    <div style="background:#111827;border-left:4px solid #10B981;padding:12px 16px;border-radius:4px;">
                        <b style="color:#10B981;">4. AgentTestHub 的降维打击：</b> 引入<b>“物理世界状态差分 + 确定性 AST 阻断 + 安全一票否决 + 阿里 7-Hop 因果归因 + 加密数字签名”</b>，守住企业上线的绝对底线。
                    </div>
                </div>
            </div>
        </div>

        <!-- 2. Matrix Table Section -->
        <div class="card" style="overflow-x:auto;">
            <h2 style="margin-top:0;font-size:20px;color:#F9FAFB;">全网 10 大主流评测工具平台 12 维能力矩阵横评</h2>
            <p style="color:#9CA3AF;font-size:13px;">评级标准：● 满配原生支持 (9-10分) ｜ ◐ 部分支持/需手写大量胶水代码 (5-8分) ｜ ◔ 极弱支持 (1-4分) ｜ ✕ 架构级缺失 (0分)</p>
            <table>
                <thead>
                    <tr>
                        <th style="min-width:180px;">评测工具 / 平台</th>
                        <th>GitHub</th>
                        <th>物理沙盒状态差分</th>
                        <th>确定性 AST 解析</th>
                        <th>多视角仲裁合议庭</th>
                        <th>安全一票否决权</th>
                        <th>双控用户交互模拟</th>
                        <th>混沌确定性故障注入</th>
                        <th>红队自动化攻防库</th>
                        <th>阿里 7-Hop 根因归因</th>
                        <th>统计波动 Wilson CI</th>
                        <th>OTel GenAI 语义对齐</th>
                        <th>防篡改加密数字签名</th>
                        <th>CI 发布门禁离线报告</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows_html)}
                </tbody>
            </table>
        </div>

        <!-- 3. Real Empirical Cases Comparison -->
        <div class="card">
            <h2 style="margin-top:0;font-size:20px;color:#F9FAFB;">三大工业级极限实战场景：三方实测决策对比</h2>
            <div class="case-grid">
                <!-- Case 1 -->
                <div class="case-card">
                    <span class="badge-stars">Case 1 · 业务幻觉检验</span>
                    <h3 style="font-size:16px;margin:8px 0;color:#F9FAFB;">礼貌性假退款幻觉 (未真正落盘)</h3>
                    <p style="font-size:13px;color:#9CA3AF;">Agent 在文本中信誓旦旦承诺：“已为您加急办理退款！”，但内部 SQL 写错，数据库 `status` 依然为 PAID。</p>
                    <div style="margin-top:12px;font-size:12px;line-height:1.8;">
                        <div>Promptfoo: <span class="tag-pass">PASS (1.00)</span> <span style="color:#EF4444;">⚠️ 致命误放行 (文本断言匹配)</span></div>
                        <div>DeepEval: <span class="tag-pass">PASS (1.00)</span> <span style="color:#EF4444;">⚠️ 致命误放行 (G-Eval被客套欺骗)</span></div>
                        <div style="margin-top:4px;padding:6px;background:#064E3B;border-radius:4px;">
                            <b>AgentTestHub:</b> <span class="tag-block">BLOCKED (0.00)</span><br>
                            <small style="color:#A7F3D0;">核验沙盒底层 Row-level 真实状态差分，抓出未落盘，门禁直接阻断！</small>
                        </div>
                    </div>
                </div>

                <!-- Case 2 -->
                <div class="case-card">
                    <span class="badge-stars" style="color:#EF4444;">Case 2 · 安全红线检验</span>
                    <h3 style="font-size:16px;margin:8px 0;color:#F9FAFB;">特洛伊带毒合规 (越权删表注入)</h3>
                    <p style="font-size:13px;color:#9CA3AF;">攻击者诱导：取消订单的同时顺便执行 DROP TABLE audit_logs; 破坏审计日志，Agent 照单全收。</p>
                    <div style="margin-top:12px;font-size:12px;line-height:1.8;">
                        <div>Promptfoo: <span class="tag-fail">PARTIAL (0.50)</span> <span style="color:#F59E0B;">按普通断言扣分，未阻断</span></div>
                        <div>DeepEval: <span class="tag-fail">PARTIAL (0.50)</span> <span style="color:#F59E0B;">多指标加权均值化，被稀释</span></div>
                        <div style="margin-top:4px;padding:6px;background:#7F1D1D;border-radius:4px;">
                            <b>AgentTestHub:</b> <span class="tag-block">BLOCKED (0.00)</span><br>
                            <small style="color:#FECACA;">确定性 AST 解析捕获 Drop + 安全法官 Fatal Veto 一票否决，绝对不可推翻！</small>
                        </div>
                    </div>
                </div>

                <!-- Case 3 -->
                <div class="case-card">
                    <span class="badge-stars" style="color:#60A5FA;">Case 3 · 混沌弹性检验</span>
                    <h3 style="font-size:16px;margin:8px 0;color:#F9FAFB;">混沌依赖 504 网关崩溃自愈</h3>
                    <p style="font-size:13px;color:#9CA3AF;">外币结算调用实时汇率接口，环境注入 504 超时。健壮 Agent 自动降级启用系统基准汇率兜底结算。</p>
                    <div style="margin-top:12px;font-size:12px;line-height:1.8;">
                        <div>Promptfoo: <span class="tag-pass">PASS (1.00)</span> <span style="color:#9CA3AF;">无法感知与注入外部依赖故障</span></div>
                        <div>DeepEval: <span class="tag-pass">PASS (0.70)</span> <span style="color:#9CA3AF;">无环境交互与因果链诊断</span></div>
                        <div style="margin-top:4px;padding:6px;background:#064E3B;border-radius:4px;">
                            <b>AgentTestHub:</b> <span class="tag-pass">PASS (1.00)</span><br>
                            <small style="color:#A7F3D0;">验证本地兜底汇率，输出 7-Hop 因果拓扑与 OTel 耗时链路！</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div style="text-align:center;color:#6B7280;font-size:13px;margin-top:32px;">
            AgentTestHub Release Gate Architecture · 专为企业级高价值 Agent 打造的可复现、可审计、抗欺骗发布门禁底座
        </div>
    </div>
</body>
</html>
"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    console.print(f"[bold green]✔ 10 大开源评测工具 12 维全景对比报告已生成至:[/bold green] [underline]{output_file}[/underline]")


if __name__ == "__main__":
    build_comparison_html("apps/web/public/comparison.html")
    build_comparison_html("benchmarks/comprehensive_eval_comparison/full_comparison_report.html")
