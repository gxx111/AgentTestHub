"use client";

import React, { useState, useEffect } from "react";
import { Settings, X, Bot, Key, Globe, Check, Cpu } from "lucide-react";

export interface TargetAgentConfigState {
  agent_type: "mock" | "litellm" | "webhook";
  model_name: string;
  api_key: string;
  api_base: string;
  webhook_url: string;
}

const DEFAULT_CONFIG: TargetAgentConfigState = {
  agent_type: "mock",
  model_name: "gpt-4o",
  api_key: "",
  api_base: "",
  webhook_url: "http://localhost:8080/api/chat",
};

interface AgentSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: TargetAgentConfigState;
  onSave: (config: TargetAgentConfigState) => void;
}

export function AgentSettingsModal({
  isOpen,
  onClose,
  config,
  onSave,
}: AgentSettingsModalProps) {
  const [form, setForm] = useState<TargetAgentConfigState>(config);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    setForm(config);
  }, [config]);

  if (!isOpen) return null;

  const handleSave = () => {
    onSave(form);
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 600);
  };

  const setPreset = (model: string, base: string = "") => {
    setForm((prev) => ({
      ...prev,
      agent_type: "litellm",
      model_name: model,
      api_base: base,
    }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-200">
      <div className="w-full max-w-xl rounded-2xl glass-panel border border-white/15 p-6 shadow-2xl relative overflow-hidden space-y-6">
        {/* 顶部青色流光条 */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyber-cyan via-cyber-azure to-indigo-500" />

        {/* 标题栏 */}
        <div className="flex items-center justify-between pb-3 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyber-cyan/10 border border-cyber-cyan/30 flex items-center justify-center text-cyber-cyan">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
                被测智能体来源配置 (Target Agent Config)
              </h3>
              <p className="text-[11px] text-slate-400">
                支持直连商用大模型 (LiteLLM) 或接入企业私有 Webhook 接口
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg glass-card flex items-center justify-center text-slate-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 来源类型单选 */}
        <div className="grid grid-cols-3 gap-2">
          {[
            { id: "mock", label: "内建自适应模拟", icon: Bot, desc: "开箱即用快速验证" },
            { id: "litellm", label: "商用/开源大模型", icon: Cpu, desc: "LiteLLM 统一网关" },
            { id: "webhook", label: "自定义 Webhook", icon: Globe, desc: "私有 Agent HTTP 接口" },
          ].map((t) => {
            const isSelected = form.agent_type === t.id;
            const Icon = t.icon;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setForm((prev) => ({ ...prev, agent_type: t.id as any }))}
                className={`p-3 rounded-xl border text-left transition-all ${
                  isSelected
                    ? "bg-cyber-cyan/10 border-cyber-cyan text-cyber-cyan shadow-lg shadow-cyber-cyan/10"
                    : "glass-card hover:border-white/20 text-slate-300"
                }`}
              >
                <div className="flex items-center gap-1.5 font-mono text-xs font-bold mb-1">
                  <Icon className="w-3.5 h-3.5" /> {t.label}
                </div>
                <span className="text-[10px] text-slate-400 block">{t.desc}</span>
              </button>
            );
          })}
        </div>

        {/* 选项表单 */}
        {form.agent_type === "litellm" && (
          <div className="space-y-4 p-4 rounded-xl bg-obsidian-950/80 border border-white/5 font-mono text-xs">
            <div>
              <label className="text-slate-300 block mb-2 font-bold">主流模型一键预设:</label>
              <div className="flex flex-wrap gap-2">
                {[
                  { name: "GPT-4o", model: "gpt-4o" },
                  { name: "Claude 3.5 Sonnet", model: "claude-3-5-sonnet-20241022" },
                  { name: "DeepSeek-V3", model: "deepseek/deepseek-chat" },
                  { name: "通义千问 (Qwen)", model: "qwen/qwen-2.5-72b-instruct" },
                  { name: "本地 Ollama", model: "ollama/llama3", base: "http://localhost:11434" },
                ].map((p, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setPreset(p.model, p.base || "")}
                    className="px-2.5 py-1 rounded bg-white/5 hover:bg-white/10 border border-white/10 text-[11px] text-slate-300 transition-colors"
                  >
                    {p.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-slate-300 block">模型名称 (Model Identifier):</label>
              <input
                type="text"
                value={form.model_name}
                onChange={(e) => setForm((prev) => ({ ...prev, model_name: e.target.value }))}
                placeholder="例如: gpt-4o 或 deepseek/deepseek-chat"
                className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyber-cyan"
              />
            </div>

            <div className="space-y-1">
              <label className="text-slate-300 flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-amber-flame" /> API Key:
              </label>
              <input
                type="password"
                value={form.api_key}
                onChange={(e) => setForm((prev) => ({ ...prev, api_key: e.target.value }))}
                placeholder="sk-..."
                className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyber-cyan font-mono"
              />
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 block">自定义 API Base URL (可选，Ollama/转发服务必填):</label>
              <input
                type="text"
                value={form.api_base}
                onChange={(e) => setForm((prev) => ({ ...prev, api_base: e.target.value }))}
                placeholder="例如: https://api.deepseek.com 或 http://localhost:11434"
                className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-slate-300 focus:outline-none focus:border-cyber-cyan"
              />
            </div>
          </div>
        )}

        {form.agent_type === "webhook" && (
          <div className="space-y-3 p-4 rounded-xl bg-obsidian-950/80 border border-white/5 font-mono text-xs">
            <label className="text-slate-300 block font-bold">外部 HTTP Agent Webhook URL:</label>
            <input
              type="text"
              value={form.webhook_url}
              onChange={(e) => setForm((prev) => ({ ...prev, webhook_url: e.target.value }))}
              placeholder="http://localhost:8080/api/chat"
              className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyber-cyan font-mono"
            />
            <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
              平台将在每轮向该 Webhook POST 发送 JSON 载荷 <code>&#123; prompt, task_id, tools &#125;</code>，
              期望返回 <code>&#123; response, tool_calls &#125;</code>。
            </p>
          </div>
        )}

        {form.agent_type === "mock" && (
          <div className="p-4 rounded-xl bg-obsidian-950/80 border border-emerald-pulse/30 text-emerald-pulse font-mono text-xs flex items-center gap-2">
            <Check className="w-4 h-4" /> 当前使用系统内建的高保真自适应 Agent，具备根据业务场景完成状态更新的完整闭环能力。
          </div>
        )}

        {/* 底部保存与取消 */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl glass-card text-xs text-slate-300 hover:text-white font-mono"
          >
            取消
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyber-cyan to-cyber-azure text-obsidian-950 text-xs font-bold font-mono shadow-lg shadow-cyber-cyan/20 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center gap-1.5"
          >
            {savedSuccess ? (
              <>
                <Check className="w-4 h-4" /> 配置已保存
              </>
            ) : (
              "保存并生效"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
