"use client";

import React, { useState, useEffect } from "react";
import {
  Bot,
  Plus,
  Trash2,
  Users,
  Globe,
  Cpu,
  Wrench,
  Check,
  X,
  Sparkles,
  GitFork,
  ArrowRight,
} from "lucide-react";

export interface AgentItem {
  id: string;
  name: string;
  agent_type: "single" | "mas_team" | "webhook" | "mock";
  model_name: string;
  description: string;
  system_prompt: string;
  tools: Array<{ name: string; description: string }>;
  mas_team: Array<{ role: string; name: string; duty: string }>;
  config: Record<string, any>;
  created_at: string;
}

export function AgentRegistryView() {
  const [agents, setAgents] = useState<AgentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // 新增表单状态
  const [name, setName] = useState("");
  const [agentType, setAgentType] = useState<"single" | "mas_team" | "webhook">("single");
  const [modelName, setModelName] = useState("gpt-4o");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [apiBase, setApiBase] = useState("");
  
  // 多 Agent 团队成员
  const [teamMembers, setTeamMembers] = useState<Array<{ role: string; name: string; duty: string }>>([
    { role: "PM_Agent", name: "业务需求分析师", duty: "负责业务需求拆解与定义" },
    { role: "Architect_Agent", name: "系统架构师", duty: "负责拓扑设计与死锁规避" },
    { role: "Coder_Agent", name: "研发执行工程师", duty: "负责调用工具并交付结果" },
  ]);

  const fetchAgents = async () => {
    try {
      const res = await fetch("http://localhost:8005/api/v1/agents");
      if (res.ok) {
        const data = await res.json();
        setAgents(data);
      }
    } catch (_) {}
    setLoading(false);
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const handleCreateAgent = async () => {
    if (!name.trim()) return;

    const payload = {
      workspace_id: "ws_primary",
      name,
      agent_type: agentType,
      model_name: modelName,
      description,
      system_prompt: systemPrompt,
      tools: [{ name: "db_execute", description: "数据库物理操作执行工具" }],
      mas_team: agentType === "mas_team" ? teamMembers : [],
      config: {
        api_key: apiKey || null,
        api_base: apiBase || null,
        webhook_url: webhookUrl || null,
      },
    };

    try {
      const res = await fetch("http://localhost:8005/api/v1/agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        setIsModalOpen(false);
        setName("");
        setDescription("");
        fetchAgents();
      }
    } catch (_) {}
  };

  const handleDeleteAgent = async (id: string) => {
    if (!confirm("确认注销并删除该智能体资产？")) return;
    try {
      await fetch(`http://localhost:8005/api/v1/agents/${id}`, { method: "DELETE" });
      fetchAgents();
    } catch (_) {}
  };

  const addTeamMember = () => {
    setTeamMembers((prev) => [
      ...prev,
      { role: `Agent_${prev.length + 1}`, name: "协同成员", duty: "通用业务协同支持" },
    ]);
  };

  return (
    <div className="w-full space-y-5 font-sans">
      {/* 顶部标题栏与新建按钮 */}
      <div className="glass-panel rounded-2xl p-5 border border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyber-cyan/15 text-cyber-cyan border border-cyber-cyan/30 uppercase font-bold">
              资产库 · CRUD
            </span>
            <h2 className="text-sm font-bold text-slate-100 font-mono tracking-tight">
              被测智能体注册表 (Agent Registry)
            </h2>
          </div>
          <p className="text-xs text-slate-400 font-sans">
            支持注册单 Agent、多智能体协同战队 (MAS Squad) 或企业私有 Webhook，支持任意业务场景 95%+ 泛化评测
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyber-cyan to-cyber-azure text-obsidian-950 font-mono text-xs font-bold shadow-lg shadow-cyber-cyan/20 hover:scale-[1.02] active:scale-[0.98] transition-all shrink-0"
        >
          <Plus className="w-4 h-4" /> 注册新智能体 (New Agent)
        </button>
      </div>

      {/* 智能体卡片网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((ag) => (
          <div
            key={ag.id}
            className="glass-panel rounded-2xl p-5 border border-white/10 space-y-3.5 hover:border-cyber-cyan/40 transition-all flex flex-col justify-between"
          >
            <div className="space-y-2">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      ag.agent_type === "mas_team"
                        ? "bg-amber-flame/15 text-amber-flame border border-amber-flame/30"
                        : ag.agent_type === "webhook"
                        ? "bg-fuchsia-500/15 text-fuchsia-400 border border-fuchsia-500/30"
                        : "bg-cyber-cyan/15 text-cyber-cyan border border-cyber-cyan/30"
                    }`}
                  >
                    {ag.agent_type === "mas_team" ? (
                      <Users className="w-4 h-4" />
                    ) : ag.agent_type === "webhook" ? (
                      <Globe className="w-4 h-4" />
                    ) : (
                      <Bot className="w-4 h-4" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-100 line-clamp-1">{ag.name}</h3>
                    <span className="text-[10px] text-slate-400 font-mono">{ag.id}</span>
                  </div>
                </div>

                <button
                  onClick={() => handleDeleteAgent(ag.id)}
                  className="text-slate-500 hover:text-red-400 p-1 rounded"
                  title="注销智能体"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              <p className="text-xs text-slate-300 font-sans line-clamp-2 leading-relaxed">
                {ag.description || "未填写描述说明"}
              </p>

              {/* 多 Agent 团队成员标签 */}
              {ag.agent_type === "mas_team" && ag.mas_team && ag.mas_team.length > 0 && (
                <div className="p-2.5 rounded-xl bg-obsidian-950/80 border border-white/5 space-y-1 font-mono text-[11px]">
                  <span className="text-[10px] text-amber-flame font-bold flex items-center gap-1">
                    <Users className="w-3 h-3" /> 团队成员架构 ({ag.mas_team.length} Agents):
                  </span>
                  <div className="space-y-0.5 text-slate-300 text-[10px]">
                    {ag.mas_team.map((m, i) => (
                      <div key={i} className="flex justify-between">
                        <span>{m.name}</span>
                        <span className="text-slate-500">{m.role}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-slate-400">
              <span className="flex items-center gap-1">
                <Cpu className="w-3 h-3 text-cyber-azure" /> {ag.model_name}
              </span>
              <span
                className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                  ag.agent_type === "mas_team"
                    ? "bg-amber-flame/15 text-amber-flame"
                    : "bg-cyber-cyan/15 text-cyber-cyan"
                }`}
              >
                {ag.agent_type === "mas_team" ? "多 Agent 战队" : ag.agent_type}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* 新建 Agent 模态框 */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="w-full max-w-2xl rounded-2xl glass-panel border border-white/15 p-6 shadow-2xl relative overflow-hidden space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-cyber-cyan" />
                <h3 className="text-sm font-bold text-white font-mono uppercase">
                  注册新被测智能体 (Register New Agent)
                </h3>
              </div>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* 架构类型单选 */}
            <div className="grid grid-cols-3 gap-2 font-mono text-xs">
              {[
                { id: "single", label: "单智能体 (Single)", icon: Bot, desc: "标准商业/自建模型 Agent" },
                { id: "mas_team", label: "多智能体战队 (MAS Team)", icon: Users, desc: "多角色协同流水线/工作流" },
                { id: "webhook", label: "私有 Webhook", icon: Globe, desc: "企业自研外部 HTTP 接口" },
              ].map((t) => {
                const isSelected = agentType === t.id;
                const Icon = t.icon;
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setAgentType(t.id as any)}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      isSelected
                        ? "bg-cyber-cyan/10 border-cyber-cyan text-cyber-cyan"
                        : "glass-card hover:border-white/20 text-slate-300"
                    }`}
                  >
                    <div className="flex items-center gap-1.5 font-bold mb-1">
                      <Icon className="w-3.5 h-3.5" /> {t.label}
                    </div>
                    <span className="text-[10px] text-slate-400 block">{t.desc}</span>
                  </button>
                );
              })}
            </div>

            {/* 表单字段 */}
            <div className="space-y-3 font-mono text-xs">
              <div>
                <label className="text-slate-300 block mb-1">智能体名称:</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="例如: 医疗问诊导医 Agent / 投资研究协同分析战队"
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white"
                />
              </div>

              <div>
                <label className="text-slate-300 block mb-1">职责描述:</label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="简述其业务定位、输入与期望输出"
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>

              {agentType === "single" && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-300 block mb-1">模型名称 (Model Identifier):</label>
                    <input
                      type="text"
                      value={modelName}
                      onChange={(e) => setModelName(e.target.value)}
                      placeholder="gpt-4o, deepseek-chat, qwen-2.5 等"
                      className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white"
                    />
                  </div>
                  <div>
                    <label className="text-slate-300 block mb-1">自定义 API Base URL (可选):</label>
                    <input
                      type="text"
                      value={apiBase}
                      onChange={(e) => setApiBase(e.target.value)}
                      placeholder="http://localhost:11434 或反代网关"
                      className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-slate-300"
                    />
                  </div>
                </div>
              )}

              {/* 多 Agent 战队专属配置 */}
              {agentType === "mas_team" && (
                <div className="p-3.5 rounded-xl bg-obsidian-950/80 border border-white/10 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-amber-flame font-bold flex items-center gap-1.5">
                      <Users className="w-3.5 h-3.5" /> 团队协作角色设定 ({teamMembers.length} 成员):
                    </span>
                    <button
                      type="button"
                      onClick={addTeamMember}
                      className="text-[11px] text-cyber-cyan hover:underline flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" /> 增加成员角色
                    </button>
                  </div>

                  <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                    {teamMembers.map((m, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <input
                          type="text"
                          value={m.role}
                          onChange={(e) => {
                            const next = [...teamMembers];
                            next[i].role = e.target.value;
                            setTeamMembers(next);
                          }}
                          className="w-32 bg-black/50 border border-white/10 rounded px-2 py-1 text-slate-200 text-[11px]"
                          placeholder="角色ID"
                        />
                        <input
                          type="text"
                          value={m.name}
                          onChange={(e) => {
                            const next = [...teamMembers];
                            next[i].name = e.target.value;
                            setTeamMembers(next);
                          }}
                          className="w-36 bg-black/50 border border-white/10 rounded px-2 py-1 text-slate-200 text-[11px]"
                          placeholder="显示名"
                        />
                        <input
                          type="text"
                          value={m.duty}
                          onChange={(e) => {
                            const next = [...teamMembers];
                            next[i].duty = e.target.value;
                            setTeamMembers(next);
                          }}
                          className="flex-1 bg-black/50 border border-white/10 rounded px-2 py-1 text-slate-400 text-[11px]"
                          placeholder="职责说明"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {agentType === "webhook" && (
                <div>
                  <label className="text-slate-300 block mb-1">外部 HTTP Webhook URL:</label>
                  <input
                    type="text"
                    value={webhookUrl}
                    onChange={(e) => setWebhookUrl(e.target.value)}
                    placeholder="http://192.168.1.10:8080/api/agent"
                    className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white"
                  />
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 rounded-xl glass-card text-xs text-slate-400 hover:text-white"
              >
                取消
              </button>
              <button
                type="button"
                onClick={handleCreateAgent}
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyber-cyan to-cyber-azure text-obsidian-950 font-bold text-xs"
              >
                确认创建
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
