"use client";

import React, { useState } from "react";
import { Play, Sparkles, Github, Terminal, CheckCircle2, RefreshCw } from "lucide-react";

interface HeaderProps {
  onRunEval: () => void;
  isRunning: boolean;
}

export function Header({ onRunEval, isRunning }: HeaderProps) {
  return (
    <header className="w-full glass-panel border-b border-white/10 sticky top-0 z-50 px-6 py-3.5 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* 左侧 Logo 与版本 */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyber-cyan to-indigo-600 flex items-center justify-center text-obsidian-950 font-black shadow-lg shadow-cyber-cyan/20">
            <Sparkles className="w-5 h-5 text-obsidian-950" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-extrabold tracking-tight text-white font-mono">
                AgentTestHub
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyber-cyan/10 text-cyber-cyan border border-cyber-cyan/30">
                v2.1 Frontier
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-sans">
              多智能体考官动态博弈 · 美团二元陪审团 · 阿里 7-Hop 评测平台
            </p>
          </div>
        </div>

        {/* 中间：基准场景选择与后端连接状态 */}
        <div className="hidden md:flex items-center gap-3 bg-obsidian-950/70 px-3 py-1.5 rounded-xl border border-white/5">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
            <Terminal className="w-3.5 h-3.5 text-cyber-azure" />
            <span>套件: 电商破损退款端到端沙盒基准</span>
          </div>
          <span className="h-3 w-px bg-white/10" />
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-emerald-pulse">
            <span className="w-2 h-2 rounded-full bg-emerald-pulse animate-ping" />
            <span>FastAPI: 8000 在线</span>
          </div>
        </div>

        {/* 右侧：操作按钮与 GitHub 外链 */}
        <div className="flex items-center gap-3">
          <button
            onClick={onRunEval}
            disabled={isRunning}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              isRunning
                ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                : "bg-gradient-to-r from-cyber-cyan to-cyber-azure text-obsidian-950 hover:shadow-lg hover:shadow-cyber-cyan/25 hover:scale-[1.02] active:scale-[0.98]"
            }`}
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                正在实时博弈评测...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                启动全链路动态评测
              </>
            )}
          </button>

          <a
            href="https://github.com/gxx111/AgentTestHub"
            target="_blank"
            rel="noreferrer"
            className="w-9 h-9 rounded-xl glass-card flex items-center justify-center text-slate-300 hover:text-white hover:border-white/20 transition-colors"
          >
            <Github className="w-4 h-4" />
          </a>
        </div>
      </div>
    </header>
  );
}
