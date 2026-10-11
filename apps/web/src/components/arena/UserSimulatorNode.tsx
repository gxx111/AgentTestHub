"use client";

import React from "react";
import { Handle, Position } from "@xyflow/react";
import { User, Sparkles } from "lucide-react";

export function UserSimulatorNode({ data }: { data: any }) {
  return (
    <div className="w-80 rounded-xl glass-card border border-cyber-cyan/40 p-4 shadow-2xl relative overflow-hidden group">
      {/* 顶部青色光晕指示条 */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyber-cyan to-cyber-azure animate-pulse-slow" />
      
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-cyber-cyan/10 border border-cyber-cyan/30 flex items-center justify-center text-cyber-cyan">
            <User className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-semibold tracking-wider text-slate-200 uppercase font-mono">
              考官 · 用户模拟官
            </h4>
            <span className="text-[10px] text-cyber-cyan font-mono">
              {data.persona || "焦急买家"}
            </span>
          </div>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyber-cyan/15 text-cyber-cyan border border-cyber-cyan/30 font-mono">
          FSM 活跃
        </span>
      </div>

      {/* 动态对话气泡 */}
      <div className="bg-obsidian-950/80 rounded-lg p-3 border border-white/5 mb-3 text-xs text-slate-300 leading-relaxed font-sans">
        <p className="line-clamp-3">"{data.message || "包裹破损了，请马上处理退款！"}"</p>
      </div>

      {/* 状态机指标 */}
      <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono pt-2 border-t border-white/5">
        <span className="flex items-center gap-1 text-slate-300">
          <Sparkles className="w-3 h-3 text-cyber-cyan" />
          隐藏意图: <span className="text-cyber-cyan font-bold">{data.revealedGoal || "开箱凭证 (已释放)"}</span>
        </span>
        <span className="text-slate-400">轮次 {data.turn || 2}/6</span>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="!bg-cyber-cyan !w-3 !h-3 !border-2 !border-obsidian-900"
      />
    </div>
  );
}
