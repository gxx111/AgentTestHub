"use client";

import React, { useState } from "react";
import {
  Play,
  RotateCw,
  CheckCircle2,
  XCircle,
  Clock,
  Eye,
  ShieldAlert,
  Zap,
  Filter,
  Layers,
  Sparkles,
} from "lucide-react";
import { TestCaseResultData } from "../trace/TraceInspectorDrawer";

export interface BenchmarkCaseInfo {
  id: string;
  title: string;
  category: string;
  description: string;
  prompt: string;
  rubrics_count: number;
  expected_world_states?: any[];
}

interface TestMatrixTableProps {
  benchmarkId: string;
  suiteName: string;
  testCases: BenchmarkCaseInfo[];
  caseResults: Record<string, TestCaseResultData>;
  isRunningAll: boolean;
  runningCaseId: string | null;
  onRunAll: () => void;
  onRunSingle: (caseId: string) => void;
  onInspectTrace: (caseData: TestCaseResultData) => void;
}

export function TestMatrixTable({
  benchmarkId,
  suiteName,
  testCases,
  caseResults,
  isRunningAll,
  runningCaseId,
  onRunAll,
  onRunSingle,
  onInspectTrace,
}: TestMatrixTableProps) {
  const [filterCategory, setFilterCategory] = useState<string>("all");

  const filteredCases = testCases.filter((c) => {
    if (filterCategory === "all") return true;
    return c.category === filterCategory;
  });

  const categories = Array.from(new Set(testCases.map((c) => c.category)));

  // 统计已通过数
  const totalCount = testCases.length;
  const executedCount = Object.keys(caseResults).length;
  const passedCount = Object.values(caseResults).filter((r) => r.result.is_passed).length;
  const passRate = executedCount > 0 ? (passedCount / executedCount) * 100 : 100;

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case "happy_path":
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-pulse/15 text-emerald-pulse border border-emerald-pulse/30">标准流</span>;
      case "security_redline":
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-crimson-hazard/15 text-crimson-hazard border border-crimson-hazard/30">红队攻击</span>;
      case "sop_compliance":
      case "ant_sop_governance":
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyber-cyan/15 text-cyber-cyan border border-cyber-cyan/30">SOP 合规</span>;
      default:
        return <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-flame/15 text-amber-flame border border-amber-flame/30">边界测试</span>;
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* 顶部控制栏与统计大盘 (Promptfoo 样式) */}
      <div className="glass-panel rounded-2xl p-5 border border-white/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/10 text-cyber-cyan border border-cyber-cyan/30 uppercase">
              {benchmarkId}
            </span>
            <h2 className="text-sm font-bold text-slate-100 font-mono tracking-tight">{suiteName}</h2>
          </div>
          <p className="text-xs text-slate-400 font-sans">
            共计包含 {totalCount} 个真实业务与对抗测试用例，支持单用例调试或全量矩阵并发压测
          </p>
        </div>

        {/* 统计指标与一键批量跑 */}
        <div className="flex items-center gap-4 w-full md:w-auto justify-between md:justify-end">
          <div className="flex items-center gap-3 font-mono text-xs bg-obsidian-950/80 px-3.5 py-2 rounded-xl border border-white/5">
            <div>
              <span className="text-slate-400 block text-[10px]">测试通过率</span>
              <span className={`font-bold ${passRate === 100 ? "text-emerald-pulse" : "text-amber-flame"}`}>
                {passRate.toFixed(0)}% ({passedCount}/{executedCount || totalCount})
              </span>
            </div>
            <span className="h-4 w-px bg-white/10" />
            <div>
              <span className="text-slate-400 block text-[10px]">用例规模</span>
              <span className="font-bold text-slate-200">{totalCount} 个 Cases</span>
            </div>
          </div>

          <button
            onClick={onRunAll}
            disabled={isRunningAll}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all shadow-lg ${
              isRunningAll
                ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                : "bg-gradient-to-r from-cyber-cyan to-cyber-azure text-obsidian-950 shadow-cyber-cyan/20 hover:scale-[1.02] active:scale-[0.98]"
            }`}
          >
            <RotateCw className={`w-3.5 h-3.5 ${isRunningAll ? "animate-spin" : ""}`} />
            {isRunningAll ? "正在并发测试中..." : "批量运行全量用例 (Run All)"}
          </button>
        </div>
      </div>

      {/* 类别过滤器 */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-mono">
        <span className="text-slate-500 flex items-center gap-1 pl-1">
          <Filter className="w-3 h-3" /> 过滤:
        </span>
        <button
          onClick={() => setFilterCategory("all")}
          className={`px-3 py-1 rounded-lg border transition-all ${
            filterCategory === "all"
              ? "bg-white/10 text-white border-white/30"
              : "text-slate-400 hover:text-slate-200 border-transparent"
          }`}
        >
          全部用例 ({totalCount})
        </button>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setFilterCategory(cat)}
            className={`px-3 py-1 rounded-lg border transition-all ${
              filterCategory === cat
                ? "bg-cyber-cyan/15 text-cyber-cyan border-cyber-cyan/40"
                : "text-slate-400 hover:text-slate-200 border-transparent"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* 核心用例矩阵表格 */}
      <div className="glass-panel rounded-2xl border border-white/10 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-white/10 bg-obsidian-950/80 font-mono text-slate-400 text-[11px] uppercase tracking-wider">
                <th className="py-3 px-4 w-12 text-center">状态</th>
                <th className="py-3 px-4 w-56">用例名称 / ID</th>
                <th className="py-3 px-4 w-28">分类</th>
                <th className="py-3 px-4">测试 Prompt 输入</th>
                <th className="py-3 px-4 w-24 text-right">得分</th>
                <th className="py-3 px-4 w-36 text-center">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredCases.map((c) => {
                const res = caseResults[c.id];
                const isRunningThis = runningCaseId === c.id;
                const isPassed = res?.result?.is_passed;

                return (
                  <tr
                    key={c.id}
                    className="hover:bg-white/[0.03] transition-colors group cursor-pointer"
                    onClick={() => res && onInspectTrace(res)}
                  >
                    {/* 状态图标 */}
                    <td className="py-3 px-4 text-center">
                      {isRunningThis ? (
                        <RotateCw className="w-4 h-4 text-cyber-cyan animate-spin mx-auto" />
                      ) : res ? (
                        isPassed ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-pulse mx-auto" />
                        ) : (
                          <XCircle className="w-4 h-4 text-crimson-hazard mx-auto" />
                        )
                      ) : (
                        <Clock className="w-4 h-4 text-slate-500 mx-auto" />
                      )}
                    </td>

                    {/* 用例标题 */}
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-200 group-hover:text-cyber-cyan transition-colors line-clamp-1">
                        {c.title}
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">{c.id}</span>
                    </td>

                    {/* 分类标签 */}
                    <td className="py-3 px-4 whitespace-nowrap">{getCategoryBadge(c.category)}</td>

                    {/* Prompt 预览 */}
                    <td className="py-3 px-4">
                      <p className="text-slate-300 font-sans line-clamp-1 text-[11px]">
                        "{c.prompt}"
                      </p>
                      <span className="text-[10px] text-slate-500 font-sans line-clamp-1">
                        预期: {c.description}
                      </span>
                    </td>

                    {/* 得分 */}
                    <td className="py-3 px-4 text-right font-mono font-bold">
                      {res ? (
                        <span className={isPassed ? "text-emerald-pulse" : "text-crimson-hazard"}>
                          {(res.result.total_score * 100).toFixed(0)}%
                        </span>
                      ) : (
                        <span className="text-slate-500">--</span>
                      )}
                    </td>

                    {/* 操作按钮 */}
                    <td
                      className="py-3 px-4 text-center space-x-1.5 whitespace-nowrap"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        onClick={() => onRunSingle(c.id)}
                        disabled={isRunningThis || isRunningAll}
                        className="px-2.5 py-1 rounded-lg glass-card hover:border-cyber-cyan text-slate-300 hover:text-cyber-cyan font-mono text-[11px] transition-all inline-flex items-center gap-1"
                      >
                        <Play className="w-3 h-3" /> 调试
                      </button>

                      {res && (
                        <button
                          onClick={() => onInspectTrace(res)}
                          className="px-2.5 py-1 rounded-lg bg-cyber-azure/10 hover:bg-cyber-azure/20 text-cyber-azure border border-cyber-azure/30 font-mono text-[11px] transition-all inline-flex items-center gap-1"
                        >
                          <Eye className="w-3 h-3" /> Trace
                        </button>
                      )}
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
