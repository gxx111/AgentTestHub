"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  Clock3,
  FlaskConical,
  Play,
  ShieldCheck,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";
import type {
  Agent,
  Dataset,
  EvaluationTeam,
  Policy,
  StreamState,
  TestCase,
  UniversalRunResponse,
} from "@/lib/types";
import { formatDuration } from "@/lib/format";
import { uid } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input, Select } from "@/components/ui/field";
import { useToast } from "@/components/ui/toast";

interface LaunchPanelProps {
  workspaceId: string;
  agents: Agent[];
  datasets: Dataset[];
  teams: EvaluationTeam[];
  policies: Policy[];
  initialDatasetId?: string | null;
  onCompleted: (result: UniversalRunResponse) => void;
}

function latestEvent(stream: StreamState | null): string {
  const last = stream?.events?.[stream.events.length - 1] as
    | { event?: { content?: unknown; event_type?: unknown } }
    | undefined;
  if (typeof last?.event?.content === "string" && last.event.content) return last.event.content;
  if (typeof last?.event?.event_type === "string") return last.event.event_type;
  return "等待评测事件…";
}

export function LaunchPanel({
  workspaceId,
  agents,
  datasets,
  teams,
  policies,
  initialDatasetId,
  onCompleted,
}: LaunchPanelProps) {
  const toast = useToast();
  const [agentId, setAgentId] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [teamId, setTeamId] = useState("");
  const [policyId, setPolicyId] = useState("");
  const [repetitions, setRepetitions] = useState(1);
  const [caseId, setCaseId] = useState("");
  const [cases, setCases] = useState<TestCase[]>([]);
  const [loadingCases, setLoadingCases] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [streamId, setStreamId] = useState<string | null>(null);
  const [stream, setStream] = useState<StreamState | null>(null);

  useEffect(() => {
    if (!agentId && agents.length > 0) setAgentId(agents[0].id);
  }, [agents, agentId]);

  useEffect(() => {
    if (datasetId) return;
    const preferred =
      initialDatasetId && datasets.some((item) => item.id === initialDatasetId)
        ? initialDatasetId
        : datasets[0]?.id;
    if (preferred) setDatasetId(preferred);
  }, [datasets, datasetId, initialDatasetId]);

  useEffect(() => {
    if (!teamId && teams.length > 0) setTeamId(teams[0].id);
  }, [teams, teamId]);

  useEffect(() => {
    if (!datasetId) {
      setCases([]);
      setCaseId("");
      return;
    }
    let cancelled = false;
    setLoadingCases(true);
    setCaseId("");
    api
      .getDataset(datasetId)
      .then((detail) => {
        if (!cancelled) setCases(detail.cases);
      })
      .catch(() => {
        if (!cancelled) setCases([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingCases(false);
      });
    return () => {
      cancelled = true;
    };
  }, [datasetId]);

  useEffect(() => {
    if (!running || !streamId) return;
    const started = Date.now();
    const tick = window.setInterval(() => setElapsed(Date.now() - started), 1000);
    const poll = window.setInterval(() => {
      api
        .getStream(streamId)
        .then(setStream)
        .catch(() => undefined);
    }, 1500);
    return () => {
      window.clearInterval(tick);
      window.clearInterval(poll);
    };
  }, [running, streamId]);

  const selectedAgent = agents.find((item) => item.id === agentId) ?? null;
  const selectedDataset = datasets.find((item) => item.id === datasetId) ?? null;
  const selectedTeam = teams.find((item) => item.id === teamId) ?? null;
  const selectedPolicy = policies.find((item) => item.id === policyId) ?? null;
  const selectedCase = cases.find((item) => item.id === caseId) ?? null;
  const caseCount = selectedCase ? 1 : cases.length;
  const totalExecutions = caseCount * repetitions;
  const canRun = Boolean(agentId && datasetId && caseCount > 0 && !running);

  const summaryRows = useMemo(
    () => [
      { label: "Agent", value: selectedAgent?.name ?? "未选择" },
      { label: "数据集", value: selectedDataset?.name ?? "未选择" },
      { label: "用例", value: selectedCase ? "单条用例" : `${caseCount} 条` },
      { label: "评委", value: selectedTeam?.name ?? "内置启发式评委" },
      { label: "重复", value: `${repetitions} 次` },
      { label: "总执行", value: `${totalExecutions} 次` },
    ],
    [selectedAgent, selectedDataset, selectedCase, caseCount, selectedTeam, repetitions, totalExecutions],
  );

  async function handleRun() {
    setError("");
    if (!agentId || !datasetId) {
      setError("请选择 Agent 和数据集");
      return;
    }
    if (caseCount === 0) {
      setError("该数据集没有用例，请先添加用例");
      return;
    }
    const nextStreamId = uid("stream");
    setRunning(true);
    setElapsed(0);
    setStream(null);
    setStreamId(nextStreamId);
    try {
      const result = await api.universalRun({
        workspace_id: workspaceId,
        agent_id: agentId,
        dataset_id: datasetId,
        policy_id: policyId || null,
        evaluation_team_id: teamId || null,
        case_id: caseId || null,
        repetitions,
        stream_id: nextStreamId,
      });
      toast.push("评测完成，正在打开报告", "success");
      onCompleted(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "评测失败";
      setError(message);
      toast.push(message, "error");
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="overflow-hidden rounded-2xl border border-app-line bg-app-surface shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-app-line px-5 py-5 sm:px-6">
        <div className="flex items-start gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-brand-soft text-brand">
            <FlaskConical className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-app-text">新建评测</h2>
            <p className="mt-0.5 text-sm text-app-muted">
              选择被测 Agent、数据集和评测团队，运行一次可审计的实验。
            </p>
          </div>
        </div>
        <Badge tone="info">Beta · 同步执行</Badge>
      </div>

      <div className="grid gap-6 p-5 sm:p-6 lg:grid-cols-[1.35fr_0.65fr]">
        <div className="space-y-4">
          {agents.length === 0 || datasets.length === 0 ? (
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              还没有可用的
              {agents.length === 0 ? " Agent" : ""}
              {agents.length === 0 && datasets.length === 0 ? " 和" : ""}
              {datasets.length === 0 ? " 数据集" : ""}。
              {agents.length === 0 && (
                <Link href="/agents" className="ml-1 font-medium underline">
                  先创建 Agent
                </Link>
              )}
              {datasets.length === 0 && (
                <Link href="/datasets" className="ml-1 font-medium underline">
                  先创建数据集
                </Link>
              )}
            </div>
          ) : null}

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="被测 Agent" required>
              <Select value={agentId} onChange={(event) => setAgentId(event.target.value)}>
                <option value="">请选择 Agent</option>
                {agents.map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name} · {agent.model_name || agent.agent_type}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="数据集" required>
              <Select value={datasetId} onChange={(event) => setDatasetId(event.target.value)}>
                <option value="">请选择数据集</option>
                {datasets.map((dataset) => (
                  <option key={dataset.id} value={dataset.id}>
                    {dataset.name} · {dataset.case_count ?? 0} 用例
                  </option>
                ))}
              </Select>
            </Field>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="评测团队" hint="不选择时使用内置启发式评委">
              <Select value={teamId} onChange={(event) => setTeamId(event.target.value)}>
                <option value="">不启用评测团队</option>
                {teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name} · {team.members.filter((member) => member.enabled).length} 个角色
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="重复次数" hint="1–20；高风险场景建议 ≥5">
              <Input
                type="number"
                min={1}
                max={20}
                value={repetitions}
                onChange={(event) =>
                  setRepetitions(Math.max(1, Math.min(20, Number(event.target.value) || 1)))
                }
              />
            </Field>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="评测策略" hint="可选：控制用户模拟官与轮次上限">
              <Select value={policyId} onChange={(event) => setPolicyId(event.target.value)}>
                <option value="">默认策略</option>
                {policies.map((policy) => (
                  <option key={policy.id} value={policy.id}>
                    {policy.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field
              label="单条用例"
              hint={loadingCases ? "正在加载用例…" : `不选择时运行全部 ${cases.length} 条`}
            >
              <Select
                value={caseId}
                onChange={(event) => setCaseId(event.target.value)}
                disabled={loadingCases || cases.length === 0}
              >
                <option value="">全部用例</option>
                {cases.map((testCase) => (
                  <option key={testCase.id} value={testCase.id}>
                    {testCase.title}
                  </option>
                ))}
              </Select>
            </Field>
          </div>

          {selectedTeam && (
            <div className="flex flex-wrap items-center gap-2 rounded-lg border border-app-line bg-app-subtle px-3 py-2 text-xs text-app-muted">
              <Users className="h-3.5 w-3.5" />
              <span>
                {selectedTeam.members
                  .filter((member) => member.enabled)
                  .map((member) => member.role)
                  .join(" · ")}
              </span>
              <span className="ml-auto">
                预算 {selectedTeam.max_calls} 次调用 / {selectedTeam.timeout_seconds}s
              </span>
            </div>
          )}

          {selectedPolicy && (
            <div className="flex flex-wrap items-center gap-2 rounded-lg border border-app-line bg-app-subtle px-3 py-2 text-xs text-app-muted">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>用户模拟：{selectedPolicy.user_sim_persona}</span>
              <span className="ml-auto">最大轮次 {selectedPolicy.watchdog_max_turns}</span>
            </div>
          )}
        </div>

        <aside className="rounded-xl border border-app-line bg-app-subtle p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-app-muted">评测摘要</p>
          <dl className="mt-4 space-y-3">
            {summaryRows.map((row) => (
              <div key={row.label} className="flex items-start justify-between gap-3">
                <dt className="text-xs text-app-muted">{row.label}</dt>
                <dd className="max-w-[60%] text-right text-xs font-medium text-app-text">
                  {row.value}
                </dd>
              </div>
            ))}
          </dl>

          {!selectedTeam && (
            <div className="mt-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-900">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>
                未配置 LLM 评测团队，本次使用内置启发式评委，结果仅适合流程验证。
                <Link href="/teams" className="ml-1 font-medium underline">
                  去配置
                </Link>
              </span>
            </div>
          )}

          <Button
            className="mt-5 w-full"
            loading={running}
            disabled={!canRun}
            icon={!running ? <Play className="h-4 w-4" /> : undefined}
            onClick={() => void handleRun()}
          >
            {running ? "评测运行中…" : "开始评测"}
          </Button>
          <p className="mt-2 text-center text-[11px] leading-4 text-app-muted">
            当前接口为同步执行，请保持页面打开。
          </p>
        </aside>
      </div>

      {running && (
        <div className="border-t border-blue-200 bg-blue-50/70 px-5 py-4 sm:px-6">
          <div className="flex flex-wrap items-center gap-3 text-sm text-blue-900">
            <Activity className="h-4 w-4 animate-pulse" />
            <span className="font-medium">评测运行中</span>
            <span className="inline-flex items-center gap-1 text-xs">
              <Clock3 className="h-3.5 w-3.5" />
              {formatDuration(elapsed)}
            </span>
            <span className="text-xs">
              {stream ? `${stream.events.length} 个事件` : "等待首批事件…"}
            </span>
          </div>
          <p className="mt-2 line-clamp-2 text-xs leading-5 text-blue-800">{latestEvent(stream)}</p>
          <p className="mt-1 text-[11px] text-blue-700">
            评测完成后会自动跳转到实验报告。若页面刷新，实验仍会在后端继续执行。
          </p>
        </div>
      )}

      {error && (
        <div className="border-t border-red-200 bg-red-50 px-5 py-3 text-sm text-red-700 sm:px-6">
          {error}
        </div>
      )}
    </section>
  );
}
