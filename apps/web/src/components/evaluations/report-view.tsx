"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  ArrowUpRight,
  CheckCircle2,
  Download,
  ShieldAlert,
  XCircle,
} from "lucide-react";
import type {
  CaseStability,
  ExecutionContext,
  ExperimentSummary,
  Judgment,
  SampleResult,
  Tone,
} from "@/lib/types";
import { formatDate, formatDuration, formatPercent, roleLabel, statusMeta } from "@/lib/format";
import { downloadJson } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Modal } from "@/components/ui/modal";
import { Progress } from "@/components/ui/progress";
import { ScoreRing } from "@/components/ui/score-ring";
import { TraceViewer } from "@/components/evaluations/trace-viewer";

interface ReportViewProps {
  title: string;
  subtitle?: string;
  status: string;
  createdAt?: string;
  summary: ExperimentSummary;
  samples: SampleResult[];
  caseStability?: CaseStability[];
  context?: ExecutionContext | null;
  snapshotHash?: string;
  raw?: unknown;
  backHref: string;
  backLabel?: string;
}

function verdictTone(verdict: string): Tone {
  if (verdict === "YES") return "success";
  if (verdict === "NO") return "danger";
  return "warning";
}

function decisionFor(
  passRate: number,
  errors: number,
  total: number,
  repetitions: number,
) {
  if (errors > 0 && passRate < 0.5) {
    return {
      label: "阻断发布",
      tone: "danger" as const,
      description: "存在执行错误或大面积失败，不能作为发布依据。",
    };
  }
  if (total < 5 || repetitions < 5) {
    return {
      label: "需复核",
      tone: "warning" as const,
      description:
        "样本量或重复次数不足（建议至少 5 个用例、5 次重复）。当前结果只能作为流程验证，不能作为发布依据。",
    };
  }
  if (passRate >= 0.95 && errors === 0) {
    return {
      label: "可发布",
      tone: "success" as const,
      description: "通过率达到门禁阈值，且没有执行错误。建议保留证据包供审计。",
    };
  }
  if (passRate >= 0.8) {
    return {
      label: "需复核",
      tone: "warning" as const,
      description: "通过率未达到 95%，或存在失败/错误样本，需要人工复核。",
    };
  }
  return {
    label: "阻断发布",
    tone: "danger" as const,
    description: "通过率低于可接受阈值，建议修复后重新评测。",
  };
}

function judgeTypeLabel(value: string | null | undefined): string {
  if (!value) return "—";
  if (value === "deterministic_heuristics") return "内置启发式评委";
  if (value === "configured_multi_agent") return "LLM 评测团队";
  return value;
}

export function ReportView({
  title,
  subtitle,
  status,
  createdAt,
  summary,
  samples,
  caseStability,
  context,
  snapshotHash,
  raw,
  backHref,
  backLabel = "返回评测实验",
}: ReportViewProps) {
  const router = useRouter();
  const [selectedSample, setSelectedSample] = useState<SampleResult | null>(null);

  const total = summary.total_cases ?? samples.length;
  const passed =
    summary.passed_cases ?? samples.filter((sample) => sample.result?.is_passed).length;
  const passRate =
    typeof summary.score === "number" ? summary.score : total > 0 ? passed / total : 0;
  const averageScore =
    typeof summary.average_score === "number"
      ? summary.average_score
      : samples.length > 0
        ? samples.reduce((sum, sample) => sum + (sample.result?.total_score ?? 0), 0) /
          samples.length
        : 0;
  const errors = summary.error_count ?? samples.filter((sample) => sample.status === "error").length;
  const flaky = summary.flaky_cases ?? caseStability?.filter((item) => item.flaky).length ?? 0;
  const repetitions = summary.repetitions ?? 1;
  const confidence =
    summary.pass_rate_statistics?.confidence_interval_95 ??
    summary.score_statistics?.confidence_interval_95 ??
    null;
  const decision = decisionFor(passRate, errors, total, repetitions);
  const statusInfo = statusMeta(status);
  const sampleLimited = total < 5 || repetitions < 5;

  const failures = useMemo(
    () =>
      samples.filter((sample) =>
        sample.result
          ? !sample.result.is_passed
          : sample.status === "error" || sample.status === "timeout",
      ),
    [samples],
  );

  const passingSamples = useMemo(
    () => samples.filter((sample) => sample.result?.is_passed),
    [samples],
  );

  const stableCases = useMemo(() => {
    const list = caseStability ?? [];
    return list.slice().sort((left, right) => left.pass_rate - right.pass_rate);
  }, [caseStability]);

  return (
    <div className="space-y-5">
      <div>
        <Link
          href={backHref}
          className="mb-4 inline-flex items-center gap-1.5 text-sm text-app-muted hover:text-app-text"
        >
          <ArrowLeft className="h-4 w-4" />
          {backLabel}
        </Link>

        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight text-app-text">{title}</h1>
              <Badge tone={statusInfo.tone}>{statusInfo.label}</Badge>
            </div>
            {subtitle && <p className="mt-1 text-sm text-app-muted">{subtitle}</p>}
            <p className="mt-1 text-xs text-app-muted">
              创建于 {formatDate(createdAt)}
              {snapshotHash && (
                <span className="ml-3 font-mono">快照 {snapshotHash.slice(0, 12)}…</span>
              )}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              size="sm"
              icon={<Download className="h-3.5 w-3.5" />}
              onClick={() =>
                downloadJson(raw ?? { summary, samples }, `agenttesthub-report-${Date.now()}.json`)
              }
            >
              导出 JSON
            </Button>
            <Button
              variant="primary"
              size="sm"
              icon={<ArrowUpRight className="h-3.5 w-3.5" />}
              onClick={() => router.push("/evaluations")}
            >
              新建评测
            </Button>
          </div>
        </div>
      </div>

      <section className="overflow-hidden rounded-2xl border border-app-line bg-app-surface">
        <div className="grid gap-6 p-6 lg:grid-cols-[auto_1fr_auto] lg:items-center">
          <ScoreRing value={passRate} tone={decision.tone} label="通过率" size={132} />
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg font-semibold text-app-text">{decision.label}</h2>
              {sampleLimited && <Badge tone="warning">样本不足</Badge>}
              {confidence && (
                <Badge tone="neutral">
                  95% CI {(confidence[0] * 100).toFixed(1)}% – {(confidence[1] * 100).toFixed(1)}%
                </Badge>
              )}
            </div>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-app-muted">{decision.description}</p>
            <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm">
              <span className="text-app-muted">
                通过 <strong className="text-app-text">{passed}</strong> / {total}
              </span>
              <span className="text-app-muted">
                错误 <strong className={errors > 0 ? "text-red-600" : "text-app-text"}>{errors}</strong>
              </span>
              <span className="text-app-muted">
                Flaky <strong className={flaky > 0 ? "text-amber-600" : "text-app-text"}>{flaky}</strong>
              </span>
              <span className="text-app-muted">
                重复 <strong className="text-app-text">{repetitions}</strong>
              </span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-2">
            <MiniMetric label="平均分" value={formatPercent(averageScore, 1)} />
            <MiniMetric label="用例数" value={String(total)} />
            <MiniMetric label="失败" value={String(failures.length)} tone={failures.length ? "danger" : "default"} />
            <MiniMetric label="置信区间" value={confidence ? "已计算" : "样本不足"} />
          </div>
        </div>
      </section>

      <div className="grid items-start gap-5 lg:grid-cols-[1.55fr_1fr]">
        <section className="rounded-2xl border border-app-line bg-app-surface">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-app-line px-5 py-4">
            <div>
              <h2 className="text-sm font-semibold text-app-text">失败与证据</h2>
              <p className="mt-0.5 text-xs text-app-muted">
                每个失败样本都保留评委理由、证据 Span 与执行 Trace。
              </p>
            </div>
            <Badge tone={failures.length ? "danger" : "success"}>
              {failures.length ? `${failures.length} 个失败/错误` : "没有失败样本"}
            </Badge>
          </div>

          {failures.length === 0 ? (
            <div className="p-5">
              <div className="flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50/70 p-4">
                <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-emerald-100 text-emerald-700">
                  <CheckCircle2 className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-emerald-900">本次评测没有失败样本</p>
                  <p className="mt-0.5 text-xs leading-5 text-emerald-800/80">
                    所有用例满足预期状态与 Rubric。仍建议检查样本量与置信区间后再做发布决策。
                  </p>
                </div>
              </div>

              {passingSamples.length > 0 && (
                <div className="mt-4">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-xs font-medium text-app-muted">通过样本</p>
                    <span className="text-[11px] text-app-muted">{passingSamples.length} 条</span>
                  </div>
                  <div className="divide-y divide-app-line rounded-xl border border-app-line">
                    {passingSamples.slice(0, 8).map((sample) => (
                      <div
                        key={sample.sample_id}
                        className="flex flex-wrap items-center justify-between gap-3 px-3 py-2.5"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-app-text">{sample.title}</p>
                          <p className="mt-0.5 text-[11px] text-app-muted">
                            第 {sample.repetition_index} 次 · 得分{" "}
                            {formatPercent(sample.result?.total_score ?? 0, 0)} ·{" "}
                            {formatDuration(sample.duration_ms)}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge tone="success">通过</Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            icon={<ArrowUpRight className="h-3.5 w-3.5" />}
                            onClick={() => setSelectedSample(sample)}
                          >
                            Trace
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="divide-y divide-app-line">
              {failures.map((sample) => (
                <FailureCard
                  key={sample.sample_id}
                  sample={sample}
                  onOpenTrace={() => setSelectedSample(sample)}
                />
              ))}
            </div>
          )}
        </section>

        <div className="space-y-5">
          <section className="rounded-2xl border border-app-line bg-app-surface">
            <div className="border-b border-app-line px-5 py-4">
              <h2 className="text-sm font-semibold text-app-text">Case 稳定性</h2>
              <p className="mt-0.5 text-xs text-app-muted">按通过率从低到高排序。</p>
            </div>
            {stableCases.length === 0 ? (
              <p className="px-5 py-8 text-center text-sm text-app-muted">
                没有稳定性数据（需要多次重复或聚合实验）。
              </p>
            ) : (
              <div className="divide-y divide-app-line">
                {stableCases.slice(0, 10).map((item) => (
                  <div key={item.case_id} className="px-5 py-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-app-text">{item.title}</p>
                        <p className="mt-0.5 text-[11px] text-app-muted">
                          {item.passed}/{item.attempts} 通过 · {formatPercent(item.pass_rate, 0)}
                        </p>
                      </div>
                      {item.flaky && <Badge tone="warning">flaky</Badge>}
                    </div>
                    <Progress
                      value={item.pass_rate}
                      tone={item.pass_rate >= 0.95 ? "success" : item.pass_rate >= 0.8 ? "warning" : "danger"}
                      className="mt-2"
                    />
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="rounded-2xl border border-app-line bg-app-surface">
            <div className="border-b border-app-line px-5 py-4">
              <h2 className="text-sm font-semibold text-app-text">实验上下文</h2>
              <p className="mt-0.5 text-xs text-app-muted">用于复现与审计的配置摘要。</p>
            </div>
            <dl className="space-y-3 px-5 py-4 text-sm">
              <ContextRow label="评委类型" value={judgeTypeLabel(context?.judge_type)} />
              <ContextRow
                label="评委角色"
                value={context?.judges?.length ? context.judges.map(roleLabel).join("、") : "—"}
              />
              <ContextRow
                label="红队"
                value={context?.red_team_applied ? "已启用" : "未启用"}
              />
              <ContextRow
                label="模型确定性"
                value={context?.model_determinism_guaranteed ? "已保证" : "概率性"}
              />
              <ContextRow label="重复次数" value={String(repetitions)} />
              {snapshotHash && (
                <div>
                  <dt className="text-xs text-app-muted">快照哈希</dt>
                  <dd className="mt-1 break-all font-mono text-[11px] text-app-text">
                    {snapshotHash}
                  </dd>
                </div>
              )}
            </dl>
          </section>
        </div>
      </div>

      <Modal
        open={Boolean(selectedSample)}
        onClose={() => setSelectedSample(null)}
        title={selectedSample ? `执行 Trace · ${selectedSample.title}` : "执行 Trace"}
        description="按时间顺序回放用户、Agent、工具、评委的完整事件。"
        size="xl"
      >
        {selectedSample?.result?.trace ? (
          <TraceViewer trace={selectedSample.result.trace} />
        ) : (
          <EmptyState
            title="没有 Trace 数据"
            description="该样本没有保存执行轨迹，可能运行失败或未启用 Trace 采集。"
          />
        )}
      </Modal>
    </div>
  );
}

function MiniMetric({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "danger";
}) {
  return (
    <div className="rounded-lg border border-app-line bg-app-subtle px-3 py-2">
      <p className="text-[11px] text-app-muted">{label}</p>
      <p
        className={
          tone === "danger"
            ? "mt-1 text-lg font-semibold text-red-600"
            : "mt-1 text-lg font-semibold text-app-text"
        }
      >
        {value}
      </p>
    </div>
  );
}

function ContextRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <dt className="shrink-0 text-xs text-app-muted">{label}</dt>
      <dd className="text-right text-xs font-medium text-app-text">{value}</dd>
    </div>
  );
}

function FailureCard({
  sample,
  onOpenTrace,
}: {
  sample: SampleResult;
  onOpenTrace: () => void;
}) {
  const result = sample.result;
  return (
    <article className="px-5 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold text-app-text">{sample.title}</h3>
            <Badge tone={sample.status === "error" ? "danger" : "warning"}>
              {sample.status === "error" ? "执行错误" : "未通过"}
            </Badge>
            <Badge tone="neutral">第 {sample.repetition_index} 次</Badge>
          </div>
          <p className="mt-1 font-mono text-[11px] text-app-muted">{sample.case_id}</p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          icon={<ArrowUpRight className="h-3.5 w-3.5" />}
          onClick={onOpenTrace}
        >
          查看 Trace
        </Button>
      </div>

      <p className="mt-3 line-clamp-3 rounded-lg bg-app-subtle px-3 py-2 text-sm leading-6 text-app-muted">
        {sample.prompt}
      </p>

      {sample.error && (
        <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{sample.error}</span>
        </div>
      )}

      {result?.execution_error && (
        <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
          <span>执行错误：{result.execution_error}</span>
        </div>
      )}

      {result && result.rubric_judgments.length > 0 && (
        <div className="mt-3 space-y-2">
          {result.rubric_judgments.map((judgment, index) => (
            <JudgmentRow key={`${judgment.rubric_id}-${judgment.judge_role}-${index}`} judgment={judgment} />
          ))}
        </div>
      )}

      {result?.attribution_tree && result.attribution_tree.length > 0 && (
        <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
          <p className="text-xs font-semibold text-amber-800">归因与建议</p>
          <ul className="mt-2 space-y-2">
            {result.attribution_tree.map((node) => (
              <li key={node.node_id} className="text-xs leading-5 text-amber-900">
                <span className="font-medium">{node.hop_stage}</span> · {node.failure_category}
                <br />
                {node.root_cause_explanation}
                <br />
                <span className="font-medium">建议：</span>
                {node.suggested_action}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-3 text-[11px] text-app-muted">
        <span>耗时 {formatDuration(sample.duration_ms)}</span>
        <span>Token {result?.total_tokens ?? "—"}</span>
        <span>状态断言 {result?.world_state_passed ? "通过" : "未通过"}</span>
        {result?.unknown_rubric_count ? <span>UNKNOWN {result.unknown_rubric_count}</span> : null}
      </div>
    </article>
  );
}

function JudgmentRow({ judgment }: { judgment: Judgment }) {
  return (
    <div className="rounded-lg border border-app-line px-3 py-2">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={verdictTone(judgment.verdict)}>{judgment.verdict}</Badge>
        <span className="font-mono text-[11px] text-app-text">{judgment.rubric_id}</span>
        <span className="text-[11px] text-app-muted">{judgment.judge_role}</span>
        <span className="text-[11px] text-app-muted">
          置信度 {formatPercent(judgment.confidence, 0)}
        </span>
      </div>
      <p className="mt-1 text-xs leading-5 text-app-muted">{judgment.rationale}</p>
      {judgment.evidence_span_ids.length > 0 && (
        <p className="mt-1 break-all font-mono text-[10px] text-app-muted">
          证据：{judgment.evidence_span_ids.join(", ")}
        </p>
      )}
    </div>
  );
}
