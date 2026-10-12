"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Bot,
  CheckCircle2,
  DatabaseZap,
  Gavel,
  MessageSquare,
  ShieldAlert,
  Sparkles,
  UserRound,
  Wrench,
} from "lucide-react";

export type TraceEvent = {
  actor_role?: string;
  event_type?: string;
  turn_index?: number;
  content?: string;
  tool_observation?: { tool_name?: string; is_error?: boolean; output?: unknown };
};

type AgentLiveBoardProps = {
  running: boolean;
  events?: TraceEvent[];
  agentName?: string;
  modelName?: string;
};

const stages = [
  { id: "user_simulator", label: "用户模拟官", icon: UserRound, tone: "cyan" },
  { id: "testee_agent", label: "被测 Agent", icon: Bot, tone: "indigo" },
  { id: "tool_sandbox", label: "工具沙盒", icon: DatabaseZap, tone: "amber" },
  { id: "judicial_committee", label: "裁决委员会", icon: Gavel, tone: "violet" },
];

const runningStages = [
  { label: "初始化测试上下文", detail: "加载数据集快照与任务约束" },
  { label: "用户模拟官施压", detail: "按状态机释放隐藏意图" },
  { label: "目标 Agent 响应", detail: "采集回复、工具调用与资源消耗" },
  { label: "沙盒状态核验", detail: "比对物理状态差分" },
  { label: "裁决委员会合议", detail: "规则法官与安全法官独立盲审" },
];

function eventStage(event: TraceEvent) {
  if (event.actor_role === "user_simulator") return "user_simulator";
  if (event.actor_role === "testee_agent") {
    return event.event_type === "tool_call_request" ? "tool_sandbox" : "testee_agent";
  }
  return "judicial_committee";
}

function eventCopy(event: TraceEvent) {
  if (event.tool_observation?.tool_name) {
    return `${event.tool_observation.tool_name} ${event.tool_observation.is_error ? "执行异常" : "执行完成"}`;
  }
  return event.content || event.event_type || "已记录事件";
}

export function AgentLiveBoard({
  running,
  events = [],
  agentName = "目标 Agent",
  modelName = "未配置模型",
}: AgentLiveBoardProps) {
  const [runningIndex, setRunningIndex] = useState(0);
  const [replayIndex, setReplayIndex] = useState(Math.max(events.length - 1, 0));
  const [replaying, setReplaying] = useState(false);

  useEffect(() => {
    if (!running) return;
    setRunningIndex(0);
    const timer = window.setInterval(() => {
      setRunningIndex((index) => (index + 1) % runningStages.length);
    }, 950);
    return () => window.clearInterval(timer);
  }, [running]);

  useEffect(() => {
    if (!events.length || running) return;
    setReplayIndex(0);
    setReplaying(true);
    const timer = window.setInterval(() => {
      setReplayIndex((index) => {
        if (index >= events.length - 1) {
          window.clearInterval(timer);
          setReplaying(false);
          return index;
        }
        return index + 1;
      });
    }, 560);
    return () => window.clearInterval(timer);
  }, [events, running]);

  const visibleEvents = useMemo(() => {
    if (running || !events.length) return [];
    return events.slice(Math.max(0, replayIndex - 2), replayIndex + 1);
  }, [events, replayIndex, running]);

  const activeStage = running
    ? stages[(runningIndex === 1 ? 0 : runningIndex === 2 ? 1 : runningIndex >= 3 ? 2 : 1)]
    : events.length
      ? stages.find((stage) => stage.id === eventStage(events[replayIndex])) || stages[1]
      : stages[0];

  return (
    <section className="agent-live-board" aria-label="多 Agent 协作动态观测">
      <div className="live-board-head">
        <div>
          <p className="eyebrow">Live orchestration</p>
          <h2>多 Agent 协作观测</h2>
          <p className="muted">
            {running
              ? "当前是执行调度状态，完成后将按真实 Trace 回放每个参与者的证据。"
              : events.length
                ? `${replaying ? "正在回放" : "回放完成"} · ${events.length} 条真实 Trace 事件`
                : "启动实验后，这里会显示用户模拟、目标 Agent、工具沙盒与裁决链路。"}
          </p>
        </div>
        <div className={`live-status ${running || replaying ? "is-active" : "is-idle"}`}>
          <span />
          {running ? "RUNNING" : replaying ? "REPLAYING" : events.length ? "TRACE READY" : "IDLE"}
        </div>
      </div>

      <div className="agent-network">
        {stages.map((stage, index) => {
          const Icon = stage.icon;
          const active = activeStage.id === stage.id;
          return (
            <div className="agent-network-step" key={stage.id}>
              <div className={`agent-node ${stage.tone} ${active ? "active" : ""}`}>
                <div className="agent-node-icon"><Icon size={17} /></div>
                <div className="agent-node-copy">
                  <strong>{stage.label}</strong>
                  <small>
                    {stage.id === "testee_agent" ? `${agentName} · ${modelName}` :
                      stage.id === "user_simulator" ? "FSM / hidden goal" :
                        stage.id === "tool_sandbox" ? "state diff / tool guard" : "rule + safety judge"}
                  </small>
                </div>
                {active && <Sparkles size={14} className="agent-node-spark" />}
              </div>
              {index < stages.length - 1 && <div className={`agent-network-link ${active ? "active" : ""}`}><span /></div>}
            </div>
          );
        })}
      </div>

      <div className="live-board-grid">
        <div className="live-stage-panel">
          <div className="live-stage-kicker">
            <span className="live-stage-dot" />
            {running ? "当前调度阶段" : "当前 Trace 阶段"}
          </div>
          <strong>{running ? runningStages[runningIndex].label : activeStage.label}</strong>
          <p>{running ? runningStages[runningIndex].detail : events.length ? eventCopy(events[replayIndex]) : "等待实验启动"}</p>
          <div className="live-progress">
            <span style={{ width: `${running ? ((runningIndex + 1) / runningStages.length) * 100 : events.length ? ((replayIndex + 1) / events.length) * 100 : 0}%` }} />
          </div>
        </div>
        <div className="live-event-feed">
          {running ? (
            runningStages.slice(0, runningIndex + 1).map((stage) => (
              <div className="live-feed-row" key={stage.label}>
                <CheckCircle2 size={14} />
                <span>{stage.label}</span>
                <small>已记录</small>
              </div>
            ))
          ) : visibleEvents.length ? (
            visibleEvents.map((event, index) => (
              <div className="live-feed-row" key={`${event.event_type}-${replayIndex}-${index}`}>
                {event.tool_observation?.tool_name ? <Wrench size={14} /> : event.actor_role === "user_simulator" ? <MessageSquare size={14} /> : event.event_type === "tool_call_request" ? <ShieldAlert size={14} /> : <Bot size={14} />}
                <span>{eventCopy(event)}</span>
                <small>T{event.turn_index || 0}</small>
              </div>
            ))
          ) : (
            <div className="live-feed-empty">暂无事件，等待真实执行 Trace。</div>
          )}
        </div>
      </div>
    </section>
  );
}
