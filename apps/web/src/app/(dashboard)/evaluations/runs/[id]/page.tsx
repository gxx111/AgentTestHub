"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { api } from "@/lib/api";
import { useResource } from "@/hooks/use-resource";
import type {
  ExecutionContext,
  ExperimentSummary,
  RunDetail,
  SampleResult,
} from "@/lib/types";
import { ReportView } from "@/components/evaluations/report-view";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { FullPageSpinner } from "@/components/ui/spinner";

export default function RunDetailPage() {
  const params = useParams<{ id: string }>();
  const run = useResource<RunDetail>(`run:${params.id}`, () => api.getRun(params.id));

  if (run.loading) return <FullPageSpinner label="正在加载运行报告…" />;

  if (run.error) {
    return (
      <div className="mx-auto max-w-lg py-20">
        <EmptyState
          title="运行加载失败"
          description={run.error}
          action={
            <div className="flex gap-2">
              <Link href="/evaluations">
                <Button variant="secondary" size="sm" icon={<ArrowLeft className="h-3.5 w-3.5" />}>
                  返回列表
                </Button>
              </Link>
              <Button size="sm" onClick={() => void run.refresh()}>
                重试
              </Button>
            </div>
          }
        />
      </div>
    );
  }

  const data = run.data;
  if (!data) return null;

  const samples: SampleResult[] = data.case_results ?? [];
  const passed = samples.filter((sample) => sample.result?.is_passed).length;
  const errors = samples.filter((sample) => sample.status === "error").length;
  const averages =
    samples.length > 0
      ? samples.reduce((sum, sample) => sum + (sample.result?.total_score ?? 0), 0) /
        samples.length
      : 0;
  const summary: ExperimentSummary = {
    ...data.summary,
    total_cases: data.summary.total_cases ?? samples.length,
    passed_cases: data.summary.passed_cases ?? passed,
    score: data.summary.score ?? (samples.length > 0 ? passed / samples.length : 0),
    average_score: data.summary.average_score ?? averages,
    error_count: data.summary.error_count ?? errors,
    repetitions:
      typeof data.summary.repetitions === "number" ? data.summary.repetitions : 1,
  };

  const snapshot = data.snapshot as
    | { execution?: ExecutionContext; agent_name?: string; dataset_name?: string }
    | null
    | undefined;
  const context = snapshot?.execution ?? null;
  const agentId = typeof data.agent_id === "string" ? data.agent_id : "Agent";
  const datasetId = typeof data.dataset_id === "string" ? data.dataset_id : "数据集";
  const agentName = summary.agent_name ?? snapshot?.agent_name ?? agentId;
  const datasetName = summary.dataset_name ?? snapshot?.dataset_name ?? datasetId;

  return (
    <ReportView
      title="运行报告"
      subtitle={`${agentName} · ${datasetName} · 单次运行`}
      status={data.status}
      createdAt={data.created_at}
      summary={summary}
      samples={samples}
      context={context}
      snapshotHash={data.snapshot_hash ?? undefined}
      raw={data}
      backHref="/evaluations"
    />
  );
}
