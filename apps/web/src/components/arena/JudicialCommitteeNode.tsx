"use client";

import React from "react";
import { Handle, Position } from "@xyflow/react";
import { Scale, Check, ShieldCheck } from "lucide-react";

export function JudicialCommitteeNode({ data }: { data: any }) {
  return (
    <div className="w-88 rounded-xl glass-card border border-violet-verdict/40 p-4 shadow-2xl relative overflow-hidden">
      {/* 顶部合议紫光晕 */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-violet-verdict to-fuchsia-500" />

      <Handle
        type="target"
        position={Position.Top}
        className="!bg-violet-verdict !w-3 !h-3 !border-2 !border-obsidian-900"
      />

      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-violet-verdict/15 border border-violet-verdict/30 flex items-center justify-center text-fuchsia-400">
            <Scale className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-semibold tracking-wider text-slate-200 uppercase font-mono">
              美团二元 Rubric 陪审团
            </h4>
            <span className="text-[10px] text-fuchsia-400 font-mono">
              多角色独立盲审 + 辩论协议
            </span>
          </div>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-verdict/20 text-fuchsia-300 border border-violet-verdict/30 font-mono">
          合议终局裁决
        </span>
      </div>

      {/* 4大异构法官盲审二元表 */}
      <div className="space-y-1.5 bg-obsidian-950/90 rounded-lg p-2.5 border border-white/5 font-mono text-[11px] mb-3">
        <div className="flex justify-between items-center text-slate-300">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-cyber-cyan" /> 规则法官 (Rule)
          </span>
          <span className="text-emerald-pulse bg-emerald-pulse/10 px-1.5 py-0.2 rounded font-bold">
            YES (100%)
          </span>
        </div>
        <div className="flex justify-between items-center text-slate-300">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-crimson-hazard" /> 安全法官 (Safety)
          </span>
          <span className="text-emerald-pulse bg-emerald-pulse/10 px-1.5 py-0.2 rounded font-bold">
            YES (100%)
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] font-mono pt-1 text-slate-400">
        <span className="text-slate-300">辩论仲裁轮次: 0 轮 (全票共识)</span>
        <span className="text-emerald-pulse font-bold flex items-center gap-1">
          <Check className="w-3 h-3" /> 加权总分: 1.00
        </span>
      </div>
    </div>
  );
}
