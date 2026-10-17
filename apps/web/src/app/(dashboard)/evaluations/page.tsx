"use client";

import { Suspense, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowUpRight, FlaskConical, History, Users } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useResource } from "@/hooks/use-resource";
import type {
  Agent,
  Dataset,
  EvalRun,
  EvaluationTeam,
  Experiment,
  Policy,
  UniversalRunResponse,
} from "@/lib/types";
import { formatDate, formatDuration, formatPercent, statusMeta } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { PageSkeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Tabs } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { LaunchPanel } from "@/components/evaluations/launch-panel";

export default function EvaluationsPage() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <EvaluationsContent />
    </Suspense>
  );
}

function EvaluationsContent() {
  const { workspaceId } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialDatasetId = searchParams.get("dataset");
  const [tab, setTab] = useState("experiments");

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
  const teams = useResource<EvaluationTeam[]>(
    `teams:${workspaceId}`,
    () => api.listTeams(workspaceId as string),
    Boolean(workspaceId),
  );
  const policies = useResource<Policy[]>(
    `policies:${workspaceId}`,
    () => api.listPolicies(workspaceId as string),
    Boolean(workspaceId),
  );
  const experiments = useResource<Experiment[]>(
    `experiments:${workspaceId}`,
    () => api.listExperiments(workspaceId as string),
    Boolean(workspaceId),
  );
  const runs = useResource<EvalRun[]>(
    `runs:${workspaceId}`,
    () => api.listRuns(workspaceId as string),
    Boolean(workspaceId),
  );

  const agentMap = useMemo(
    () => new Map((agents.data ?? []).map((agent) => [agent.id, agent.name])),
    [agents.data],
  );
  const datasetMap = useMemo(
    () => new Map((datasets.data ?? []).map((dataset) => [dataset.id, dataset.name])),
    [datasets.data],
  );

  function handleCompleted(result: UniversalRunResponse) {
    void experiments.refresh();
    void runs.refresh();
    router.push(`/evaluations/experiments/${result.experiment_id}`);
  }

  if (agents.loading || datasets.loading) return <PageSkeleton />;

  const agentList = agents.data ?? [];
  const datasetList = datasets.data ?? [];
  const teamList = teams.data ?? [];
  const policyList = policies.data ?? [];
  const experimentList = experiments.data ?? [];
  const runList = runs.data ?? [];
  const error = agents.error || datasets.error || experiments.error || runs.error;

  return (
    <div>
      <PageHeader
        eyebrow="工作台"
        title="评测实验"
        description="在发布前验证 Agent 的业务完成度、工具行为、世界状态与安全边界。"
        actions={
          <div className="flex gap-2">
            <Button
              variant="secondary"
              icon={<Users className="h-4 w-4" />}
              onClick={() => router.push("/teams")}
            >
              评测团队
            </Button>
            <Button
              variant="secondary"
              icon={<FlaskConical className="h-4 w-4" />}
              onClick={() => router.push("/datasets")}
            >
              数据集
            </Button>
          </div>
        }
      />

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
          <button
            className="ml-3 underline"
            onClick={() => {
              void agents.refresh();
              void datasets.refresh();
              void experiments.refresh();
              void runs.refresh();
            }}
          >
            重试
          </button>
        </div>
      )}

      {workspaceId && (
        <LaunchPanel
          workspaceId={workspaceId}
          agents={agentList}
          datasets={datasetList}
          teams={teamList}
          policies={policyList}
          initialDatasetId={initialDatasetId}
          onCompleted={handleCompleted}
        />
      )}

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <Tabs
          items={[
            { id: "experiments", label: "实验", count: experimentList.length },
            { id: "runs", label: "运行历史", count: runList.length },
          ]}
          value={tab}
          onChange={setTab}
        />
        <p className="text-xs text-app-muted">
          实验聚合多次重复；运行历史保留每一次独立执行。
        </p>
      </div>

      <div className="mt-4 overflow-hidden rounded-2xl border border-app-line bg-app-surface">
        {tab === "experiments" ? (
          experiments.loading ? (
            <div className="flex justify-center py-16">
              <Spinner className="h-6 w-6 text-brand" />
            </div>
          ) : experimentList.length === 0 ? (
            <div className="p-6">
              <EmptyState
                icon={<FlaskConical className="h-8 w-8" />}
                title="还没有评测实验"
                description="在上方选择 Agent 与数据集，运行第一次评测。"
              />
            </div>
          ) : (
            <ExperimentTable
              experiments={experimentList}
              agentMap={agentMap}
              datasetMap={datasetMap}
            />
          )
        ) : runs.loading ? (
          <div className="flex justify-center py-16">
            <Spinner className="h-6 w-6 text-brand" />
          </div>
        ) : runList.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={<History className="h-8 w-8" />}
              title="还没有运行记录"
              description="完成一次评测后，这里会保留每次独立运行。"
            />
          </div>
        ) : (
          <RunTable runs={runList} agentMap={agentMap} datasetMap={datasetMap} />
        )}
      </div>
    </div>
  );
}

function ExperimentTable({
  experiments,
  agentMap,
  datasetMap,
}: {
  experiments: Experiment[];
  agentMap: Map<string, string>;
  datasetMap: Map<string, string>;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[880px] text-left">
        <thead>
          <tr className="border-b border-app-line bg-app-subtle text-[11px] uppercase tracking-wider text-app-muted">
            <th className="px-5 py-3 font-medium">实验</th>
            <th className="px-5 py-3 font-medium">状态</th>
            <th className="px-5 py-3 font-medium">通过率</th>
            <th className="px-5 py-3 font-medium">平均分</th>
            <th className="px-5 py-3 font-medium">重复</th>
            <th className="px-5 py-3 font-medium">Flaky</th>
            <th className="px-5 py-3 font-medium">创建时间</th>
            <th className="px-5 py-3 font-medium" />
          </tr>
        </thead>
        <tbody className="divide-y divide-app-line">
          {experiments.map((experiment) => {
            const meta = statusMeta(experiment.status);
            const summary = experiment.summary;
            const agentName =
              summary.agent_name ?? agentMap.get(experiment.agent_id) ?? experiment.agent_id;
            const datasetName =
              summary.dataset_name ?? datasetMap.get(experiment.dataset_id) ?? experiment.dataset_id;
            const passRate = summary.score ?? 0;
            const flaky = summary.flaky_cases ?? 0;
            return (
              <tr key={experiment.id} className="text-sm hover:bg-app-subtle/60">
                <td className="px-5 py-4">
                  <p className="font-medium text-app-text">{agentName}</p>
                  <p className="mt-0.5 text-xs text-app-muted">{datasetName}</p>
                  <p className="mt-0.5 font-mono text-[10px] text-app-muted">{experiment.id}</p>
                </td>
                <td className="px-5 py-4">
                  <Badge tone={meta.tone}>{meta.label}</Badge>
                </td>
                <td className="px-5 py-4">
                  <div className="w-28">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-app-text">{formatPercent(passRate, 1)}</span>
                    </div>
                    <Progress
                      value={passRate}
                      tone={passRate >= 0.95 ? "success" : passRate >= 0.8 ? "warning" : "danger"}
                      className="mt-1.5"
                    />
                  </div>
                </td>
                <td className="px-5 py-4 text-app-text">
                  {formatPercent(summary.average_score ?? 0, 1)}
                </td>
                <td className="px-5 py-4 text-app-muted">{experiment.repetitions}</td>
                <td className="px-5 py-4">
                  {flaky > 0 ? <Badge tone="warning">{flaky}</Badge> : <span className="text-app-muted">0</span>}
                </td>
                <td className="px-5 py-4 text-xs text-app-muted">
                  {formatDate(experiment.created_at)}
                </td>
                <td className="px-5 py-4">
                  <Link
                    href={`/evaluations/experiments/${experiment.id}`}
                    className="inline-flex items-center gap-1 text-xs font-medium text-brand hover:underline"
                  >
                    查看报告
                    <ArrowUpRight className="h-3.5 w-3.5" />
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function RunTable({
  runs,
  agentMap,
  datasetMap,
}: {
  runs: EvalRun[];
  agentMap: Map<string, string>;
  datasetMap: Map<string, string>;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[820px] text-left">
        <thead>
          <tr className="border-b border-app-line bg-app-subtle text-[11px] uppercase tracking-wider text-app-muted">
            <th className="px-5 py-3 font-medium">运行</th>
            <th className="px-5 py-3 font-medium">状态</th>
            <th className="px-5 py-3 font-medium">通过</th>
            <th className="px-5 py-3 font-medium">得分</th>
            <th className="px-5 py-3 font-medium">耗时</th>
            <th className="px-5 py-3 font-medium">创建时间</th>
            <th className="px-5 py-3 font-medium" />
          </tr>
        </thead>
        <tbody className="divide-y divide-app-line">
          {runs.map((run) => {
            const meta = statusMeta(run.status);
            const agentName = agentMap.get(run.agent_id) ?? run.agent_id;
            const datasetName = datasetMap.get(run.dataset_id) ?? run.dataset_id;
            return (
              <tr key={run.id} className="text-sm hover:bg-app-subtle/60">
                <td className="px-5 py-4">
                  <p className="font-medium text-app-text">{agentName}</p>
                  <p className="mt-0.5 text-xs text-app-muted">{datasetName}</p>
                  <p className="mt-0.5 font-mono text-[10px] text-app-muted">{run.id}</p>
                </td>
                <td className="px-5 py-4">
                  <Badge tone={meta.tone}>{meta.label}</Badge>
                </td>
                <td className="px-5 py-4 text-app-text">
                  {run.passed_cases ?? 0} / {run.total_cases ?? 0}
                </td>
                <td className="px-5 py-4 font-medium text-app-text">
                  {formatPercent(run.score ?? 0, 1)}
                </td>
                <td className="px-5 py-4 text-xs text-app-muted">
                  {formatDuration(run.latency_ms)}
                </td>
                <td className="px-5 py-4 text-xs text-app-muted">{formatDate(run.created_at)}</td>
                <td className="px-5 py-4">
                  <Link
                    href={`/evaluations/runs/${run.id}`}
                    className="inline-flex items-center gap-1 text-xs font-medium text-brand hover:underline"
                  >
                    查看运行
                    <ArrowUpRight className="h-3.5 w-3.5" />
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
