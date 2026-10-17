"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { api } from "@/lib/api";
import { useResource } from "@/hooks/use-resource";
import type { ExperimentDetail } from "@/lib/types";
import { ReportView } from "@/components/evaluations/report-view";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { FullPageSpinner } from "@/components/ui/spinner";

export default function ExperimentDetailPage() {
  const params = useParams<{ id: string }>();
  const experiment = useResource<ExperimentDetail>(
    `experiment:${params.id}`,
    () => api.getExperiment(params.id),
  );

  if (experiment.loading) return <FullPageSpinner label="正在加载实验报告…" />;

  if (experiment.error) {
    return (
      <div className="mx-auto max-w-lg py-20">
        <EmptyState
          title="实验加载失败"
          description={experiment.error}
          action={
            <div className="flex gap-2">
              <Link href="/evaluations">
                <Button variant="secondary" size="sm" icon={<ArrowLeft className="h-3.5 w-3.5" />}>
                  返回列表
                </Button>
              </Link>
              <Button size="sm" onClick={() => void experiment.refresh()}>
                重试
              </Button>
            </div>
          }
        />
      </div>
    );
  }

  const data = experiment.data;
  if (!data) return null;

  const samples = data.runs.flatMap((run) => run.case_results ?? []);
  const summary = data.summary;
  const agentName = summary.agent_name ?? data.agent_id;
  const datasetName = summary.dataset_name ?? data.dataset_id;

  return (
    <ReportView
      title="实验报告"
      subtitle={`${agentName} · ${datasetName} · ${data.repetitions} 次重复`}
      status={data.status}
      createdAt={data.created_at}
      summary={summary}
      samples={samples}
      caseStability={summary.case_stability}
      context={summary.execution_context}
      snapshotHash={data.snapshot_hash}
      raw={data}
      backHref="/evaluations"
    />
  );
}
