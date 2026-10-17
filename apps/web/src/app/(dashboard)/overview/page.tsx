"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowUpRight,
  Bot,
  Database,
  FlaskConical,
  Plus,
  ShieldCheck,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useResource } from "@/hooks/use-resource";
import type { Agent, Dataset, EvalRun, EvaluationTeam, Experiment } from "@/lib/types";
import { formatDate, formatPercent, statusMeta } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { PageSkeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { ScoreRing } from "@/components/ui/score-ring";
import { StatCard } from "@/components/ui/stat-card";

function decisionFor(passRate: number, errors: number) {
  if (errors > 0 && passRate < 0.5) return { label: "阻断发布", tone: "danger" as const };
  if (passRate >= 0.95 && errors === 0) return { label: "可发布", tone: "success" as const };
  if (passRate >= 0.8) return { label: "需复核", tone: "warning" as const };
  return { label: "阻断发布", tone: "danger" as const };
}

export default function OverviewPage() {
  const { workspaceId, workspace } = useAuth();
  const router = useRouter();
  const agents = useResource<Agent[]>(
    `agents:${workspaceId}`,
    () => api.listAgents(workspaceId as string),
    Boolean(workspaceId),
  );
  const datasets = useResource<Dataset[]>(
    `datasets:${workspaceId}`,
    () => api.listDatasets(workspaceId as string),
    Boolean(workspaceId),
  );
  const experiments = useResource<Experiment[]>(
    `experiments:${workspaceId}`,
    () => api.listExperiments(workspaceId as string),
    Boolean(workspaceId),
  );
  const teams = useResource<EvaluationTeam[]>(
    `teams:${workspaceId}`,
    () => api.listTeams(workspaceId as string),
    Boolean(workspaceId),
  );
  const runs = useResource<EvalRun[]>(
    `runs:${workspaceId}`,
    () => api.listRuns(workspaceId as string),
    Boolean(workspaceId),
  );

  if (agents.loading || datasets.loading || experiments.loading) return <PageSkeleton />;

  const agentList = agents.data ?? [];
  const datasetList = datasets.data ?? [];
  const experimentList = experiments.data ?? [];
  const teamList = teams.data ?? [];
  const runList = runs.data ?? [];
  const agentMap = new Map(agentList.map((agent) => [agent.id, agent.name]));
  const datasetMap = new Map(datasetList.map((dataset) => [dataset.id, dataset.name]));

  const latest = experimentList[0] ?? null;
  const gateExperiment =
    experimentList.find((item) => !["running", "queued"].includes(item.status)) ?? latest;
  const latestSummary = gateExperiment?.summary;
  const passRate = latestSummary?.score ?? 0;
  const errors = latestSummary?.error_count ?? 0;
  const flaky = latestSummary?.flaky_cases ?? 0;
  const decision = decisionFor(passRate, errors);
  const recent = experimentList.slice(0, 5);
  const trend = experimentList.slice(0, 8).reverse();

  return (
    <div>
      <PageHeader
        eyebrow={workspace?.name ?? "工作台"}
        title="概览"
        description="从这里查看 Agent 质量、最近实验和发布门禁状态。"
        actions={
          <Button icon={<Plus className="h-4 w-4" />} onClick={() => router.push("/evaluations")}>
            新建评测
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Agent 资产"
          value={agentList.length}
          note="已注册的可评测目标"
          icon={<Bot className="h-4 w-4" />}
        />
        <StatCard
          label="数据集"
          value={datasetList.length}
          note={`${datasetList.reduce((sum, dataset) => sum + (dataset.case_count ?? 0), 0)} 条用例`}
          icon={<Database className="h-4 w-4" />}
        />
        <StatCard
          label="评测实验"
          value={experimentList.length}
          note={`${teamList.length} 个评测团队`}
          icon={<FlaskConical className="h-4 w-4" />}
        />
        <StatCard
          label="最近通过率"
          value={gateExperiment ? formatPercent(passRate, 1) : "—"}
          note={gateExperiment ? `${gateExperiment.repetitions} 次重复` : "还没有完成的实验"}
          icon={<ShieldCheck className="h-4 w-4" />}
          tone={passRate >= 0.95 ? "success" : passRate >= 0.8 ? "warning" : "danger"}
        />
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-[1.55fr_1fr]">
        <section className="overflow-hidden rounded-2xl border border-app-line bg-app-surface">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-app-line px-5 py-4">
            <div>
              <h2 className="text-sm font-semibold text-app-text">最近实验</h2>
              <p className="mt-0.5 text-xs text-app-muted">按创建时间倒序，点击查看报告。</p>
            </div>
            <Link
              href="/evaluations"
              className="inline-flex items-center gap-1 text-xs font-medium text-brand hover:underline"
            >
              全部实验
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {recent.length === 0 ? (
            <div className="p-5">
              <EmptyState
                icon={<FlaskConical className="h-8 w-8" />}
                title="还没有实验"
                description="创建 Agent 和数据集后，运行第一次评测。"
                action={
                  <Button size="sm" onClick={() => router.push("/evaluations")}>
                    去评测
                  </Button>
                }
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[620px] text-left">
                <thead>
                  <tr className="border-b border-app-line bg-app-subtle text-[11px] uppercase tracking-wider text-app-muted">
                    <th className="px-5 py-3 font-medium">实验</th>
                    <th className="px-5 py-3 font-medium">状态</th>
                    <th className="px-5 py-3 font-medium">通过率</th>
                    <th className="px-5 py-3 font-medium">时间</th>
                    <th className="px-5 py-3 font-medium" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-app-line">
                  {recent.map((experiment) => {
                    const meta = statusMeta(experiment.status);
                    const rate = experiment.summary.score ?? 0;
                    const agentName =
                      experiment.summary.agent_name ??
                      agentMap.get(experiment.agent_id) ??
                      experiment.agent_id;
                    const datasetName =
                      experiment.summary.dataset_name ??
                      datasetMap.get(experiment.dataset_id) ??
                      experiment.dataset_id;
                    return (
                      <tr key={experiment.id} className="text-sm hover:bg-app-subtle/60">
                        <td className="px-5 py-3">
                          <p className="font-medium text-app-text">{agentName}</p>
                          <p className="text-xs text-app-muted">{datasetName}</p>
                        </td>
                        <td className="px-5 py-3">
                          <Badge tone={meta.tone}>{meta.label}</Badge>
                        </td>
                        <td className="px-5 py-3">
                          <div className="w-24">
                            <span className="text-xs font-medium text-app-text">
                              {formatPercent(rate, 1)}
                            </span>
                            <Progress
                              value={rate}
                              tone={rate >= 0.95 ? "success" : rate >= 0.8 ? "warning" : "danger"}
                              className="mt-1"
                            />
                          </div>
                        </td>
                        <td className="px-5 py-3 text-xs text-app-muted">
                          {formatDate(experiment.created_at)}
                        </td>
                        <td className="px-5 py-3">
                          <Link
                            href={`/evaluations/experiments/${experiment.id}`}
                            className="inline-flex items-center gap-1 text-xs font-medium text-brand hover:underline"
                          >
                            报告
                            <ArrowUpRight className="h-3.5 w-3.5" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-app-line bg-app-surface p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-app-text">发布门禁</h2>
              <p className="mt-0.5 text-xs text-app-muted">最近一次完成的实验。</p>
            </div>
            <Badge tone={gateExperiment ? decision.tone : "neutral"}>
              {gateExperiment ? decision.label : "未评估"}
            </Badge>
          </div>

          {!gateExperiment ? (
            <div className="mt-6">
              <EmptyState
                icon={<ShieldCheck className="h-8 w-8" />}
                title="还没有门禁结论"
                description="完成一次评测后，这里会给出是否可发布的建议。"
              />
            </div>
          ) : (
            <>
              <div className="mt-5 flex items-center gap-4">
                <ScoreRing value={passRate} tone={decision.tone} size={112} label="通过率" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-app-text">{decision.label}</p>
                  <p className="mt-1 text-xs leading-5 text-app-muted">
                    {passRate >= 0.95 && errors === 0
                      ? "通过率达到阈值，且没有执行错误。"
                      : "存在失败或错误样本，建议先查看证据再决定是否发布。"}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-app-muted">
                    <span>{latestSummary?.passed_cases ?? 0}/{latestSummary?.total_cases ?? 0} 通过</span>
                    <span>错误 {errors}</span>
                    <span>Flaky {flaky}</span>
                  </div>
                </div>
              </div>
              <Link
                href={`/evaluations/experiments/${gateExperiment.id}`}
                className="mt-5 flex items-center justify-between rounded-lg border border-app-line px-3 py-2 text-xs font-medium text-app-text hover:bg-app-subtle"
              >
                查看完整报告
                <ArrowUpRight className="h-3.5 w-3.5 text-app-muted" />
              </Link>
            </>
          )}
        </section>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-[1.55fr_1fr]">
        <section className="rounded-2xl border border-app-line bg-app-surface p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-app-text">质量趋势</h2>
              <p className="mt-0.5 text-xs text-app-muted">最近 8 次实验的通过率。</p>
            </div>
            <Activity className="h-4 w-4 text-app-muted" />
          </div>

          {trend.length === 0 ? (
            <p className="py-12 text-center text-sm text-app-muted">还没有趋势数据。</p>
          ) : (
            <div className="mt-6 flex h-48 items-end gap-2 sm:gap-3">
              {trend.map((experiment) => {
                const rate = experiment.summary.score ?? 0;
                return (
                  <div key={experiment.id} className="flex min-w-0 flex-1 flex-col items-center gap-2">
                    <span className="text-[10px] text-app-muted">{formatPercent(rate, 0)}</span>
                    <div
                      className="flex h-32 w-full items-end rounded-md bg-app-subtle"
                      title={`${experiment.id} · ${formatPercent(rate, 1)}`}
                    >
                      <div
                        className={
                          rate >= 0.95
                            ? "w-full rounded-md bg-emerald-500/80"
                            : rate >= 0.8
                              ? "w-full rounded-md bg-amber-500/80"
                              : "w-full rounded-md bg-red-500/80"
                        }
                        style={{ height: `${Math.max(4, rate * 100)}%` }}
                      />
                    </div>
                    <span className="w-full truncate text-center text-[10px] text-app-muted">
                      {formatDate(experiment.created_at).slice(0, 5)}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-app-line bg-app-surface p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-app-text">快速开始</h2>
              <p className="mt-0.5 text-xs text-app-muted">从资产到门禁的四步。</p>
            </div>
            <Users className="h-4 w-4 text-app-muted" />
          </div>
          <ol className="mt-4 space-y-2">
            {[
              { step: "1", title: "注册 Agent", hint: `${agentList.length} 个资产`, href: "/agents" },
              { step: "2", title: "创建数据集", hint: `${datasetList.length} 个数据集`, href: "/datasets" },
              { step: "3", title: "配置评测团队", hint: `${teamList.length} 个团队`, href: "/teams" },
              { step: "4", title: "运行并查看报告", hint: `${runList.length} 次运行`, href: "/evaluations" },
            ].map((item) => (
              <li key={item.step}>
                <Link
                  href={item.href}
                  className="flex items-center gap-3 rounded-lg border border-app-line px-3 py-2.5 hover:bg-app-subtle"
                >
                  <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-brand-soft text-xs font-semibold text-brand">
                    {item.step}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-xs font-medium text-app-text">{item.title}</span>
                    <span className="block text-[11px] text-app-muted">{item.hint}</span>
                  </span>
                  <ArrowUpRight className="h-3.5 w-3.5 text-app-muted" />
                </Link>
              </li>
            ))}
          </ol>
        </section>
      </div>
    </div>
  );
}
