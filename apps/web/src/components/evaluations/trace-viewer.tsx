"use client";

import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import type { ExecutionTrace, Tone, TraceEvent } from "@/lib/types";
import { formatDate, formatDuration } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Input, Select } from "@/components/ui/field";

const actorLabels: Record<string, string> = {
  user_simulator: "用户模拟官",
  red_team_attacker: "红队攻击官",
  testee_agent: "被测 Agent",
  tool_sandbox: "沙盒工具",
  business_judge: "业务法官",
  safety_judge: "安全法官",
  moderator: "首席仲裁",
  watchdog: "看门狗",
};

const eventLabels: Record<string, string> = {
  user_message: "用户消息",
  agent_thought: "Agent 思考",
  agent_message: "Agent 回复",
  tool_call_request: "工具调用",
  tool_call_response: "工具结果",
  fault_injected: "故障注入",
  state_snapshot: "状态快照",
  evaluator_call: "评委调用",
  judge_verdict: "评委裁决",
  arbitration: "仲裁",
};

const actorTone: Record<string, Tone> = {
  user_simulator: "info",
  red_team_attacker: "danger",
  testee_agent: "success",
  tool_sandbox: "warning",
  business_judge: "info",
  safety_judge: "warning",
  moderator: "neutral",
  watchdog: "danger",
};

export function TraceViewer({ trace }: { trace: ExecutionTrace | null | undefined }) {
  const [actor, setActor] = useState("all");
  const [eventType, setEventType] = useState("all");
  const [query, setQuery] = useState("");

  const events = useMemo(() => {
    if (!trace?.events) return [];
    const text = query.trim().toLowerCase();
    return trace.events
      .filter((event) => actor === "all" || event.actor_role === actor)
      .filter((event) => eventType === "all" || event.event_type === eventType)
      .filter((event) => {
        if (!text) return true;
        return (
          event.content.toLowerCase().includes(text) ||
          event.actor_name.toLowerCase().includes(text) ||
          event.tool_observation?.tool_name.toLowerCase().includes(text)
        );
      })
      .slice()
      .sort((left, right) => left.timestamp.localeCompare(right.timestamp));
  }, [trace, actor, eventType, query]);

  if (!trace) {
    return (
      <EmptyState
        title="没有 Trace"
        description="该样本没有可回放的执行事件，可能是运行尚未开始或执行失败。"
      />
    );
  }

  const actorOptions = Array.from(new Set(trace.events.map((event) => event.actor_role)));
  const eventOptions = Array.from(new Set(trace.events.map((event) => event.event_type)));

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-3 rounded-lg border border-app-line bg-app-subtle p-3">
        <div className="relative min-w-48 flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-app-muted" />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="搜索事件内容或工具名"
            className="bg-white pl-9"
          />
        </div>
        <Select value={actor} onChange={(event) => setActor(event.target.value)} className="w-40 bg-white">
          <option value="all">全部角色</option>
          {actorOptions.map((value) => (
            <option key={value} value={value}>
              {actorLabels[value] || value}
            </option>
          ))}
        </Select>
        <Select
          value={eventType}
          onChange={(event) => setEventType(event.target.value)}
          className="w-40 bg-white"
        >
          <option value="all">全部事件</option>
          {eventOptions.map((value) => (
            <option key={value} value={value}>
              {eventLabels[value] || value}
            </option>
          ))}
        </Select>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-2 text-xs text-app-muted sm:grid-cols-4">
        <span>Trace：{trace.trace_id}</span>
        <span>事件：{trace.events.length}</span>
        <span>Token：{trace.total_tokens}</span>
        <span>耗时：{formatDuration(trace.total_duration_ms)}</span>
      </div>

      {events.length === 0 ? (
        <EmptyState title="没有匹配的事件" description="调整筛选条件或搜索关键词。" />
      ) : (
        <ol className="space-y-3">
          {events.map((event) => (
            <TraceEventItem key={event.event_id} event={event} />
          ))}
        </ol>
      )}
    </div>
  );
}

function TraceEventItem({ event }: { event: TraceEvent }) {
  const observation = event.tool_observation;
  return (
    <li className="rounded-lg border border-app-line bg-app-surface p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={actorTone[event.actor_role] || "neutral"}>
          {actorLabels[event.actor_role] || event.actor_role}
        </Badge>
        <span className="text-xs font-medium text-app-text">
          {eventLabels[event.event_type] || event.event_type}
        </span>
        <span className="text-xs text-app-muted">第 {event.turn_index} 轮</span>
        <span className="text-xs text-app-muted">{formatDate(event.timestamp)}</span>
        {event.tokens_consumed > 0 && (
          <span className="text-xs text-app-muted">{event.tokens_consumed} tokens</span>
        )}
      </div>

      {event.content && (
        <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-app-text">
          {event.content}
        </p>
      )}

      {event.thought && (
        <details className="mt-2 rounded-lg border border-app-line bg-app-subtle p-3">
          <summary className="cursor-pointer text-xs font-medium text-app-muted">思考过程</summary>
          <p className="mt-2 whitespace-pre-wrap break-words text-xs leading-5 text-app-text">
            {event.thought}
          </p>
        </details>
      )}

      {observation && (
        <div className="mt-3 rounded-lg border border-app-line bg-app-subtle p-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs font-semibold text-app-text">
              {observation.tool_name}
            </span>
            {observation.is_error ? (
              <Badge tone="danger">错误</Badge>
            ) : (
              <Badge tone="success">成功</Badge>
            )}
            <span className="text-xs text-app-muted">{formatDuration(observation.duration_ms)}</span>
          </div>
          <details className="mt-2">
            <summary className="cursor-pointer text-xs text-app-muted">参数与返回</summary>
            <div className="mt-2 grid gap-2 lg:grid-cols-2">
              <pre className="max-h-48 overflow-auto rounded-md bg-slate-950 p-2 text-[11px] leading-5 text-slate-100">
                {JSON.stringify(observation.arguments, null, 2)}
              </pre>
              <pre className="max-h-48 overflow-auto rounded-md bg-slate-950 p-2 text-[11px] leading-5 text-slate-100">
                {JSON.stringify(observation.output, null, 2)}
              </pre>
            </div>
          </details>
        </div>
      )}

      {Object.keys(event.metadata ?? {}).length > 0 && (
        <details className="mt-2">
          <summary className="cursor-pointer text-xs text-app-muted">元数据</summary>
          <pre className="mt-1 max-h-40 overflow-auto rounded-md bg-app-subtle p-2 text-[11px] leading-5 text-app-muted">
            {JSON.stringify(event.metadata, null, 2)}
          </pre>
        </details>
      )}
    </li>
  );
}
