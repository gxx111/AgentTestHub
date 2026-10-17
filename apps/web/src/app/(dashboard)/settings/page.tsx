"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import {
  BookOpen,
  Building2,
  LogOut,
  Mail,
  ShieldCheck,
  UserPlus,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useResource } from "@/hooks/use-resource";
import type { WorkspaceMember } from "@/lib/types";
import { formatDate, memberRoleLabel } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input, Select } from "@/components/ui/field";
import { PageHeader } from "@/components/ui/page-header";
import { Spinner } from "@/components/ui/spinner";
import { useToast } from "@/components/ui/toast";

export default function SettingsPage() {
  const { user, workspace, workspaceId, logout } = useAuth();
  const toast = useToast();
  const members = useResource<WorkspaceMember[]>(
    `members:${workspaceId}`,
    () => api.listMembers(workspaceId as string),
    Boolean(workspaceId),
  );
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("engineer");
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState("");

  const canInvite =
    workspace?.member_role === "owner" || workspace?.member_role === "admin";

  async function handleInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setInviteError("");
    if (!workspaceId) return;
    if (!email.trim()) {
      setInviteError("请填写成员邮箱");
      return;
    }
    setInviting(true);
    try {
      await api.inviteMember(workspaceId, email.trim(), role);
      toast.push("成员已加入工作区", "success");
      setEmail("");
      await members.refresh();
    } catch (err) {
      setInviteError(err instanceof Error ? err.message : "邀请失败");
    } finally {
      setInviting(false);
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="治理"
        title="工作区设置"
        description="管理成员、角色与 API 连接。当前版本使用本地账号体系；企业版将支持 SSO 与审计。"
      />

      <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
        <div className="space-y-5">
          <section className="rounded-2xl border border-app-line bg-app-surface p-5">
            <div className="flex items-start gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-brand-soft text-brand">
                <Building2 className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-base font-semibold text-app-text">
                    {workspace?.name ?? "未选择工作区"}
                  </h2>
                  {workspace?.member_role && (
                    <Badge tone="info">{memberRoleLabel(workspace.member_role)}</Badge>
                  )}
                </div>
                <p className="mt-1 font-mono text-xs text-app-muted">{workspace?.id ?? "—"}</p>
                <p className="mt-2 text-xs text-app-muted">
                  创建工作区后，Agent、数据集、实验和评测团队都按工作区隔离。
                </p>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-app-line bg-app-surface">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-app-line px-5 py-4">
              <div>
                <h2 className="text-sm font-semibold text-app-text">工作区成员</h2>
                <p className="mt-0.5 text-xs text-app-muted">
                  owner/admin 可邀请成员；engineer 可创建资产与实验。
                </p>
              </div>
              {members.data && <Badge>{members.data.length} 人</Badge>}
            </div>

            {members.loading ? (
              <div className="flex justify-center py-10">
                <Spinner className="h-5 w-5 text-brand" />
              </div>
            ) : members.error ? (
              <div className="px-5 py-4 text-sm text-red-700">
                {members.error}
                <button className="ml-3 underline" onClick={() => void members.refresh()}>
                  重试
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[560px] text-left">
                  <thead>
                    <tr className="border-b border-app-line bg-app-subtle text-[11px] uppercase tracking-wider text-app-muted">
                      <th className="px-5 py-3 font-medium">成员</th>
                      <th className="px-5 py-3 font-medium">角色</th>
                      <th className="px-5 py-3 font-medium">加入时间</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-app-line">
                    {(members.data ?? []).map((member) => (
                      <tr key={member.id} className="text-sm">
                        <td className="px-5 py-3">
                          <p className="font-medium text-app-text">{member.name}</p>
                          <p className="text-xs text-app-muted">{member.email}</p>
                        </td>
                        <td className="px-5 py-3">
                          <Badge tone={member.role === "owner" ? "info" : "neutral"}>
                            {memberRoleLabel(member.role)}
                          </Badge>
                        </td>
                        <td className="px-5 py-3 text-xs text-app-muted">
                          {formatDate(member.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {canInvite && (
              <form
                className="grid gap-3 border-t border-app-line bg-app-subtle/60 px-5 py-4 sm:grid-cols-[1fr_160px_auto]"
                onSubmit={handleInvite}
              >
                <Field label="邀请成员">
                  <Input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="member@company.com"
                  />
                </Field>
                <Field label="角色">
                  <Select value={role} onChange={(event) => setRole(event.target.value)}>
                    <option value="engineer">工程师</option>
                    <option value="reviewer">评审员</option>
                    <option value="admin">管理员</option>
                  </Select>
                </Field>
                <div className="flex items-end">
                  <Button
                    type="submit"
                    loading={inviting}
                    icon={<UserPlus className="h-4 w-4" />}
                    className="w-full sm:w-auto"
                  >
                    邀请
                  </Button>
                </div>
                {inviteError && (
                  <p className="text-xs text-red-600 sm:col-span-3">{inviteError}</p>
                )}
              </form>
            )}
          </section>
        </div>

        <div className="space-y-5">
          <section className="rounded-2xl border border-app-line bg-app-surface p-5">
            <h2 className="text-sm font-semibold text-app-text">当前账号</h2>
            <div className="mt-4 flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded-full bg-app-text text-sm font-semibold text-white">
                {(user?.name || user?.email || "U").slice(0, 1).toUpperCase()}
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-app-text">{user?.name}</p>
                <p className="truncate text-xs text-app-muted">{user?.email}</p>
              </div>
            </div>
            <dl className="mt-4 space-y-3 border-t border-app-line pt-4 text-xs">
              <div className="flex items-center justify-between">
                <dt className="text-app-muted">账号角色</dt>
                <dd className="font-medium text-app-text">
                  {user?.role ? memberRoleLabel(user.role) : "—"}
                </dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-app-muted">工作区角色</dt>
                <dd className="font-medium text-app-text">
                  {workspace?.member_role ? memberRoleLabel(workspace.member_role) : "—"}
                </dd>
              </div>
            </dl>
          </section>

          <section className="rounded-2xl border border-app-line bg-app-surface p-5">
            <h2 className="text-sm font-semibold text-app-text">API 连接</h2>
            <p className="mt-1 text-xs text-app-muted">
              前端通过以下地址访问控制面。生产环境请使用 HTTPS 并配置 CORS。
            </p>
            <code className="mt-3 block break-all rounded-lg border border-app-line bg-app-subtle px-3 py-2 font-mono text-[11px] text-app-text">
              {apiBase()}
            </code>
          </section>

          <section className="rounded-2xl border border-app-line bg-app-surface p-5">
            <h2 className="text-sm font-semibold text-app-text">帮助与治理</h2>
            <div className="mt-3 space-y-2">
              <a
                href="https://github.com/gxx111/AgentTestHub/tree/main/docs"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 rounded-lg border border-app-line px-3 py-2 text-xs text-app-text hover:bg-app-subtle"
              >
                <BookOpen className="h-4 w-4 text-app-muted" />
                研发文档与路线图
              </a>
              <div className="flex items-center gap-2 rounded-lg border border-app-line px-3 py-2 text-xs text-app-muted">
                <ShieldCheck className="h-4 w-4" />
                审计日志与 SSO 将在企业版提供
              </div>
              <div className="flex items-center gap-2 rounded-lg border border-app-line px-3 py-2 text-xs text-app-muted">
                <Mail className="h-4 w-4" />
                成员邀请需要对方先注册账号
              </div>
            </div>
          </section>

          <Button
            variant="secondary"
            className="w-full border-red-200 text-red-600 hover:bg-red-50"
            icon={<LogOut className="h-4 w-4" />}
            onClick={() => void logout()}
          >
            退出登录
          </Button>
        </div>
      </div>
    </div>
  );
}

function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005/api/v1";
}
