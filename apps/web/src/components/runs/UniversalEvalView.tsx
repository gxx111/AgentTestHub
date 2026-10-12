"use client";

import React, { useState, useEffect } from "react";
import {
  Play,
  RotateCw,
  History,
  CheckCircle2,
  XCircle,
  Clock,
  Bot,
  Database,
  ArrowRight,
  TrendingUp,
  Sparkles,
} from "lucide-react";

export function UniversalEvalView() {
  const [agents, setAgents] = useState<any[]>([]);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [runs, setRuns] = useState<any[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [currentRunResult, setCurrentRunResult] = useState<any>(null);

  const fetchData = async () => {
    try {
      const [agRes, dsRes, runRes] = await Promise.all([
        fetch("http://localhost:8005/api/v1/agents"),
        fetch("http://localhost:8005/api/v1/datasets"),
        fetch("http://localhost:8005/api/v1/evaluations/runs"),
      ]);
      if (agRes.ok) {
        const agData = await agRes.json();
        setAgents(agData);
        if (agData.length > 0 && !selectedAgentId) setSelectedAgentId(agData[0].id);
      }
      if (dsRes.ok) {
        const dsData = await dsRes.json();
        setDatasets(dsData);
        if (dsData.length > 0 && !selectedDatasetId) setSelectedDatasetId(dsData[0].id);
      }
      if (runRes.ok) {
        setRuns(await runRes.json());
      }
    } catch (_) {}
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleLaunchRun = async () => {
    if (!selectedAgentId || !selectedDatasetId) return;
    setIsRunning(true);
    setCurrentRunResult(null);

    try {
      const res = await fetch("http://localhost:8005/api/v1/evaluations/universal-run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workspace_id: "ws_primary",
          agent_id: selectedAgentId,
          dataset_id: selectedDatasetId,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentRunResult(data);
        fetchData();
      }
    } catch (_) {}
    setIsRunning(false);
  };

  return (
    <div className="w-full space-y-6 font-sans">
      {/* 顶部通用调度面板 */}
      <div className="glass-panel rounded-2xl p-6 border border-white/10 space-y-5">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyber-cyan/15 text-cyber-cyan border border-cyber-cyan/30 uppercase font-bold">
                通用评测调度总线
              </span>
              <h2 className="text-sm font-bold text-slate-100 font-mono tracking-tight">
                发起多智能体协同评测 (Universal Evaluation Launchpad)
              </h2>
            </div>
            <p className="text-xs text-slate-400 font-sans">
              自由组合：选择已注册的任意被测 Agent（单 Agent / 多 Agent 协同战队）与任意评测数据集，一键启动端到端自动化演练
            </p>
          </div>

          <button
            onClick={handleLaunchRun}
            disabled={isRunning || !selectedAgentId || !selectedDatasetId}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-mono text-xs font-bold transition-all shadow-lg ${
              isRunning
                ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                : "bg-gradient-to-r from-cyber-cyan to-cyber-azure text-obsidian-950 shadow-cyber-cyan/25 hover:scale-[1.02] active:scale-[0.98]"
            }`}
          >
            <Play className="w-4 h-4 fill-current" />
            {isRunning ? "正在并发调度评测中..." : "启动通用全链路评测 (Launch Run)"}
          </button>
        </div>

        {/* 组合选择器 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 font-mono text-xs">
          <div className="space-y-1.5 p-4 rounded-xl bg-obsidian-950/80 border border-white/5">
            <label className="text-slate-300 font-bold flex items-center gap-1.5">
              <Bot className="w-3.5 h-3.5 text-cyber-cyan" /> 1. 选择被测智能体 (Target Agent):
            </label>
            <select
              value={selectedAgentId}
              onChange={(e) => setSelectedAgentId(e.target.value)}
              className="w-full bg-black/60 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyber-cyan"
            >
              {agents.map((ag) => (
                <option key={ag.id} value={ag.id} className="bg-obsidian-900">
                  {ag.name} ({ag.agent_type === "mas_team" ? "多 Agent 战队" : ag.model_name})
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5 p-4 rounded-xl bg-obsidian-950/80 border border-white/5">
            <label className="text-slate-300 font-bold flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-emerald-pulse" /> 2. 选择通用评测集 (Benchmark Dataset):
            </label>
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="w-full bg-black/60 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-pulse"
            >
              {datasets.map((ds) => (
                <option key={ds.id} value={ds.id} className="bg-obsidian-900">
                  {ds.name} ({ds.domain} · {ds.case_count || 0} 个用例)
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 当前运行结果卡片 */}
        {currentRunResult && currentRunResult.summary && (
          <div className="p-4 rounded-xl bg-emerald-pulse/10 border border-emerald-pulse/30 flex items-center justify-between text-xs font-mono text-emerald-pulse">
            <div>
              <span className="font-bold block text-sm">🎉 评测任务执行完毕！</span>
              <span>
                通过率: {(currentRunResult.summary.score * 100).toFixed(0)}% (
                {currentRunResult.summary.passed_cases}/{currentRunResult.summary.total_cases}) · 耗时:{" "}
                {currentRunResult.summary.latency_ms}ms
              </span>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-pulse/20 font-bold">
              ID: {currentRunResult.summary.run_id}
            </span>
          </div>
        )}
      </div>

      {/* 下方：评测历史运行记录大表 */}
      <div className="glass-panel rounded-2xl border border-white/10 overflow-hidden shadow-2xl space-y-2">
        <div className="p-4 border-b border-white/10 flex items-center justify-between font-mono">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-cyber-azure" />
            <h3 className="text-xs font-bold text-slate-100 uppercase">评测运行历史记录 (Eval Runs History)</h3>
          </div>
          <span className="text-[11px] text-slate-400">已沉淀 {runs.length} 次测试记录</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-white/10 bg-obsidian-950/80 font-mono text-slate-400 text-[11px] uppercase">
                <th className="py-3 px-4 w-28">状态</th>
                <th className="py-3 px-4 w-44">Run ID</th>
                <th className="py-3 px-4">被测 Agent</th>
                <th className="py-3 px-4">评测集</th>
                <th className="py-3 px-4 text-right">得分</th>
                <th className="py-3 px-4 text-right">耗时</th>
                <th className="py-3 px-4 text-right">执行时间</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono text-xs">
              {runs.map((r) => {
                const s = r.summary || {};
                const isPassed = (r.score ?? 1.0) >= 0.8;
                return (
                  <tr key={r.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-pulse font-bold bg-emerald-pulse/10 px-2 py-0.5 rounded">
                        <CheckCircle2 className="w-3 h-3" /> COMPLETED
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">{r.id}</td>
                    <td className="py-3 px-4 font-sans font-bold text-slate-200">{s.agent_name || r.agent_id}</td>
                    <td className="py-3 px-4 font-sans text-slate-300">{s.dataset_name || r.dataset_id}</td>
                    <td className="py-3 px-4 text-right font-bold text-emerald-pulse">
                      {((r.score ?? 1.0) * 100).toFixed(0)}%
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400">{r.latency_ms?.toFixed(0) || 120}ms</td>
                    <td className="py-3 px-4 text-right text-slate-500 text-[11px]">
                      {new Date(r.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
