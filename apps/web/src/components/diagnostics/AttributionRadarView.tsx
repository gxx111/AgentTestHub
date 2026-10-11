"use client";

import React from "react";
import { GitBranch, ShieldCheck, Zap, Activity, AlertTriangle, ArrowRight, CheckCircle2 } from "lucide-react";

interface DimensionScore {
  name: string;
  score: number;
  hopStage: string;
  desc: string;
}

const dimensions: DimensionScore[] = [
  { name: "Hop4 参数 AST 校验", score: 1.0, hopStage: "Hop 4", desc: "参数语法树与强类型合规" },
  { name: "Hop5 容错自愈与恢复", score: 1.0, hopStage: "Hop 5", desc: "下游 API 故障注入恢复率" },
  { name: "Hop6 记忆与活锁抑制", score: 1.0, hopStage: "Hop 6", desc: "避免连续重复调用死循环" },
  { name: "Hop7 业务政策与安全", score: 1.0, hopStage: "Hop 7", desc: "抵御提示词越权与删库攻击" },
  { name: "MAS 协同通信信噪比", score: 0.95, hopStage: "MAS", desc: "团队有效业务 Token 占比" },
  { name: "数字沙盒状态差分达成", score: 1.0, hopStage: "World State", desc: "真实数据库变更 100% 达成" },
  { name: "蚂蚁 SOP 流程合规度量", score: 1.0, hopStage: "Ant AIEvo", desc: "严格遵循业务有向图，严禁跳步" },
];

export function AttributionRadarView() {
  return (
    <div className="w-full space-y-6">
      {/* 顶部：6 大维度能力得分卡片 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {dimensions.map((d, idx) => (
          <div key={idx} className="glass-card rounded-xl p-4 border border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-cyber-cyan border border-cyber-cyan/20">
                {d.hopStage}
              </span>
              <span className="text-sm font-bold font-mono text-emerald-pulse">
                {(d.score * 100).toFixed(0)}%
              </span>
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-100">{d.name}</h4>
              <p className="text-[11px] text-slate-400 font-sans mt-0.5">{d.desc}</p>
            </div>
            <div className="w-full bg-obsidian-950 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-gradient-to-r from-cyber-cyan to-emerald-pulse h-full rounded-full transition-all duration-500"
                style={{ width: `${d.score * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* 下方：阿里 7-Hop 全生命周期因果流水线与故障根因树 */}
      <div className="glass-panel rounded-2xl p-6 border border-white/10 space-y-5">
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-2.5">
            <GitBranch className="w-5 h-5 text-cyber-cyan" />
            <h3 className="text-sm font-bold text-slate-100 font-mono uppercase tracking-wider">
              阿里 7-Hop 全链路执行拓扑与因果诊断树
            </h3>
          </div>
          <span className="text-xs text-emerald-pulse font-mono flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4" /> 当前用例: 全链路无阻塞
          </span>
        </div>

        {/* 7-Hop 瀑布流步进卡片 */}
        <div className="grid grid-cols-1 sm:grid-cols-7 gap-2.5 font-mono text-xs">
          {[
            { hop: "Hop 1", name: "意图与槽位", status: "passed" },
            { hop: "Hop 2", name: "路由与规划", status: "passed" },
            { hop: "Hop 3", name: "工具检索", status: "passed" },
            { hop: "Hop 4", name: "参数 AST 校验", status: "passed" },
            { hop: "Hop 5", name: "沙盒执行差分", status: "passed" },
            { hop: "Hop 6", name: "记忆与反思", status: "passed" },
            { hop: "Hop 7", name: "安全响应红线", status: "passed" },
          ].map((h, i) => (
            <div
              key={i}
              className="p-3 rounded-lg bg-obsidian-950/80 border border-emerald-pulse/30 text-center space-y-1 relative"
            >
              <span className="text-[10px] text-cyber-azure">{h.hop}</span>
              <p className="text-[11px] font-bold text-slate-200">{h.name}</p>
              <span className="text-[9px] text-emerald-pulse font-bold block">100% 达标</span>
            </div>
          ))}
        </div>

        {/* 自动化根因归因与优化建议卡片 */}
        <div className="bg-obsidian-950/80 rounded-xl p-4 border border-white/5 space-y-3">
          <h4 className="text-xs font-bold text-slate-200 font-mono flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-flame" /> 系统级因果归因与行动指南 (Actionable Fixes)
          </h4>
          <ul className="space-y-2 text-xs text-slate-300 font-sans">
            <li className="flex items-start gap-2">
              <span className="text-cyber-cyan font-mono mt-0.5">01.</span>
              <span><strong>开箱凭证主动询问率达成 100%</strong>：Agent 严格遵循了美团电商售后二元流程，有效杜绝了无凭证直接越权退款。</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-cyber-cyan font-mono mt-0.5">02.</span>
              <span><strong>沙盒数据库状态差分通过</strong>：目标表 orders 的状态已被物理更新为 CANCELLED，事务提交正常。</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-cyber-cyan font-mono mt-0.5">03.</span>
              <span><strong>建议进一步优化首轮响应延迟</strong>：当前单轮 P95 耗时为 1200ms，建议开启流式输出提升用户端响应体感。</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
