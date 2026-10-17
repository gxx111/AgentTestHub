"use client";

import { useState } from "react";
import {
  Clock,
  GitBranch,
  Pencil,
  Plus,
  Scale,
  ShieldCheck,
  Trash2,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useResource } from "@/hooks/use-resource";
import type { EvaluationTeam } from "@/lib/types";
import { formatDate, roleLabel } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { PageHeader } from "@/components/ui/page-header";
import { Spinner } from "@/components/ui/spinner";
import { useToast } from "@/components/ui/toast";
import { TeamForm } from "@/components/teams/team-form";

const teamRoles = [
  { role: "user_simulator", description: "模拟真实用户，分阶段释放隐藏信息" },
  { role: "red_team_attacker", description: "可选。安全用例中注入攻击，验证防线" },
  { role: "business_judge", description: "判断业务目标、流程与事实" },
  { role: "safety_judge", description: "检查安全红线，fatal 一票否决" },
  { role: "moderator", description: "评委分歧时基于证据仲裁" },
];

export default function TeamsPage() {
  const { workspaceId } = useAuth();
  const toast = useToast();
  const teams = useResource<EvaluationTeam[]>(
    `teams:${workspaceId}`,
    () => api.listTeams(workspaceId as string),
    Boolean(workspaceId),
  );
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<EvaluationTeam | null>(null);

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(team: EvaluationTeam) {
    setEditing(team);
    setModalOpen(true);
  }

  async function remove(team: EvaluationTeam) {
    if (!workspaceId) return;
    if (!window.confirm(`删除评测团队「${team.name}」？`)) return;
    try {
      await api.deleteTeam(team.id, workspaceId);
      toast.push("评测团队已删除", "success");
      await teams.refresh();
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "删除失败", "error");
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="资产"
        title="评测团队"
        description="配置用户模拟官、红队、业务/安全法官和首席仲裁。团队会真实调用模型，并受预算与超时约束。"
        actions={
          <Button icon={<Plus className="h-4 w-4" />} onClick={openCreate}>
            新建团队
          </Button>
        }
      />

      {teams.error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {teams.error}
          <button className="ml-3 underline" onClick={() => void teams.refresh()}>
            重试
          </button>
        </div>
      )}

      {teams.loading ? (
        <div className="flex justify-center py-20">
          <Spinner className="h-6 w-6 text-brand" />
        </div>
      ) : (teams.data ?? []).length === 0 ? (
        <div className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
          <section className="rounded-2xl border border-app-line bg-app-surface p-6">
            <div className="flex items-start gap-4">
              <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-brand-soft text-brand">
                <Users className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-app-text">配置你的 LLM 评审团</h2>
                <p className="mt-1 text-sm leading-6 text-app-muted">
                  用多角色协同替代单一裁判：用户模拟官负责博弈，业务/安全法官独立裁决，首席仲裁处理分歧。
                </p>
              </div>
            </div>

            <div className="mt-6 grid gap-2 sm:grid-cols-2">
              {teamRoles.map((item) => (
                <div
                  key={item.role}
                  className="rounded-xl border border-app-line bg-app-subtle px-3 py-3"
                >
                  <p className="text-sm font-medium text-app-text">{roleLabel(item.role)}</p>
                  <p className="mt-0.5 text-xs leading-5 text-app-muted">{item.description}</p>
                </div>
              ))}
            </div>

            <Button
              className="mt-6"
              icon={<Plus className="h-4 w-4" />}
              onClick={openCreate}
            >
              新建评测团队
            </Button>
          </section>

          <section className="rounded-2xl border border-app-line bg-app-surface p-6">
            <h3 className="text-sm font-semibold text-app-text">为什么需要评测团队？</h3>
            <ul className="mt-4 space-y-4">
              {[
                {
                  icon: ShieldCheck,
                  title: "多视角裁决",
                  text: "业务法官看目标，安全法官看红线，降低单一模型的偏置与幻觉。",
                },
                {
                  icon: Scale,
                  title: "分歧可仲裁",
                  text: "评委意见不一致时，由首席仲裁基于 Span 证据收敛。",
                },
                {
                  icon: GitBranch,
                  title: "证据可追溯",
                  text: "每个判决绑定评委版本、置信度与执行轨迹。",
                },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <li key={item.title} className="flex gap-3">
                    <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-app-subtle text-brand">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-app-text">{item.title}</p>
                      <p className="mt-0.5 text-xs leading-5 text-app-muted">{item.text}</p>
                    </div>
                  </li>
                );
              })}
            </ul>
            <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5 text-xs leading-5 text-amber-900">
              未配置团队时，评测会使用内置启发式评委，仅适合流程验证。
            </div>
          </section>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {(teams.data ?? []).map((team) => {
            const enabledMembers = team.members.filter((member) => member.enabled);
            return (
              <article
                key={team.id}
                className="flex flex-col rounded-xl border border-app-line bg-app-surface p-5"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-lg bg-brand-soft text-brand">
                    <Users className="h-5 w-5" />
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={<Pencil className="h-3.5 w-3.5" />}
                      onClick={() => openEdit(team)}
                    >
                      编辑
                    </Button>
                    <button
                      type="button"
                      aria-label="删除团队"
                      onClick={() => void remove(team)}
                      className="rounded-md p-2 text-app-muted hover:bg-red-50 hover:text-red-600"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                <h2 className="mt-4 text-base font-semibold text-app-text">{team.name}</h2>
                <p className="mt-1 text-xs text-app-muted">
                  {enabledMembers.length} 个启用角色 · 创建于 {formatDate(team.created_at)}
                </p>

                <div className="mt-3 space-y-2">
                  {enabledMembers.map((member) => (
                    <div
                      key={member.role}
                      className="flex items-center justify-between gap-2 rounded-lg border border-app-line bg-app-subtle px-3 py-2"
                    >
                      <span className="text-xs font-medium text-app-text">
                        {roleLabel(member.role)}
                      </span>
                      <span className="truncate font-mono text-[11px] text-app-muted">
                        {member.model}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-app-line pt-3 text-[11px] text-app-muted">
                  <span className="inline-flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    {team.max_turns} 轮 / {team.timeout_seconds}s
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    预算 {team.max_calls}
                  </span>
                  <Badge tone={team.members.some((member) => member.role === "red_team_attacker" && member.enabled) ? "warning" : "neutral"}>
                    红队{team.members.some((member) => member.role === "red_team_attacker" && member.enabled) ? "开启" : "关闭"}
                  </Badge>
                </div>
              </article>
            );
          })}
        </div>
      )}

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? "编辑评测团队" : "新建评测团队"}
        description="配置 4 个必选角色和可选的红色攻击官。"
        size="xl"
      >
        {workspaceId && (
          <TeamForm
            team={editing}
            workspaceId={workspaceId}
            onCancel={() => setModalOpen(false)}
            onSaved={() => {
              setModalOpen(false);
              toast.push(editing ? "评测团队已更新" : "评测团队已创建", "success");
              void teams.refresh();
            }}
          />
        )}
      </Modal>
    </div>
  );
}
