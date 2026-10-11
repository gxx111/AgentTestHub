"use client";

import React from "react";
import { Handle, Position } from "@xyflow/react";
import { Bot, Cpu, Wrench } from "lucide-react";

export function TesteeAgentNode({ data }: { data: any }) {
  return (
    <div className="w-84 rounded-xl glass-card border border-white/15 p-4 shadow-2xl relative overflow-hidden">
      {/* 顶部高亮边 */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-indigo-500" />

      <Handle
        type="target"
        position={Position.Left}
        className="!bg-cyber-azure !w-3 !h-3 !border-2 !border-obsidian-900"
      />

      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-semibold tracking-wider text-slate-200 uppercase font-mono">
              被测智能体 (Target)
            </h4>
            <span className="text-[10px] text-indigo-400 font-mono flex items-center gap-1">
              <Cpu className="w-2.5 h-2.5" /> {data.model || "gpt-4o / 企业客服 Agent"}
            </span>
          </div>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-pulse/15 text-emerald-pulse border border-emerald-pulse/30 font-mono">
          在线响应中
        </span>
      </div>

      {/* 实时思考链与回复 */}
      <div className="bg-obsidian-950/80 rounded-lg p-3 border border-white/5 mb-3 text-xs text-slate-300 leading-relaxed font-sans">
        <p className="line-clamp-3">
          "{data.response || "已收到您的开箱凭证并核验通过，正在为您办理订单 ORD_1001 的退款取消..."}"
        </p>
      </div>

      {/* 工具调用活跃标签 */}
      <div className="flex items-center justify-between text-[11px] font-mono pt-2 border-t border-white/5 text-slate-400">
        <span className="flex items-center gap-1.5 text-cyber-azure">
          <Wrench className="w-3 h-3 text-cyber-azure" />
          调用: <span className="text-slate-200 font-bold bg-white/5 px-1.5 py-0.5 rounded">db_execute</span>
        </span>
        <span className="text-emerald-pulse font-semibold">AST 校验通过 ✅</span>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-indigo-400 !w-3 !h-3 !border-2 !border-obsidian-900"
      />
    </div>
  );
}
