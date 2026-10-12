"use client";

import React, { useState } from "react";
import {
  X,
  MessageSquare,
  Wrench,
  Database,
  Scale,
  GitBranch,
  Bot,
  User,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

export interface TraceEventData {
  event_id: string;
  span_id: string;
  turn_index: number;
  actor_role: string;
  actor_name: string;
  event_type: string;
  content: string;
  thought?: string | null;
  tool_observation?: {
    tool_name: string;
    arguments: Record<string, any>;
    output: any;
    is_error: boolean;
    duration_ms: number;
  } | null;
}

export interface TestCaseResultData {
  case_id: string;
  title: string;
  category: string;
  prompt: string;
  result: {
    task_id: string;
    is_passed: boolean;
    total_score: number;
    world_state_passed: boolean;
    world_state_diff: {
      modified_records?: Array<{
        table?: string;
        action?: string;
        old?: any;
        new?: any;
        record?: any;
      }>;
    };
    rubric_judgments: Array<{
      rubric_id: string;
      judge_role: string;
      verdict: "YES" | "NO" | "UNKNOWN";
      evidence_span_ids: string[];
      rationale: string;
      confidence: number;
    }>;
    attribution_tree?: Array<{
      node_id: string;
      hop_stage: string;
      failure_category: string;
      root_cause_explanation: string;
      suggested_action: string;
    }>;
    trace?: {
      task_id: string;
      trace_id: string;
      events: TraceEventData[];
      total_tokens?: number;
      total_duration_ms?: number;
    };
  };
}

interface TraceInspectorDrawerProps {
  caseData: TestCaseResultData | null;
  onClose: () => void;
}

export function TraceInspectorDrawer({ caseData, onClose }: TraceInspectorDrawerProps) {
  const [activeTab, setActiveTab] = useState<"transcript" | "sandbox" | "judges" | "diagnostics">("transcript");
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});

  if (!caseData) return null;

  const result = caseData.result;
  const events = result.trace?.events || [];
  const modifiedRecords = result.world_state_diff?.modified_records || [];
  const judgments = result.rubric_judgments || [];
  const attributions = result.attribution_tree || [];

  const toggleTool = (id: string) => {
    setExpandedTools((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-3xl glass-panel border-l border-white/15 bg-obsidian-950/95 shadow-2xl flex flex-col font-sans backdrop-blur-2xl animate-in slide-in-from-right duration-300">
      {/* 顶部标题栏 */}
      <div className="p-5 border-b border-white/10 flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <span
              className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded ${
                result.is_passed
                  ? "bg-emerald-pulse/15 text-emerald-pulse border border-emerald-pulse/30"
                  : "bg-crimson-hazard/15 text-crimson-hazard border border-crimson-hazard/30"
              }`}
            >
              {result.is_passed ? "PASSED (已通过)" : "FAILED (未达标)"}
            </span>
            <span className="text-xs text-cyber-cyan font-mono">{caseData.case_id}</span>
            <span className="text-xs text-slate-500 font-mono">|</span>
            <span className="text-xs text-slate-400 font-mono">得分: {(result.total_score * 100).toFixed(0)}%</span>
          </div>
          <h2 className="text-sm font-bold text-slate-100">{caseData.title}</h2>
        </div>

        <button
          onClick={onClose}
          className="w-8 h-8 rounded-xl glass-card flex items-center justify-center text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* 选项卡导航 */}
      <div className="px-5 pt-3 border-b border-white/10 flex items-center gap-2 bg-obsidian-900/60 font-mono text-xs">
        {[
          { id: "transcript", label: "多轮交互流 (Transcript)", icon: MessageSquare, count: events.length },
          { id: "sandbox", label: "数据库差分 (DB Diff)", icon: Database, count: modifiedRecords.length },
          { id: "judges", label: "二元法官合议 (Jury)", icon: Scale, count: judgments.length },
          { id: "diagnostics", label: "7-Hop 归因 (Diagnostics)", icon: GitBranch, count: attributions.length },
        ].map((t) => {
          const Icon = t.icon;
          const isActive = activeTab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as any)}
              className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-bold transition-all ${
                isActive
                  ? "border-cyber-cyan text-cyber-cyan bg-cyber-cyan/5"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{t.label}</span>
              {t.count !== undefined && t.count > 0 && (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-white/10 text-slate-300">
                  {t.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* 主展示内容区域 */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {/* Tab 1: 交互流气泡 */}
        {activeTab === "transcript" && (
          <div className="space-y-4 font-sans text-xs">
            {events.length === 0 ? (
              <div className="p-8 text-center text-slate-500 font-mono">
                暂无事件日志流记录，请在矩阵中点击「运行单用例」触发测试。
              </div>
            ) : (
              events.map((evt, idx) => {
                const isUser = evt.actor_role === "user_simulator";
                const isRedTeam = evt.actor_role === "red_team_attacker";
                const isAgent = evt.actor_role === "testee_agent";
                const isTool = evt.event_type === "tool_call_request";

                if (isTool && evt.tool_observation) {
                  const obs = evt.tool_observation;
                  const isExp = !!expandedTools[evt.event_id];
                  return (
                    <div
                      key={idx}
                      className="rounded-xl border border-cyber-azure/30 bg-obsidian-900/90 overflow-hidden font-mono"
                    >
                      <button
                        onClick={() => toggleTool(evt.event_id)}
                        className="w-full p-3 flex items-center justify-between text-left hover:bg-white/5 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <Wrench className="w-3.5 h-3.5 text-cyber-azure" />
                          <span className="font-bold text-cyber-azure">工具调用: {obs.tool_name}</span>
                          {obs.is_error ? (
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-crimson-hazard/20 text-crimson-hazard">
                              执行报错
                            </span>
                          ) : (
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-pulse/20 text-emerald-pulse">
                              成功
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-slate-400">
                          <span>{obs.duration_ms.toFixed(1)}ms</span>
                          {isExp ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                        </div>
                      </button>

                      {isExp && (
                        <div className="p-3 border-t border-white/5 space-y-2 bg-black/40 text-[11px]">
                          <div>
                            <span className="text-slate-400 block mb-1">输入参数 (Arguments):</span>
                            <pre className="p-2 rounded bg-obsidian-950 text-slate-200 overflow-x-auto">
                              {JSON.stringify(obs.arguments, null, 2)}
                            </pre>
                          </div>
                          <div>
                            <span className="text-slate-400 block mb-1">执行输出 (Output):</span>
                            <pre className="p-2 rounded bg-obsidian-950 text-emerald-pulse overflow-x-auto">
                              {JSON.stringify(obs.output, null, 2)}
                            </pre>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                }

                return (
                  <div
                    key={idx}
                    className={`flex gap-3 ${
                      isAgent ? "justify-end" : "justify-start"
                    }`}
                  >
                    {!isAgent && (
                      <div
                        className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                          isRedTeam
                            ? "bg-crimson-hazard/15 text-crimson-hazard border border-crimson-hazard/30"
                            : "bg-cyber-cyan/15 text-cyber-cyan border border-cyber-cyan/30"
                        }`}
                      >
                        {isRedTeam ? <ShieldAlert className="w-4 h-4" /> : <User className="w-4 h-4" />}
                      </div>
                    )}

                    <div
                      className={`max-w-[85%] rounded-2xl p-3.5 space-y-2.5 ${
                        isAgent
                          ? "bg-gradient-to-r from-blue-600/15 to-indigo-600/15 border border-indigo-500/30 text-slate-100"
                          : isRedTeam
                          ? "bg-crimson-hazard/10 border border-crimson-hazard/30 text-red-200"
                          : "bg-obsidian-900 border border-white/10 text-slate-200"
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] font-mono opacity-60 pb-1 border-b border-white/5">
                        <span className="font-bold">
                          {isAgent
                            ? "被测 Agent (Target)"
                            : isRedTeam
                            ? "考官 · 对抗攻防红队 (Red-Team)"
                            : "考官 · 状态化用户模拟官 (UserSimulator)"}
                        </span>
                        <span>轮次 {evt.turn_index}</span>
                      </div>

                      {/* 若存在 Agent 的 ReAct 思考链，清晰展示独立思考卡片 */}
                      {isAgent && evt.thought && (
                        <div className="p-2.5 rounded-xl bg-indigo-950/60 border border-indigo-500/30 text-[11px] font-mono text-indigo-200 space-y-1">
                          <div className="flex items-center gap-1.5 text-cyber-cyan font-bold text-[10px] uppercase">
                            <Sparkles className="w-3 h-3 text-cyber-cyan" />
                            <span>自主推理与反思链 (ReAct Thought)</span>
                          </div>
                          <p className="leading-relaxed opacity-90">{evt.thought}</p>
                        </div>
                      )}

                      <p className="leading-relaxed whitespace-pre-wrap">{evt.content}</p>
                    </div>

                    {isAgent && (
                      <div className="w-7 h-7 rounded-lg bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 flex items-center justify-center shrink-0">
                        <Bot className="w-4 h-4" />
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* Tab 2: 数据库差分 */}
        {activeTab === "sandbox" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between font-mono text-xs text-slate-300">
              <span className="flex items-center gap-1.5">
                <Database className="w-4 h-4 text-emerald-pulse" /> 物理沙盒数据表状态差分 (StateDelta)
              </span>
              <span className="text-emerald-pulse font-bold">
                {result.world_state_passed ? "物理终态已达成 ✅" : "未达成 ❌"}
              </span>
            </div>

            {modifiedRecords.length === 0 ? (
              <div className="p-6 rounded-xl bg-obsidian-900 border border-white/5 text-center text-xs text-slate-400 font-mono">
                本用例执行前后未发生数据库记录变更 (符合预期或无写操作)。
              </div>
            ) : (
              modifiedRecords.map((m, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-obsidian-900 border border-white/10 font-mono text-xs space-y-2">
                  <div className="flex items-center justify-between text-slate-300">
                    <span>目标表: <strong className="text-cyber-cyan">{m.table || "orders"}</strong></span>
                    <span className="text-emerald-pulse bg-emerald-pulse/10 px-2 py-0.5 rounded text-[10px]">
                      {m.action || "UPDATE"}
                    </span>
                  </div>
                  {m.old && (
                    <div className="p-2.5 rounded bg-black/40 border border-red-500/20 text-red-300 line-through text-[11px]">
                      变更前: {JSON.stringify(m.old)}
                    </div>
                  )}
                  {m.new && (
                    <div className="p-2.5 rounded bg-black/40 border border-emerald-500/20 text-emerald-pulse font-bold text-[11px]">
                      变更后: {JSON.stringify(m.new)}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* Tab 3: 法官盲审与合议明细 */}
        {activeTab === "judges" && (
          <div className="space-y-3">
            {judgments.length === 0 ? (
              <div className="p-6 text-center text-slate-500 font-mono text-xs">
                暂无法官合议记录。
              </div>
            ) : (
              judgments.map((j, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-obsidian-900 border border-white/10 space-y-2">
                  <div className="flex items-center justify-between font-mono text-xs">
                    <span className="text-slate-200 font-bold">{j.rubric_id}</span>
                    <span
                      className={`px-2 py-0.5 rounded font-bold ${
                        j.verdict === "YES"
                          ? "bg-emerald-pulse/15 text-emerald-pulse border border-emerald-pulse/30"
                          : "bg-crimson-hazard/15 text-crimson-hazard border border-crimson-hazard/30"
                      }`}
                    >
                      {j.judge_role}: {j.verdict}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 font-sans leading-relaxed">{j.rationale}</p>
                  {j.evidence_span_ids && j.evidence_span_ids.length > 0 && (
                    <div className="pt-2 border-t border-white/5 flex items-center gap-1.5 text-[10px] font-mono text-cyber-azure">
                      <span>证据锚点:</span>
                      {j.evidence_span_ids.map((sid, i) => (
                        <span key={i} className="bg-white/5 px-1.5 py-0.5 rounded">
                          {sid}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* Tab 4: 因果归因 */}
        {activeTab === "diagnostics" && (
          <div className="space-y-3 font-mono text-xs">
            {attributions.length === 0 ? (
              <div className="p-6 rounded-xl bg-emerald-pulse/5 border border-emerald-pulse/20 text-emerald-pulse text-center space-y-1">
                <CheckCircle2 className="w-5 h-5 mx-auto" />
                <p>全链路指标合规达标，未触发任何故障因果节点。</p>
              </div>
            ) : (
              attributions.map((a, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-crimson-hazard/10 border border-crimson-hazard/30 space-y-2">
                  <div className="flex items-center justify-between text-crimson-hazard font-bold">
                    <span>{a.hop_stage}</span>
                    <span>{a.failure_category}</span>
                  </div>
                  <p className="text-slate-300 font-sans">{a.root_cause_explanation}</p>
                  <div className="p-2.5 rounded bg-black/40 border border-white/10 text-emerald-pulse">
                    <strong>建议修复操作:</strong> {a.suggested_action}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
