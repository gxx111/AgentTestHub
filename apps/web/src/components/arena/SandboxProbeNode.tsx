"use client";

import React from "react";
import { Handle, Position } from "@xyflow/react";
import { Database, CheckCircle2 } from "lucide-react";

export function SandboxProbeNode({ data }: { data: any }) {
  return (
    <div className="w-88 rounded-xl glass-card border border-emerald-pulse/40 p-4 shadow-2xl relative overflow-hidden">
      {/* 顶部翠绿光晕 */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-pulse to-teal-400" />

      <Handle
        type="target"
        position={Position.Top}
        className="!bg-emerald-pulse !w-3 !h-3 !border-2 !border-obsidian-900"
      />

      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-pulse/10 border border-emerald-pulse/30 flex items-center justify-center text-emerald-pulse">
            <Database className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-semibold tracking-wider text-slate-200 uppercase font-mono">
              数字孪生沙盒探针
            </h4>
            <span className="text-[10px] text-emerald-pulse font-mono">
              SQLite 内存快照隔离
            </span>
          </div>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-pulse/15 text-emerald-pulse border border-emerald-pulse/30 font-mono flex items-center gap-1">
          <CheckCircle2 className="w-2.5 h-2.5" /> 物理差分达成
        </span>
      </div>

      {/* 真实数据库表变更对比 (State Delta Diff) */}
      <div className="bg-obsidian-950/90 rounded-lg p-3 border border-white/5 mb-3 font-mono text-[11px]">
        <div className="text-slate-400 mb-1 flex justify-between">
          <span>表: orders</span>
          <span className="text-cyber-azure">主键: ORD_1001</span>
        </div>
        <div className="space-y-1 bg-black/40 p-2 rounded border border-white/5">
          <div className="flex justify-between text-red-400/80 line-through">
            <span>status</span>
            <span>'PAID'</span>
          </div>
          <div className="flex justify-between text-emerald-pulse font-bold">
            <span>status</span>
            <span>'CANCELLED' (已更新)</span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1">
        <span>影响行数: 1 行</span>
        <span className="text-emerald-pulse">预期物理终态: 100% 吻合</span>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-emerald-pulse !w-3 !h-3 !border-2 !border-obsidian-900"
      />
    </div>
  );
}
