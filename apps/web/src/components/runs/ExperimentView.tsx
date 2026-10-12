"use client";

import { useEffect, useRef, useState } from "react";
import { Activity, ArrowUpRight, Download, FlaskConical, Play, RefreshCw, X } from "lucide-react";
import { AgentLiveBoard, type TraceEvent } from "./AgentLiveBoard";

type Api = (path: string, options?: RequestInit) => Promise<any>;
type Asset = { id: string; name: string; model_name?: string };
type LiveEvent = {
  event?: TraceEvent;
};
type Stats = {
  mean: number;
  sample_stddev: number | null;
  range: [number, number];
  confidence_interval_95: [number, number] | null;
};
type Stability = {
  case_id: string;
  title: string;
  attempts: number;
  passed: number;
  error_count: number;
  flaky: boolean;
  pass_rate: number;
  pass_rate_interval_95: [number, number] | null;
  scores: Stats;
};
type Sample = {
  sample_id: string;
  case_id: string;
  title: string;
  prompt: string;
  status: string;
  error: string | null;
  duration_ms: number;
  result: {
    is_passed: boolean;
    total_score: number;
    world_state_passed: boolean;
    rubric_judgments: { rubric_id: string; judge_role: string; verdict: string; rationale: string }[];
    trace: { events: TraceEvent[] } | null;
  } | null;
};
type ExperimentRun = {
  run_id: string;
  repetition_index: number;
  status: string;
  summary: { score: number; average_score: number; error_count: number };
  case_results: Sample[];
};
type Experiment = {
  id: string;
  agent_id: string;
  dataset_id: string;
  status: string;
  repetitions: number;
  created_at: string;
  snapshot_hash: string;
  snapshot?: unknown;
  summary: {
    agent_name?: string;
    dataset_name?: string;
    score?: number;
    average_score?: number;
    total_cases?: number;
    unique_cases?: number;
    error_count?: number;
    flaky_cases?: number;
    score_statistics?: Stats;
    case_stability?: Stability[];
    execution_context?: { mock_uses_expected_state: boolean; red_team_applied: boolean };
  };
  runs?: ExperimentRun[];
};

const percent = (value: number | undefined) => value === undefined ? "-" : `${(value * 100).toFixed(1)}%`;
const interval = (value: [number, number] | null | undefined) => value ? `${percent(value[0])} - ${percent(value[1])}` : "-";
const statusLabel = (value: string) => ({
  running: "执行中", completed: "完成", partial: "部分异常", failed: "执行失败",
}[value] || value);

function ExperimentReport({ id, api, onClose }: { id: string; api: Api; onClose: () => void }) {
  const [detail, setDetail] = useState<Experiment | null>(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"stability" | "samples" | "replay" | "audit">("stability");
  const [round, setRound] = useState(1);
  const [caseId, setCaseId] = useState("");
  const dialog = useRef<HTMLElement>(null);
  useEffect(() => {
    const controller = new AbortController();
    api(`/evaluations/experiments/${id}`, { signal: controller.signal })
      .then(setDetail)
      .catch((err) => { if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "加载报告失败"); });
    return () => controller.abort();
  }, [id, api]);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    dialog.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
      if (event.key !== "Tab") return;
      const controls = Array.from(dialog.current?.querySelectorAll<HTMLElement>("button, select, summary, a, [tabindex='0']") || []);
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog.current)) {
        event.preventDefault(); last?.focus();
      } else if (!event.shiftKey && (document.activeElement === last || document.activeElement === dialog.current)) {
        event.preventDefault(); first?.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = overflow;
      document.removeEventListener("keydown", onKey);
      previous?.focus();
    };
  }, [onClose]);
  const current = detail?.runs?.find((run) => run.repetition_index === round);
  const exportReport = () => {
    if (!detail) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(detail, null, 2)], { type: "application/json" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${detail.id}.json`;
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return <div className="modal-backdrop">
    <section className="modal experiment-dialog" role="dialog" aria-modal="true" aria-labelledby="experiment-title" ref={dialog} tabIndex={-1}>
      <div className="modal-head">
        <div><h2 id="experiment-title">实验报告</h2><span className="mono">{id}</span></div>
        <div className="report-actions">
          <button className="icon-button" title="导出 JSON 报告" aria-label="导出 JSON 报告" disabled={!detail} onClick={exportReport}><Download size={17} /></button>
          <button className="icon-button" title="关闭" aria-label="关闭报告" onClick={onClose}><X size={17} /></button>
        </div>
      </div>
      {error ? <div className="form-error" role="alert">{error}</div> : !detail ? <div className="boot-screen compact">正在加载实验...</div> : <>
        <div className="experiment-heading">
          <strong>{detail.summary.agent_name} <span className="muted">/</span> {detail.summary.dataset_name}</strong>
          <span className={`status ${detail.status === "completed" ? "success" : "warning"}`}>{statusLabel(detail.status)}</span>
        </div>
        {detail.summary.execution_context?.mock_uses_expected_state && <div className="experiment-notice">Mock 流程验证 · 使用预期终态生成工具动作 · 不代表真实 Agent 能力</div>}
        <dl className="experiment-metrics">
          <div><dt>平均通过率</dt><dd>{percent(detail.summary.score)}</dd></div>
          <div><dt>平均得分</dt><dd>{percent(detail.summary.average_score)}</dd></div>
          <div><dt>重复轮次</dt><dd>{detail.runs?.length || 0} / {detail.repetitions}</dd></div>
          <div><dt>执行异常</dt><dd>{detail.summary.error_count ?? "-"}</dd></div>
        </dl>
        <div className="report-tabs" role="tablist" aria-label="报告视图">
          {([{ id: "stability", label: "稳定性" }, { id: "samples", label: "逐轮结果" }, { id: "replay", label: "协作回放" }, { id: "audit", label: "配置审计" }] as const).map((item) =>
            <button key={item.id} role="tab" aria-selected={tab === item.id} aria-controls={`report-${item.id}`} id={`tab-${item.id}`} className={tab === item.id ? "active" : ""} onClick={() => setTab(item.id)}>{item.label}</button>
          )}
        </div>
        <div className="experiment-report-body" role="tabpanel" id={`report-${tab}`} aria-labelledby={`tab-${tab}`}>
          {tab === "stability" && <>
            <dl className="stability-facts">
              <div><dt>得分标准差</dt><dd>{detail.summary.score_statistics?.sample_stddev == null ? "-" : percent(detail.summary.score_statistics.sample_stddev)}</dd></div>
              <div><dt>得分范围</dt><dd>{interval(detail.summary.score_statistics?.range)}</dd></div>
              <div><dt>均分 95% Bootstrap 区间</dt><dd>{detail.summary.score_statistics?.confidence_interval_95 ? interval(detail.summary.score_statistics.confidence_interval_95) : "样本不足（n < 5）"}</dd></div>
              <div><dt>波动用例</dt><dd>{detail.summary.flaky_cases ?? "-"} / {detail.summary.unique_cases ?? "-"}</dd></div>
            </dl>
            <div className="table-wrap">
              <table><thead><tr><th>用例</th><th>通过 / 执行</th><th>通过率 95% Wilson 区间</th><th>均分</th><th>异常</th><th>状态</th><th /></tr></thead>
                <tbody>{detail.summary.case_stability?.map((item) => <tr key={item.case_id}>
                  <td className="case-title-cell">{item.title}</td><td>{item.passed} / {item.attempts}</td>
                  <td>{interval(item.pass_rate_interval_95)}</td><td>{percent(item.scores.mean)}</td><td>{item.error_count}</td>
                  <td><span className={`status ${item.flaky || item.error_count ? "warning" : "success"}`}>{item.error_count ? "含异常" : item.flaky ? "结果波动" : item.attempts === 1 ? "单轮" : "观察一致"}</span></td>
                  <td><button className="icon-button" title={`查看 ${item.title} 的逐轮结果`} aria-label={`查看 ${item.title} 的逐轮结果`} onClick={() => { setCaseId(item.case_id); setTab("samples"); }}><ArrowUpRight size={15} /></button></td>
                </tr>)}</tbody>
              </table>
            </div>
            <p className="statistics-note">区间基于固定用例集的重复采样，假设各轮独立。小样本或零观测波动不等于确定性；不估计新任务的泛化能力。异常以 0 分保留在分母。</p>
          </>}
          {tab === "samples" && <>
            <div className="sample-filters">
              <label>轮次<select value={round} onChange={(event) => setRound(Number(event.target.value))}>{detail.runs?.map((run) => <option key={run.run_id} value={run.repetition_index}>第 {run.repetition_index} 轮 · {statusLabel(run.status)} · 通过率 {percent(run.summary.score)}</option>)}</select></label>
              <label>用例<select value={caseId} onChange={(event) => setCaseId(event.target.value)}><option value="">全部用例</option>{detail.summary.case_stability?.map((item) => <option key={item.case_id} value={item.case_id}>{item.title}</option>)}</select></label>
            </div>
            <div className="report-cases">
              {current?.case_results.filter((sample) => !caseId || sample.case_id === caseId).map((sample) => <article className="experiment-sample" key={sample.sample_id}>
                <div className="case-item-head"><strong>{sample.title}</strong><span className={`status ${sample.result?.is_passed ? "success" : "warning"}`}>{sample.status === "error" ? "执行异常" : sample.result?.is_passed ? "通过" : "未通过"}</span></div>
                <p>{sample.prompt}</p>
                <div className="report-facts">
                  <span>得分 {percent(sample.result?.total_score ?? 0)}</span><span>耗时 {sample.duration_ms.toFixed(0)} ms</span>
                  <span>状态断言 {sample.result ? sample.result.world_state_passed ? "通过" : "未通过" : "未完成"}</span>
                  <span>{sample.result?.trace?.events.length || 0} 条 Trace 事件</span>
                </div>
                {sample.error && <div className="form-error">执行异常：{sample.error}</div>}
                {sample.result?.rubric_judgments.map((judgment, index) => <div className="judgment" key={`${judgment.rubric_id}-${index}`}><b>{judgment.rubric_id}</b><span>{judgment.judge_role} · {judgment.verdict}</span><p>{judgment.rationale}</p></div>)}
                <details><summary>执行 Trace</summary><pre>{JSON.stringify(sample.result?.trace?.events || [], null, 2)}</pre></details>
              </article>)}
            </div>
          </>}
          {tab === "replay" && <div className="replay-view">
            <div className="sample-filters">
              <label>轮次<select value={round} onChange={(event) => setRound(Number(event.target.value))}>{detail.runs?.map((run) => <option key={run.run_id} value={run.repetition_index}>第 {run.repetition_index} 轮</option>)}</select></label>
              <label>用例<select value={caseId} onChange={(event) => setCaseId(event.target.value)}><option value="">首个用例</option>{detail.summary.case_stability?.map((item) => <option key={item.case_id} value={item.case_id}>{item.title}</option>)}</select></label>
            </div>
            {(() => {
              const candidates = current?.case_results || [];
              const sample = candidates.find((item) => item.case_id === caseId) || candidates[0];
              const sourceAgent = detail.snapshot as { agent?: { name?: string; model_name?: string } } | undefined;
              return <AgentLiveBoard
                running={false}
                events={sample?.result?.trace?.events || []}
                agentName={sourceAgent?.agent?.name || detail.summary.agent_name}
                modelName={sourceAgent?.agent?.model_name || "model"}
              />;
            })()}
          </div>}
          {tab === "audit" && <div className="audit-view">
            <dl><dt>配置 SHA-256</dt><dd className="mono">{detail.snapshot_hash}</dd><dt>裁决器</dt><dd>RuleJudge / SafetyJudge（规则启发式）</dd><dt>动态红队</dt><dd>本实验执行链未启用</dd><dt>运行输入</dt><dd>Agent、数据集、用例与策略已冻结；凭据已脱敏</dd></dl>
            <pre>{JSON.stringify(detail.snapshot, null, 2)}</pre>
          </div>}
        </div>
      </>}
    </section>
  </div>;
}

export function ExperimentView({ workspaceId, agents, datasets, api, onRefresh }: {
  workspaceId: string; agents: Asset[]; datasets: Asset[]; api: Api; onRefresh: () => void;
}) {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [agentId, setAgentId] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [repetitions, setRepetitions] = useState("3");
  const [running, setRunning] = useState(false);
  const [liveEvents, setLiveEvents] = useState<TraceEvent[]>([]);
  const [streamId, setStreamId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState("");
  const mounted = useRef(true);
  const reload = async () => {
    setLoading(true);
    try { const data = await api(`/evaluations/experiments?workspace_id=${encodeURIComponent(workspaceId)}`); if (mounted.current) setExperiments(data); }
    catch (err) { if (mounted.current) setError(err instanceof Error ? err.message : "加载失败"); }
    finally { if (mounted.current) setLoading(false); }
  };
  useEffect(() => {
    mounted.current = true;
    reload();
    return () => { mounted.current = false; };
    // workspace changes remount this view in the host page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId]);
  useEffect(() => { setAgentId((current) => agents.some((item) => item.id === current) ? current : agents[0]?.id || ""); }, [agents]);
  useEffect(() => { setDatasetId((current) => datasets.some((item) => item.id === current) ? current : datasets[0]?.id || ""); }, [datasets]);
  const count = Number(repetitions);
  const valid = Number.isInteger(count) && count >= 1 && count <= 20;
  const launch = async () => {
    if (!valid || !agentId || !datasetId || running) return;
    const nextStreamId = `stream_${crypto.randomUUID().replaceAll("-", "").slice(0, 24)}`;
    setError(""); setRunning(true); setLiveEvents([]); setStreamId(nextStreamId);
    const poller = window.setInterval(async () => {
      try {
        const stream = await api(`/evaluations/streams/${nextStreamId}`);
        setLiveEvents((stream.events || []).map((item: LiveEvent) => item.event).filter((event: TraceEvent | undefined): event is TraceEvent => Boolean(event)));
      } catch {
        // The run request owns the final error state; a transient poll failure is harmless.
      }
    }, 420);
    try {
      const result = await api("/evaluations/universal-run", {
        method: "POST",
        body: JSON.stringify({ workspace_id: workspaceId, agent_id: agentId, dataset_id: datasetId, repetitions: count, stream_id: nextStreamId }),
      });
      if (mounted.current) {
        const stream = await api(`/evaluations/streams/${nextStreamId}`).catch(() => null);
        if (stream) setLiveEvents((stream.events || []).map((item: LiveEvent) => item.event).filter((event: TraceEvent | undefined): event is TraceEvent => Boolean(event)));
        await reload();
        onRefresh();
        setSelected(result.experiment_id);
      }
    } catch (err) { if (mounted.current) setError(err instanceof Error ? err.message : "执行失败"); }
    finally {
      window.clearInterval(poller);
      if (mounted.current) setRunning(false);
    }
  };
  return <div className="page-content">
    <div className="page-heading"><div><p className="eyebrow">Evaluation / Experiments</p><h1>评测实验</h1></div>
      <button className="icon-button" title="刷新实验" aria-label="刷新实验" disabled={loading} onClick={reload}><RefreshCw size={17} className={loading ? "spin" : ""} /></button>
    </div>
    <section className="experiment-launch">
      <div className="launch-copy"><div className="launch-icon"><FlaskConical size={20} /></div><h2>新建实验</h2></div>
      <div className="launch-controls experiment-controls">
        <label>被测 Agent<select value={agentId} disabled={running} onChange={(event) => setAgentId(event.target.value)}>{!agents.length && <option value="">暂无 Agent</option>}{agents.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label>评测数据集<select value={datasetId} disabled={running} onChange={(event) => setDatasetId(event.target.value)}>{!datasets.length && <option value="">暂无数据集</option>}{datasets.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label>重复次数<input type="number" min={1} max={20} step={1} value={repetitions} disabled={running} onChange={(event) => setRepetitions(event.target.value)} aria-invalid={!valid} /></label>
        <button className="primary-button" disabled={running || !agentId || !datasetId || !valid} onClick={launch}>{running ? <Activity size={15} className="spin" /> : <Play size={15} />}{running ? "执行中..." : "启动实验"}</button>
      </div>
      {!valid && <div className="form-error" role="alert">重复次数须为 1 至 20 的整数。</div>}
      {running && <p className="muted" role="status">正在执行 {count} 轮独立评测...</p>}
    </section>
    {error && <div className="form-error page-error" role="alert">{error}</div>}
    {(running || liveEvents.length > 0) && <AgentLiveBoard
      running={running}
      events={liveEvents}
      agentName={agents.find((item) => item.id === agentId)?.name}
      modelName={agents.find((item) => item.id === agentId)?.model_name}
    />}
    <section className="experiment-history"><div className="panel-header"><h2>实验历史</h2><span className="muted">{experiments.length} 个实验</span></div>
      <div className="table-wrap"><table><thead><tr><th>实验 / 时间</th><th>目标 Agent / 数据集</th><th>轮次</th><th>通过率</th><th>均分 / 标准差</th><th>状态</th><th /></tr></thead><tbody>
        {experiments.length ? experiments.map((item) => <tr key={item.id}>
          <td><span className="mono">{item.id}</span><small className="table-secondary">{new Date(item.created_at).toLocaleString("zh-CN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</small></td>
          <td>{item.summary.agent_name || item.agent_id}<small className="table-secondary">{item.summary.dataset_name || item.dataset_id}</small></td>
          <td>{item.repetitions}</td><td>{percent(item.summary.score)}</td>
          <td>{percent(item.summary.average_score)} / {item.summary.score_statistics?.sample_stddev == null ? "-" : percent(item.summary.score_statistics.sample_stddev)}</td>
          <td><span className={`status ${item.status === "completed" ? "success" : "warning"}`}>{statusLabel(item.status)}</span></td>
          <td><button className="icon-button" title={`查看实验 ${item.id}`} aria-label={`查看实验 ${item.id}`} onClick={() => setSelected(item.id)}><ArrowUpRight size={15} /></button></td>
        </tr>) : <tr><td colSpan={7}><div className="table-empty">{loading ? "正在加载..." : "暂无实验记录"}</div></td></tr>}
      </tbody></table></div>
    </section>
    {selected && <ExperimentReport id={selected} api={api} onClose={() => setSelected("")} />}
  </div>;
}
