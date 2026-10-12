"use client";

import { useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import {
  Activity,
  ArrowUpRight,
  Bot,
  Check,
  ChevronDown,
  CircleHelp,
  Database,
  FlaskConical,
  LayoutDashboard,
  LogOut,
  Menu,
  Plus,
  Play,
  Settings2,
  ShieldCheck,
  Sparkles,
  Trash2,
  Users,
  X,
} from "lucide-react";
import { ExperimentView } from "../components/runs/ExperimentView";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005/api/v1";

type User = { id: string; email: string; name: string; role: string };
type Workspace = { id: string; name: string; member_role?: string };
type Agent = { id: string; name: string; agent_type: string; model_name: string; description?: string; config?: Record<string, unknown> };
type Dataset = { id: string; name: string; domain: string; description?: string; case_count?: number };
type TestCase = { id: string; title: string; category: string; prompt: string; description?: string; rubrics?: any[]; expected_state?: any[] };
type Run = {
  id: string;
  status: string;
  created_at: string;
  summary: {
    agent_name?: string;
    dataset_name?: string;
    score?: number;
    passed_cases?: number;
    total_cases?: number;
  };
};
type View = "overview" | "runs" | "experiments" | "agents" | "datasets";

async function api(path: string, options: RequestInit = {}) {
  const token = typeof window !== "undefined" ? localStorage.getItem("ath_token") : null;
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.error || "请求失败");
  return data;
}

function formatDate(value?: string) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("zh-CN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

function AuthScreen({ onAuthenticated }: { onAuthenticated: (data: any) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const data = await api(`/auth/${mode}`, { method: "POST", body: JSON.stringify({ email, password, name: mode === "register" ? name : undefined }) });
      localStorage.setItem("ath_token", data.token);
      onAuthenticated(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "无法完成操作");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="auth-shell">
      <section className="auth-intro">
        <div className="brand-mark"><Sparkles size={18} /></div>
        <p className="eyebrow">Agent evaluation operations</p>
        <h1>把 Agent 质量，变成可重复的工程流程。</h1>
        <p className="auth-copy">为测试团队统一管理被测 Agent、场景数据、考官策略与可审计的运行结果。</p>
        <div className="auth-proof"><ShieldCheck size={17} /><span>状态化沙盒 · 逐条 Trace · 多维质量门禁</span></div>
      </section>
      <section className="auth-card">
        <div className="auth-tabs">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>登录</button>
          <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>创建账号</button>
        </div>
        <h2>{mode === "login" ? "欢迎回来" : "创建你的工作区"}</h2>
        <p className="muted">{mode === "login" ? "进入团队评测控制台" : "注册后会自动创建一个私有工作区"}</p>
        <form onSubmit={submit} className="form-stack">
          {mode === "register" && <label>你的名字<input value={name} onChange={(e) => setName(e.target.value)} placeholder="例如：林工" required /></label>}
          <label>工作邮箱<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@company.com" required /></label>
          <label>密码<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="至少 8 个字符" minLength={8} required /></label>
          {error && <div className="form-error">{error}</div>}
          <button className="primary-button wide" disabled={busy}>{busy ? "处理中..." : mode === "login" ? "进入控制台" : "创建工作区"}<ArrowUpRight size={16} /></button>
        </form>
        <p className="form-note">本地开发环境 · 数据保存在当前服务端数据库</p>
      </section>
    </main>
  );
}

function StatCard({ label, value, note, tone = "cyan" }: { label: string; value: string; note: string; tone?: string }) {
  return <div className={`stat-card ${tone}`}><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-note">{note}</div></div>;
}

function Dimension({ name, score, color }: { name: string; score: number; color: string }) {
  return <div className="dimension"><div className="dimension-head"><span>{name}</span><strong>{score}%</strong></div><div className="progress"><span className={color} style={{ width: `${score}%` }} /></div></div>;
}

function RunTable({ runs, onOpen }: { runs: Run[]; onOpen: (run: Run) => void }) {
  return <div className="table-wrap"><table><thead><tr><th>运行</th><th>目标 Agent</th><th>数据集</th><th>结果</th><th>时间</th><th /></tr></thead><tbody>{runs.length ? runs.map((run) => <tr key={run.id} className="click-row" onClick={() => onOpen(run)}><td><span className="run-id">{run.id.slice(0, 16)}</span></td><td>{run.summary.agent_name || "-"}</td><td>{run.summary.dataset_name || "-"}</td><td><span className={`status ${run.status === "completed" ? "success" : "warning"}`}>{run.status === "completed" ? `${Math.round(Number(run.summary.score || 0) * 100)}% 通过` : run.status}</span></td><td className="muted">{formatDate(run.created_at)}</td><td><ArrowUpRight size={14} className="muted" /></td></tr>) : <tr><td colSpan={6}><div className="table-empty">还没有运行记录</div></td></tr>}</tbody></table></div>;
}

function Overview({ runs, agents, datasets, onNavigate, onOpenRun }: { runs: Run[]; agents: Agent[]; datasets: Dataset[]; onNavigate: (view: View) => void; onOpenRun: (run: Run) => void }) {
  const completed = runs.filter((run) => run.status === "completed");
  const score = completed.length ? completed.reduce((sum, run) => sum + Number(run.summary.score || 0), 0) / completed.length : 0;
  const totalCases = completed.reduce((sum, run) => sum + Number(run.summary.total_cases || 0), 0);
  const passedCases = completed.reduce((sum, run) => sum + Number(run.summary.passed_cases || 0), 0);
  return <div className="page-content">
    <div className="page-heading"><div><p className="eyebrow">Workspace overview</p><h1>质量控制台</h1><p className="muted">从资产准备到评测裁决，所有质量信号在这里汇总。</p></div><button className="primary-button" onClick={() => onNavigate("runs")}><Play size={15} /> 发起评测</button></div>
    <div className="stat-grid"><StatCard label="平均通过率" value={`${Math.round(score * 100)}%`} note={completed.length ? `${completed.length} 次运行的平均结果` : "等待第一次运行"} /><StatCard label="执行用例" value={String(totalCases)} note={`${passedCases} 条通过`} tone="green" /><StatCard label="被测 Agent" value={String(agents.length)} note="已接入工作区资产" tone="violet" /><StatCard label="评测数据集" value={String(datasets.length)} note="可复用场景集合" tone="amber" /></div>
    <div className="content-grid">
      <section className="panel chart-panel"><div className="panel-header"><div><h2>质量趋势</h2><p className="muted">最近运行的综合通过率</p></div><span className="panel-icon"><Activity size={16} /></span></div><div className="quality-chart">{completed.length ? completed.slice(0, 8).reverse().map((run, index) => <div className="chart-bar-wrap" key={run.id}><div className="chart-bar" style={{ height: `${Math.max(12, Number(run.summary.score || 0) * 100)}%` }}><span>{Math.round(Number(run.summary.score || 0) * 100)}%</span></div><small>{index + 1}</small></div>) : <div className="empty-state"><FlaskConical size={24} /><span>完成第一次评测后，这里会出现质量趋势</span></div>}</div></section>
      <section className="panel"><div className="panel-header"><div><h2>评测信号</h2><p className="muted">本项目支持的评测维度</p></div><CircleHelp size={16} className="muted" /></div><div className="signal-list"><span><Check size={14} />Rubric 二元裁决与陪审团争议</span><span><Check size={14} />沙盒世界状态与工具调用</span><span><Check size={14} />红队安全边界与提示注入</span><span><Check size={14} />逐轮 Trace 与失败归因</span></div></section>
    </div>
    <section className="panel recent-panel"><div className="panel-header"><div><h2>最近运行</h2><p className="muted">可追溯的运行记录和结果摘要</p></div><button className="text-button" onClick={() => onNavigate("runs")}>查看全部 <ArrowUpRight size={14} /></button></div><RunTable runs={runs.slice(0, 5)} onOpen={onOpenRun} /></section>
  </div>;
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  return <div className="modal-backdrop"><section className="modal"><div className="modal-head"><h2>{title}</h2><button className="icon-button" onClick={onClose} title="关闭"><X size={17} /></button></div>{children}</section></div>;
}

function AgentsPage({ agents, onRefresh }: { agents: Agent[]; onRefresh: () => void }) {
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Agent | null>(null);
  const [form, setForm] = useState({ name: "", model_name: "Qwen/Qwen2.5-0.5B-Instruct", agent_type: "litellm", description: "", api_base: "", api_key: "", webhook_url: "" });
  const [error, setError] = useState("");
  const start = (agent?: Agent) => { const config = agent?.config || {}; setEditing(agent || null); setForm(agent ? { name: agent.name, model_name: agent.model_name, agent_type: agent.agent_type, description: agent.description || "", api_base: String(config.api_base || ""), api_key: "", webhook_url: String(config.webhook_url || "") } : { name: "", model_name: "Qwen/Qwen2.5-0.5B-Instruct", agent_type: "litellm", description: "", api_base: "http://127.0.0.1:11434", api_key: "", webhook_url: "" }); setError(""); setOpen(true); };
  const save = async () => { try { const config = form.agent_type === "webhook" ? { webhook_url: form.webhook_url } : { api_base: form.api_base || null, ...(form.api_key ? { api_key: form.api_key } : {}) }; const payload = { name: form.name, model_name: form.model_name, agent_type: form.agent_type, description: form.description, workspace_id: localStorage.getItem("ath_workspace") || "ws_primary", config }; await api(editing ? `/agents/${editing.id}` : "/agents", { method: editing ? "PUT" : "POST", body: JSON.stringify(payload) }); setOpen(false); onRefresh(); } catch (err) { setError(err instanceof Error ? err.message : "保存失败"); } };
  const remove = async (id: string) => { if (!window.confirm("确认删除这个 Agent 资产？")) return; try { await api(`/agents/${id}`, { method: "DELETE" }); onRefresh(); } catch (err) { setError(err instanceof Error ? err.message : "删除失败"); } };
  return <div className="page-content"><div className="page-heading"><div><p className="eyebrow">Assets / Agents</p><h1>被测 Agent</h1><p className="muted">连接开源模型、Multi-Agent 团队或外部 Webhook，作为可复用测试目标。</p></div><button className="primary-button" onClick={() => start()}><Plus size={15} /> 添加 Agent</button></div><div className="asset-grid">{agents.map((agent) => <article className="asset-card" key={agent.id}><div className="asset-card-top"><div className="asset-avatar"><Bot size={18} /></div><button className="icon-button" onClick={() => remove(agent.id)} title="删除"><Trash2 size={15} /></button></div><h3>{agent.name}</h3><p className="muted clamp">{agent.description || "尚未添加描述"}</p><div className="tag-row"><span className="tag">{agent.agent_type}</span><span className="tag">{agent.model_name}</span></div><div className="asset-footer"><span className="muted mono">{agent.id.slice(0, 15)}</span><button className="text-button" onClick={() => start(agent)}>编辑 <Settings2 size={13} /></button></div></article>)}</div>{open && <Modal title={editing ? "编辑 Agent" : "添加 Agent"} onClose={() => setOpen(false)}><div className="form-stack"><label>名称<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="例如：Qwen 本地客服 Agent" /></label><label>接入类型<select value={form.agent_type} onChange={(e) => setForm({ ...form, agent_type: e.target.value })}><option value="litellm">开源模型 / LiteLLM</option><option value="mas_team">Multi-Agent 团队</option><option value="webhook">Webhook</option><option value="mock">本地 Mock（仅流程验证）</option></select></label><label>模型 / 版本<input value={form.model_name} onChange={(e) => setForm({ ...form, model_name: e.target.value })} placeholder="例如：Qwen/Qwen2.5-0.5B-Instruct" /></label>{form.agent_type === "litellm" && <><label>OpenAI 兼容 API Base<input value={form.api_base} onChange={(e) => setForm({ ...form, api_base: e.target.value })} placeholder="例如：http://127.0.0.1:11434" /></label><label>API Key（可选）<input type="password" value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} placeholder={editing ? "已配置则留空以保留" : "本地服务通常无需填写"} /></label></>}{form.agent_type === "webhook" && <label>Webhook URL<input value={form.webhook_url} onChange={(e) => setForm({ ...form, webhook_url: e.target.value })} placeholder="http://127.0.0.1:8000/agent" /></label>}<label>描述<textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} placeholder="这个 Agent 负责什么任务？" /></label>{error && <div className="form-error">{error}</div>}<button className="primary-button wide" onClick={save}><Check size={15} /> 保存资产</button></div></Modal>}</div>;
}

function DatasetsPage({ datasets, onRefresh }: { datasets: Dataset[]; onRefresh: () => void }) {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<Dataset | null>(null);
  const [cases, setCases] = useState<TestCase[]>([]);
  const [caseOpen, setCaseOpen] = useState(false);
  const [editingCase, setEditingCase] = useState<TestCase | null>(null);
  const [caseForm, setCaseForm] = useState({ title: "", category: "happy_path", prompt: "", description: "" });
  const [form, setForm] = useState({ name: "", domain: "general", description: "" });
  const [error, setError] = useState("");
  const openDataset = async (dataset: Dataset) => { setSelected(dataset); setError(""); try { const detail = await api(`/datasets/${dataset.id}`); setCases(detail.cases || []); } catch (err) { setError(err instanceof Error ? err.message : "无法加载用例"); } };
  const startCase = (testCase?: TestCase) => { setEditingCase(testCase || null); setCaseForm(testCase ? { title: testCase.title, category: testCase.category, prompt: testCase.prompt, description: testCase.description || "" } : { title: "", category: "happy_path", prompt: "", description: "" }); setCaseOpen(true); };
  const saveCase = async () => { if (!selected) return; try { const payload = { ...caseForm, expected_state: editingCase?.expected_state || [], rubrics: editingCase?.rubrics || [] }; if (editingCase) await api(`/cases/${editingCase.id}`, { method: "PUT", body: JSON.stringify(payload) }); else await api(`/datasets/${selected.id}/cases`, { method: "POST", body: JSON.stringify(payload) }); setCaseOpen(false); await openDataset(selected); onRefresh(); } catch (err) { setError(err instanceof Error ? err.message : "用例保存失败"); } };
  const deleteCase = async (testCase: TestCase) => { if (!window.confirm(`删除用例“${testCase.title}”？`)) return; try { await api(`/cases/${testCase.id}`, { method: "DELETE" }); if (selected) await openDataset(selected); onRefresh(); } catch (err) { setError(err instanceof Error ? err.message : "删除失败"); } };
  const save = async () => { try { await api("/datasets", { method: "POST", body: JSON.stringify({ ...form, workspace_id: localStorage.getItem("ath_workspace") || "ws_primary" }) }); setOpen(false); setForm({ name: "", domain: "general", description: "" }); onRefresh(); } catch (err) { setError(err instanceof Error ? err.message : "创建失败"); } };
  return <div className="page-content"><div className="page-heading"><div><p className="eyebrow">Assets / Datasets</p><h1>评测数据集</h1><p className="muted">将真实业务任务、边界攻击和世界状态断言组织成可复用的测试集。</p></div><button className="primary-button" onClick={() => setOpen(true)}><Plus size={15} /> 创建数据集</button></div>{error && <div className="form-error page-error">{error}</div>}<div className="dataset-layout"><div className="dataset-list">{datasets.map((dataset) => <button className={`dataset-row dataset-select ${selected?.id === dataset.id ? "selected" : ""}`} key={dataset.id} onClick={() => openDataset(dataset)}><div className="dataset-icon"><Database size={18} /></div><div className="dataset-main"><div className="dataset-title"><h3>{dataset.name}</h3><span className="tag">{dataset.domain}</span></div><p className="muted clamp">{dataset.description || "尚未添加描述"}</p><div className="dataset-meta"><span>{dataset.case_count || 0} 个测试用例</span><span>·</span><span className="mono">{dataset.id}</span></div></div><ArrowUpRight size={15} className="muted" /></button>)}</div>{selected && <section className="panel case-panel"><div className="panel-header"><div><h2>{selected.name}</h2><p className="muted">{cases.length} 个测试用例 · {selected.domain}</p></div><button className="primary-button" onClick={() => startCase()}><Plus size={14} /> 添加用例</button></div><div className="case-list">{cases.map((testCase) => <article className="case-item" key={testCase.id}><div className="case-item-head"><div><strong>{testCase.title}</strong><span className="tag">{testCase.category}</span></div><div className="case-actions"><button className="icon-button" onClick={() => startCase(testCase)} title="编辑用例"><Settings2 size={14} /></button><button className="icon-button" onClick={() => deleteCase(testCase)} title="删除用例"><Trash2 size={14} /></button></div></div><p>{testCase.prompt}</p><small className="muted">{testCase.description || "无描述"} · {testCase.rubrics?.length || 0} 条 Rubric</small></article>)}</div></section>}</div>{open && <Modal title="创建评测数据集" onClose={() => setOpen(false)}><div className="form-stack"><label>数据集名称<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="例如：客服退款安全回归集" /></label><label>业务域<select value={form.domain} onChange={(e) => setForm({ ...form, domain: e.target.value })}><option value="general">通用</option><option value="ecommerce">电商</option><option value="coding">代码</option><option value="finance">金融</option><option value="security">安全</option></select></label><label>描述<textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} placeholder="覆盖什么能力与风险？" /></label>{error && <div className="form-error">{error}</div>}<button className="primary-button wide" onClick={save}><Check size={15} /> 创建数据集</button></div></Modal>}{caseOpen && <Modal title={editingCase ? "编辑测试用例" : "添加测试用例"} onClose={() => setCaseOpen(false)}><div className="form-stack"><label>用例标题<input value={caseForm.title} onChange={(e) => setCaseForm({ ...caseForm, title: e.target.value })} /></label><label>类别<select value={caseForm.category} onChange={(e) => setCaseForm({ ...caseForm, category: e.target.value })}><option value="happy_path">标准流程</option><option value="edge_case">边界条件</option><option value="security_redline">安全红线</option><option value="sop_compliance">SOP 遵循</option><option value="mas_deadlock">多 Agent 协作</option></select></label><label>用户输入 / 初始任务<textarea rows={4} value={caseForm.prompt} onChange={(e) => setCaseForm({ ...caseForm, prompt: e.target.value })} /></label><label>预期行为说明<textarea rows={2} value={caseForm.description} onChange={(e) => setCaseForm({ ...caseForm, description: e.target.value })} /></label>{error && <div className="form-error">{error}</div>}<button className="primary-button wide" onClick={saveCase}><Check size={15} /> 保存用例</button></div></Modal>}</div>;
}

function RunsPage({ agents, datasets, runs, onRefresh, onOpenRun }: { agents: Agent[]; datasets: Dataset[]; runs: Run[]; onRefresh: () => void; onOpenRun: (run: Run) => void }) {
  const [agent, setAgent] = useState(agents[0]?.id || "");
  const [dataset, setDataset] = useState(datasets[0]?.id || "");
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState("");
  useEffect(() => { if (!agent && agents[0]) setAgent(agents[0].id); if (!dataset && datasets[0]) setDataset(datasets[0].id); }, [agents, datasets, agent, dataset]);
  const run = async () => { setRunning(true); setMessage(""); try { await api("/evaluations/universal-run", { method: "POST", body: JSON.stringify({ workspace_id: localStorage.getItem("ath_workspace") || "ws_primary", agent_id: agent, dataset_id: dataset }) }); setMessage("评测已完成，结果已写入运行历史。"); onRefresh(); } catch (err) { setMessage(err instanceof Error ? err.message : "运行失败"); } finally { setRunning(false); } };
  return <div className="page-content"><div className="page-heading"><div><p className="eyebrow">Evaluation / Runs</p><h1>评测运行</h1><p className="muted">选择目标与测试集，启动一次可审计的端到端评测。</p></div></div><section className="panel launch-panel"><div className="launch-copy"><div className="launch-icon"><Play size={19} /></div><div><h2>启动一次新评测</h2><p className="muted">运行结果由实际执行产生，包含用例通过率、状态断言和 Trace 证据。</p></div></div><div className="launch-controls"><label>被测 Agent<select value={agent} onChange={(e) => setAgent(e.target.value)}>{agents.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.model_name}</option>)}</select></label><label>评测数据集<select value={dataset} onChange={(e) => setDataset(e.target.value)}>{datasets.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.case_count || 0} cases</option>)}</select></label><button className="primary-button" disabled={running || !agent || !dataset} onClick={run}>{running ? <Activity className="spin" size={15} /> : <Play size={15} />}{running ? "执行中..." : "启动评测"}</button></div>{message && <div className="run-message"><Check size={15} />{message}</div>}</section><section className="panel recent-panel"><div className="panel-header"><div><h2>运行历史</h2><p className="muted">每次运行都会保留目标、数据集和结果摘要。</p></div></div><RunTable runs={runs} onOpen={onOpenRun} /></section></div>;
}

function RunDetail({ run, onClose }: { run: Run; onClose: () => void }) {
  const [detail, setDetail] = useState<any>(null);
  const [error, setError] = useState("");
  useEffect(() => { api(`/evaluations/runs/${run.id}`).then(setDetail).catch((err) => setError(err instanceof Error ? err.message : "加载报告失败")); }, [run.id]);
  if (error) return <Modal title="运行报告" onClose={onClose}><div className="form-error">{error}</div></Modal>;
  if (!detail) return <Modal title="运行报告" onClose={onClose}><div className="boot-screen compact">载入逐用例报告...</div></Modal>;
  return <Modal title={`运行报告 · ${run.id}`} onClose={onClose}><div className="report-summary"><strong>{Math.round(Number(detail.summary.score || 0) * 100)}%</strong><span>{detail.summary.passed_cases} / {detail.summary.total_cases} 用例通过</span><span>{detail.summary.agent_name} · {detail.summary.dataset_name}</span></div><div className="report-cases">{(detail.case_results || []).map((item: any) => <article className="report-case" key={item.case_id}><div className="case-item-head"><strong>{item.title}</strong><span className={`status ${item.result?.is_passed ? "success" : "warning"}`}>{item.result?.is_passed ? "通过" : "未通过"}</span></div><p>{item.prompt}</p><div className="report-facts"><span>得分 {Math.round(Number(item.result?.total_score || 0) * 100)}%</span><span>状态断言 {item.result?.world_state_passed ? "通过" : "未通过"}</span><span>{item.result?.trace?.events?.length || 0} 条 Trace 事件</span></div>{item.result?.rubric_judgments?.map((judgment: any, index: number) => <div className="judgment" key={`${judgment.rubric_id}-${index}`}><b>{judgment.rubric_id}</b><span>{judgment.verdict}</span><p>{judgment.rationale}</p></div>)}<details><summary>查看执行 Trace</summary><pre>{JSON.stringify(item.result?.trace?.events || [], null, 2)}</pre></details></article>)}</div></Modal>;
}

export default function Home() {
  const [auth, setAuth] = useState<{ user: User; workspaces: Workspace[] } | null>(null);
  const [booting, setBooting] = useState(true);
  const [view, setView] = useState<View>("overview");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [workspace, setWorkspace] = useState("");
  const [sidebar, setSidebar] = useState(false);
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const [error, setError] = useState("");
  const load = async (workspaceId: string) => { try { const [ag, ds, rh] = await Promise.all([api(`/agents?workspace_id=${workspaceId}`), api(`/datasets?workspace_id=${workspaceId}`), api(`/evaluations/runs?workspace_id=${workspaceId}`)]); setAgents(ag); setDatasets(ds); setRuns(rh); setError(""); } catch (err) { setError(err instanceof Error ? err.message : "加载数据失败"); } };
  useEffect(() => { const token = localStorage.getItem("ath_token"); if (!token) { setBooting(false); return; } api("/auth/me").then((data) => { setAuth(data); const first = data.workspaces[0]?.id || ""; const current = data.workspaces.some((item: Workspace) => item.id === localStorage.getItem("ath_workspace")) ? localStorage.getItem("ath_workspace") || first : first; setWorkspace(current); localStorage.setItem("ath_workspace", current); return load(current); }).catch(() => { localStorage.removeItem("ath_token"); setBooting(false); }).finally(() => setBooting(false)); }, []);
  useEffect(() => { if (workspace && auth) load(workspace); }, [workspace, auth]);
  if (booting) return <div className="boot-screen"><Sparkles size={22} /><span>正在打开控制台...</span></div>;
  if (!auth) return <AuthScreen onAuthenticated={(data) => { setAuth({ user: data.user, workspaces: [{ id: data.workspace_id, name: "我的工作区", member_role: "owner" }] }); setWorkspace(data.workspace_id); localStorage.setItem("ath_workspace", data.workspace_id); }} />;
  const workspaceName = auth.workspaces.find((item) => item.id === workspace)?.name || "工作区";
  const nav = [{ id: "overview" as View, label: "概览", icon: LayoutDashboard }, { id: "experiments" as View, label: "评测实验", icon: FlaskConical }, { id: "runs" as View, label: "单次运行", icon: Activity }, { id: "agents" as View, label: "Agent 资产", icon: Bot }, { id: "datasets" as View, label: "数据集", icon: Database }];
  const logout = async () => { await api("/auth/logout", { method: "POST" }).catch(() => undefined); localStorage.removeItem("ath_token"); setAuth(null); };
  return <div className="app-shell"><aside className={`sidebar ${sidebar ? "open" : ""}`}><div className="sidebar-brand"><div className="brand-mark"><Sparkles size={16} /></div><strong>AgentTestHub</strong><span>beta</span></div><div className="workspace-select"><div className="workspace-avatar">{workspaceName.slice(0, 1)}</div><div><small>当前工作区</small><strong>{workspaceName}</strong></div><ChevronDown size={15} /></div><nav>{nav.map((item) => { const Icon = item.icon; return <button key={item.id} className={view === item.id ? "active" : ""} onClick={() => { setView(item.id); setSidebar(false); }}><Icon size={17} />{item.label}</button>; })}</nav><div className="sidebar-section"><small>治理</small><button><Users size={17} />团队成员<span className="soon">即将推出</span></button><button><Settings2 size={17} />工作区设置</button></div><div className="sidebar-bottom"><div className="connection"><span className="online-dot" />API 服务正常</div><div className="user-row"><div className="user-avatar">{auth.user.name.slice(0, 1)}</div><div><strong>{auth.user.name}</strong><small>{auth.user.email}</small></div><button className="icon-button" onClick={logout} title="退出登录"><LogOut size={15} /></button></div></div></aside><div className="main-shell"><header className="topbar"><button className="mobile-menu icon-button" onClick={() => setSidebar(!sidebar)}><Menu size={19} /></button><div className="breadcrumbs"><span>{workspaceName}</span><span>/</span><strong>{nav.find((item) => item.id === view)?.label}</strong></div><div className="topbar-actions"><span className="command-hint">⌘ K</span><button className="icon-button" title="帮助"><CircleHelp size={17} /></button></div></header>{error && <div className="global-error">{error}<button onClick={() => setError("")}><X size={14} /></button></div>}{view === "overview" && <Overview runs={runs} agents={agents} datasets={datasets} onNavigate={setView} onOpenRun={setSelectedRun} />}{view === "experiments" && <ExperimentView workspaceId={workspace} agents={agents} datasets={datasets} api={api} onRefresh={() => load(workspace)} />}{view === "runs" && <RunsPage agents={agents} datasets={datasets} runs={runs} onRefresh={() => load(workspace)} onOpenRun={setSelectedRun} />}{view === "agents" && <AgentsPage agents={agents} onRefresh={() => load(workspace)} />}{view === "datasets" && <DatasetsPage datasets={datasets} onRefresh={() => load(workspace)} />}{selectedRun && <RunDetail run={selectedRun} onClose={() => setSelectedRun(null)} />}</div></div>;
}
