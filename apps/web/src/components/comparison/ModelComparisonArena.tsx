"use client";

import React, { useState } from "react";
import {
  Trophy,
  Bot,
  Zap,
  CheckCircle2,
  XCircle,
  Clock,
  Coins,
  ArrowUpRight,
  TrendingUp,
} from "lucide-react";
import { BenchmarkCaseInfo } from "../matrix/TestMatrixTable";

interface ModelArenaProps {
  testCases: BenchmarkCaseInfo[];
}

export function ModelComparisonArena({ testCases }: ModelArenaProps) {
  const models = [
    {
      id: "deepseek",
      name: "DeepSeek-V3",
      provider: "DeepSeek",
      passRate: "100%",
      avgLatency: "680ms",
      costPer1k: "$0.002",
      rank: "Top 1",
      scores: [1.0, 1.0, 1.0, 1.0],
    },
    {
      id: "gpt4o",
      name: "GPT-4o",
      provider: "OpenAI",
      passRate: "100%",
      avgLatency: "940ms",
      costPer1k: "$0.015",
      rank: "Top 2",
      scores: [1.0, 1.0, 1.0, 1.0],
    },
    {
      id: "claude35",
      name: "Claude 3.5 Sonnet",
      provider: "Anthropic",
      passRate: "100%",
      avgLatency: "1120ms",
      costPer1k: "$0.018",
      rank: "Top 3",
      scores: [1.0, 1.0, 1.0, 1.0],
    },
    {
      id: "baseline",
      name: "企业内建自适应 Agent",
      provider: "Local Baseline",
      passRate: "100%",
      avgLatency: "120ms",
      costPer1k: "$0.000",
      rank: "基线",
      scores: [1.0, 1.0, 1.0, 1.0],
    },
  ];

  return (
    <div className="w-full space-y-6">
      {/* 顶部天梯榜榜首卡片 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {models.map((m, idx) => (
          <div
            key={m.id}
            className={`glass-panel rounded-2xl p-5 border relative overflow-hidden transition-all ${
              idx === 0
                ? "border-cyber-cyan/50 shadow-xl shadow-cyber-cyan/10"
                : "border-white/10"
            }`}
          >
            {idx === 0 && (
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyber-cyan to-cyber-azure" />
            )}
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/10 text-slate-300">
                {m.provider}
              </span>
              <span
                className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded ${
                  idx === 0
                    ? "bg-amber-flame/15 text-amber-flame border border-amber-flame/30"
                    : "bg-white/5 text-slate-400"
                }`}
              >
                {m.rank}
              </span>
            </div>
            <h3 className="text-sm font-bold text-slate-100 font-mono mb-2">{m.name}</h3>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-3 border-t border-white/5">
              <div>
                <span className="text-[10px] text-slate-500 block">综合通过率</span>
                <span className="text-emerald-pulse font-bold">{m.passRate}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block">平均耗时</span>
                <span className="text-cyber-azure font-bold">{m.avgLatency}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 横向多模型用例对比矩阵 (Promptfoo 对比大表) */}
      <div className="glass-panel rounded-2xl border border-white/10 overflow-hidden shadow-2xl">
        <div className="p-4 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Trophy className="w-4 h-4 text-amber-flame" />
            <h3 className="text-sm font-bold text-slate-100 font-mono">
              横向模型对抗天梯矩阵 (Model Arena Comparison)
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            同一评测套件 · 跨大模型横向并发对比
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-white/10 bg-obsidian-950/80 text-slate-400 text-[11px] uppercase">
                <th className="py-3 px-4 w-64">测试用例 (Test Case)</th>
                {models.map((m) => (
                  <th key={m.id} className="py-3 px-4 text-center">
                    <div>{m.name}</div>
                    <span className="text-[9px] text-slate-500 lowercase">({m.provider})</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {testCases.map((c, caseIdx) => (
                <tr key={c.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3.5 px-4">
                    <div className="font-bold text-slate-200 line-clamp-1">{c.title}</div>
                    <span className="text-[10px] text-slate-500 font-mono">{c.id}</span>
                  </td>
                  {models.map((m) => (
                    <td key={m.id} className="py-3.5 px-4 text-center">
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-pulse/10 border border-emerald-pulse/20 text-emerald-pulse font-bold text-[11px]">
                        <CheckCircle2 className="w-3.5 h-3.5" /> 100%
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
