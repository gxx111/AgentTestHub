"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  AlertCircle,
  ArrowRight,
  Bot,
  CheckCircle2,
  Cpu,
  Database,
  Eye,
  EyeOff,
  FlaskConical,
  GitBranch,
  LayoutDashboard,
  LockKeyhole,
  Mail,
  Scale,
  ShieldCheck,
  Sparkles,
  UserRound,
  Users,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { Spinner } from "@/components/ui/spinner";

const features = [
  { icon: Cpu, label: "双控用户模拟" },
  { icon: Database, label: "业务世界沙盒" },
  { icon: GitBranch, label: "轨迹级证据" },
  { icon: ShieldCheck, label: "CI 发布门禁" },
];

const navItems = [
  { icon: LayoutDashboard, label: "概览", active: false },
  { icon: FlaskConical, label: "实验", active: true },
  { icon: Database, label: "数据集", active: false },
  { icon: Bot, label: "Agent", active: false },
  { icon: Users, label: "团队", active: false },
];

const stages = [
  { icon: UserRound, label: "用户模拟官", detail: "隐藏目标 · 第 3 轮", state: "done" as const },
  { icon: Bot, label: "被测 Agent", detail: "调用 refund_apply", state: "done" as const },
  { icon: Database, label: "业务沙盒", detail: "状态差分通过", state: "done" as const },
  { icon: Scale, label: "评审团", detail: "2 位法官 · 证据锚定", state: "active" as const },
];

const bars = [38, 52, 44, 66, 58, 74, 64, 82, 70, 88, 78, 96];
const verdicts = [
  { label: "业务法官", value: "YES", tone: "text-emerald-300", bg: "bg-emerald-400/10" },
  { label: "安全法官", value: "YES", tone: "text-emerald-300", bg: "bg-emerald-400/10" },
  { label: "首席仲裁", value: "无需触发", tone: "text-slate-400", bg: "bg-white/[0.04]" },
];

const inputClass =
  "h-12 w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 text-sm text-white " +
  "placeholder:text-slate-500 outline-none transition focus:border-blue-400/60 " +
  "focus:bg-white/[0.06] focus:ring-2 focus:ring-blue-500/20";

export default function LoginPage() {
  const router = useRouter();
  const { user, loading, login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace("/overview");
  }, [loading, router, user]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!email.trim() || !password) {
      setError("请填写邮箱和密码");
      return;
    }
    if (mode === "register" && password.length < 8) {
      setError("密码至少需要 8 个字符");
      return;
    }
    setSubmitting(true);
    try {
      if (mode === "login") {
        await login(email.trim(), password);
      } else {
        await register(name.trim() || email.split("@")[0], email.trim(), password);
      }
      router.replace("/overview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失败，请稍后重试");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="login-bg relative min-h-screen overflow-hidden text-white"
      onMouseMove={(event) => {
        const rect = event.currentTarget.getBoundingClientRect();
        event.currentTarget.style.setProperty("--mx", `${event.clientX - rect.left}px`);
        event.currentTarget.style.setProperty("--my", `${event.clientY - rect.top}px`);
      }}
    >
      <div className="login-grid pointer-events-none absolute inset-0 opacity-80" />
      <div className="login-spotlight pointer-events-none absolute inset-0" />
      <div className="login-aurora left-[-10%] top-[-16%] h-[40rem] w-[40rem] bg-blue-600/30" />
      <div className="login-aurora login-aurora-delayed right-[-12%] top-[4%] h-[34rem] w-[34rem] bg-cyan-400/20" />
      <div className="login-aurora left-[38%] bottom-[-30%] h-[38rem] w-[38rem] bg-indigo-600/25" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-blue-400/60 to-transparent" />

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-[1560px] flex-col px-5 py-6 sm:px-8 lg:px-12">
        <header className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="relative grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 shadow-[0_0_28px_rgba(37,99,235,0.45)]">
              <ShieldCheck className="h-5 w-5 text-white" />
              <span className="login-pulse absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full bg-emerald-400 ring-4 ring-emerald-400/10" />
            </div>
            <div>
              <p className="text-sm font-semibold tracking-tight">AgentTestHub</p>
              <p className="text-[11px] text-slate-400">Agent Release Gate</p>
            </div>
          </div>

          <div className="hidden items-center gap-2 sm:flex">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-[11px] text-slate-400">
              <LockKeyhole className="h-3 w-3 text-emerald-400" />
              Private by default
            </span>
            <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-[11px] text-slate-400">
              v0.2 · Beta
            </span>
          </div>
        </header>

        <main className="grid flex-1 items-center gap-10 py-8 lg:grid-cols-[1.28fr_0.72fr] lg:gap-14 lg:py-6">
          <section className="login-fade-up min-w-0">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-400/20 bg-blue-500/10 px-3 py-1.5 text-[11px] font-medium uppercase tracking-[0.18em] text-blue-200">
              <span className="login-pulse h-1.5 w-1.5 rounded-full bg-blue-300" />
              Agent Reliability Engineering
            </div>

            <h1 className="mt-6 max-w-3xl text-4xl font-semibold leading-[1.06] tracking-[-0.045em] sm:text-5xl xl:text-[66px]">
              让每一次 Agent 发布
              <br />
              <span className="bg-gradient-to-r from-blue-300 via-cyan-200 to-indigo-300 bg-clip-text text-transparent">
                都带着证据。
              </span>
            </h1>

            <p className="mt-5 max-w-2xl text-sm leading-7 text-slate-400 sm:text-base">
              用可复现的仿真环境、双控用户模拟和带 Span 证据的轨迹裁决，在发布前回答
              <span className="text-slate-200">“这个版本能不能上线”</span>。
            </p>

            <div className="mt-6 flex flex-wrap gap-2">
              {features.map((feature) => {
                const Icon = feature.icon;
                return (
                  <span
                    key={feature.label}
                    className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-slate-300 backdrop-blur"
                  >
                    <Icon className="h-3.5 w-3.5 text-blue-300" />
                    {feature.label}
                  </span>
                );
              })}
            </div>

            <div className="login-float relative mt-8 hidden max-w-[900px] sm:block">
              <div className="absolute -inset-8 rounded-[3rem] bg-gradient-to-r from-blue-500/15 via-cyan-400/10 to-indigo-500/15 blur-3xl" />
              <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#070c16]/95 shadow-[0_50px_140px_-40px_rgba(0,0,0,1)] backdrop-blur-xl">
                <div className="login-scan pointer-events-none absolute inset-y-0 left-0 w-1/5 bg-gradient-to-r from-transparent via-cyan-300/[0.08] to-transparent" />

                <div className="flex h-11 items-center gap-2 border-b border-white/[0.06] px-4">
                  <span className="h-2 w-2 rounded-full bg-red-400/70" />
                  <span className="h-2 w-2 rounded-full bg-amber-400/70" />
                  <span className="h-2 w-2 rounded-full bg-emerald-400/70" />
                  <span className="ml-3 hidden text-[10px] text-slate-500 sm:inline">
                    agenttesthub / experiments / exp_9f2c…
                  </span>
                  <span className="ml-auto inline-flex items-center gap-1.5 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-[9px] font-medium text-emerald-300">
                    <span className="login-pulse h-1.5 w-1.5 rounded-full bg-emerald-300" />
                    LIVE
                  </span>
                </div>

                <div className="grid sm:grid-cols-[134px_1fr]">
                  <aside className="hidden border-r border-white/[0.06] bg-white/[0.015] p-3 sm:block">
                    <div className="space-y-1">
                      {navItems.map((item) => {
                        const Icon = item.icon;
                        return (
                          <div
                            key={item.label}
                            className={
                              item.active
                                ? "flex items-center gap-2 rounded-lg bg-blue-500/10 px-2.5 py-1.5 text-[10px] font-medium text-blue-200"
                                : "flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-[10px] text-slate-500"
                            }
                          >
                            <Icon className="h-3 w-3" />
                            {item.label}
                          </div>
                        );
                      })}
                    </div>
                    <div className="mt-4 rounded-lg border border-white/[0.06] bg-white/[0.02] p-2.5">
                      <p className="text-[9px] uppercase tracking-[0.16em] text-slate-500">Gate policy</p>
                      <p className="mt-1 text-[10px] font-medium text-emerald-300">pass ≥ 95%</p>
                      <p className="text-[9px] text-slate-500">fatal = 0</p>
                    </div>
                  </aside>

                  <div className="p-4">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="text-[9px] uppercase tracking-[0.2em] text-blue-300">
                          Experiment report
                        </p>
                        <h3 className="mt-1 text-sm font-semibold text-white">退款回归实验</h3>
                        <p className="mt-0.5 text-[10px] text-slate-500">
                          refund-agent:v12 · 24 cases · 5 repetitions
                        </p>
                      </div>
                      <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-[9px] font-medium text-emerald-300">
                        可发布
                      </span>
                    </div>

                    <div className="mt-3 grid grid-cols-3 gap-2">
                      {[
                        { label: "通过率", value: "96.2%" },
                        { label: "平均分", value: "94.1%" },
                        { label: "Flaky", value: "1" },
                      ].map((metric) => (
                        <div
                          key={metric.label}
                          className="rounded-lg border border-white/[0.06] bg-white/[0.025] px-2.5 py-2"
                        >
                          <p className="text-[9px] text-slate-500">{metric.label}</p>
                          <p className="mt-0.5 text-sm font-semibold text-white">{metric.value}</p>
                        </div>
                      ))}
                    </div>

                    <div className="mt-3 grid gap-3 md:grid-cols-[1fr_174px]">
                      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] text-slate-400">Trace timeline</span>
                          <span className="text-[9px] text-slate-500">284 spans</span>
                        </div>
                        <div className="mt-2 space-y-1.5">
                          {stages.map((stage) => {
                            const Icon = stage.icon;
                            return (
                              <div
                                key={stage.label}
                                className="flex items-center gap-2 rounded-lg border border-white/[0.05] bg-white/[0.015] px-2.5 py-1.5"
                              >
                                <div className="grid h-6 w-6 place-items-center rounded-md bg-white/[0.05] text-slate-300">
                                  <Icon className="h-3 w-3" />
                                </div>
                                <div className="min-w-0 flex-1">
                                  <p className="truncate text-[10px] font-medium text-slate-200">
                                    {stage.label}
                                  </p>
                                  <p className="truncate text-[9px] text-slate-500">{stage.detail}</p>
                                </div>
                                {stage.state === "active" ? (
                                  <span className="login-pulse h-1.5 w-1.5 rounded-full bg-cyan-300" />
                                ) : (
                                  <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                                )}
                              </div>
                            );
                          })}
                        </div>
                        <div className="mt-3 flex h-8 items-end gap-1">
                          {bars.map((height, index) => (
                            <div
                              key={index}
                              className="flex-1 rounded-sm bg-gradient-to-t from-blue-500/30 to-cyan-400/70"
                              style={{ height: `${height}%` }}
                            />
                          ))}
                        </div>
                      </div>

                      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3">
                        <p className="text-[10px] text-slate-400">Judge verdicts</p>
                        <div className="mt-2 space-y-1.5">
                          {verdicts.map((verdict) => (
                            <div
                              key={verdict.label}
                              className={`flex items-center justify-between gap-2 rounded-lg px-2.5 py-2 ${verdict.bg}`}
                            >
                              <span className="text-[9px] text-slate-300">{verdict.label}</span>
                              <span className={`text-[9px] font-medium ${verdict.tone}`}>
                                {verdict.value}
                              </span>
                            </div>
                          ))}
                        </div>
                        <div className="mt-3 rounded-lg border border-white/[0.05] bg-white/[0.02] p-2">
                          <p className="text-[9px] text-slate-500">Evidence</p>
                          <p className="mt-0.5 text-[9px] text-slate-300">spn_8f2c · spn_91ad</p>
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-white/[0.06] pt-2 text-[9px] text-slate-500">
                      <span className="inline-flex items-center gap-1">
                        <ShieldCheck className="h-3 w-3 text-emerald-400" />
                        CI Gate · PASSED
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Activity className="h-3 w-3" />
                        5 repetitions
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <GitBranch className="h-3 w-3" />
                        snapshot 8ac1…
                      </span>
                      <span className="ml-auto inline-flex items-center gap-1 text-cyan-300/80">
                        <Sparkles className="h-3 w-3" />
                        Evidence anchored
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="absolute -right-3 -top-4 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-[10px] font-medium text-emerald-300 shadow-lg backdrop-blur">
                LIVE · Trace replay
              </div>
            </div>
          </section>

          <section
            className="login-fade-up flex justify-center lg:justify-end"
            style={{ animationDelay: "120ms" }}
          >
            <div className="relative w-full max-w-[420px]">
              <div className="absolute -inset-6 rounded-[2.2rem] bg-blue-500/10 blur-3xl" />
              <div className="relative rounded-[1.65rem] bg-gradient-to-b from-white/20 via-white/[0.06] to-white/[0.02] p-px">
                <div className="relative overflow-hidden rounded-[1.6rem] bg-[#080d18]/95 p-6 shadow-[0_40px_120px_-30px_rgba(0,0,0,1)] backdrop-blur-2xl sm:p-8">
                  <div className="pointer-events-none absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-blue-400/70 to-transparent" />

                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-blue-300">
                        Secure access
                      </p>
                      <h2 className="mt-1.5 text-2xl font-semibold tracking-tight">
                        {mode === "login" ? "进入工作区" : "创建你的工作区"}
                      </h2>
                      <p className="mt-1 text-xs leading-5 text-slate-400">
                        {mode === "login"
                          ? "继续管理 Agent 评测、证据与发布门禁。"
                          : "注册后自动生成起步工作区与演示资产。"}
                      </p>
                    </div>
                    <div className="hidden h-10 w-10 place-items-center rounded-full border border-white/10 bg-white/[0.04] text-blue-300 sm:grid">
                      <LockKeyhole className="h-4 w-4" />
                    </div>
                  </div>

                  <div className="mt-6 grid grid-cols-2 gap-1 rounded-xl border border-white/10 bg-white/[0.03] p-1">
                    {(["login", "register"] as const).map((item) => (
                      <button
                        key={item}
                        type="button"
                        onClick={() => {
                          setMode(item);
                          setError("");
                        }}
                        className={
                          mode === item
                            ? "rounded-lg bg-white/10 px-3 py-2 text-sm font-medium text-white shadow-inner"
                            : "rounded-lg px-3 py-2 text-sm text-slate-400 transition hover:text-slate-200"
                        }
                      >
                        {item === "login" ? "登录" : "注册"}
                      </button>
                    ))}
                  </div>

                  <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
                    {mode === "register" && (
                      <label className="block">
                        <span className="mb-1.5 block text-xs font-medium text-slate-300">姓名</span>
                        <div className="relative">
                          <UserRound className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                          <input
                            className={`${inputClass} pl-10`}
                            value={name}
                            onChange={(event) => setName(event.target.value)}
                            placeholder="你的名字"
                            autoComplete="name"
                          />
                        </div>
                      </label>
                    )}

                    <label className="block">
                      <span className="mb-1.5 block text-xs font-medium text-slate-300">
                        邮箱 <span className="text-blue-300">*</span>
                      </span>
                      <div className="relative">
                        <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                        <input
                          className={`${inputClass} pl-10`}
                          type="email"
                          value={email}
                          onChange={(event) => setEmail(event.target.value)}
                          placeholder="you@company.com"
                          autoComplete="email"
                        />
                      </div>
                    </label>

                    <label className="block">
                      <span className="mb-1.5 block text-xs font-medium text-slate-300">
                        密码 <span className="text-blue-300">*</span>
                      </span>
                      <div className="relative">
                        <LockKeyhole className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                        <input
                          className={`${inputClass} pl-10 pr-11`}
                          type={showPassword ? "text" : "password"}
                          value={password}
                          onChange={(event) => setPassword(event.target.value)}
                          placeholder={mode === "register" ? "至少 8 个字符" : "••••••••"}
                          autoComplete={mode === "login" ? "current-password" : "new-password"}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword((value) => !value)}
                          className="absolute right-2 top-1/2 grid h-8 w-8 -translate-y-1/2 place-items-center rounded-lg text-slate-500 transition hover:bg-white/[0.06] hover:text-slate-300"
                          aria-label={showPassword ? "隐藏密码" : "显示密码"}
                        >
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                    </label>

                    {error && (
                      <div
                        role="alert"
                        className="login-shake flex items-start gap-2 rounded-xl border border-red-400/20 bg-red-500/10 px-3 py-2.5 text-xs leading-5 text-red-200"
                      >
                        <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                        <span>{error}</span>
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={submitting}
                      className="group relative flex h-12 w-full items-center justify-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-blue-500 via-blue-500 to-cyan-400 text-sm font-semibold text-white shadow-[0_12px_40px_-12px_rgba(37,99,235,0.8)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <span className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition duration-700 group-hover:translate-x-full" />
                      {submitting ? (
                        <Spinner className="h-4 w-4" />
                      ) : (
                        <>
                          {mode === "login" ? "进入工作区" : "创建账号"}
                          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                        </>
                      )}
                    </button>
                  </form>

                  <div className="mt-5 flex items-center justify-center gap-2 text-[11px] text-slate-500">
                    <ShieldCheck className="h-3.5 w-3.5 text-emerald-400/80" />
                    本地部署 · 数据不出域 · 评测结果可审计
                  </div>

                  <p className="mt-4 text-center text-[10px] leading-5 text-slate-600">
                    登录即表示你同意仅将平台用于授权的 Agent 测试与评测。
                  </p>
                </div>
              </div>
            </div>
          </section>
        </main>

        <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.06] py-5 text-[10px] text-slate-600">
          <span>AgentTestHub © 2026 · Agent Reliability Engineering</span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400/80" />
            API ready · 8005
          </span>
        </footer>
      </div>
    </div>
  );
}
