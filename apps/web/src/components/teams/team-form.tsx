"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { KeyRound, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import type { EvaluationTeam, TeamMember } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Field, Input } from "@/components/ui/field";

const roleDefinitions = [
  {
    role: "user_simulator",
    label: "用户模拟官",
    description: "模拟真实业务用户，按隐藏目标分阶段释放信息。",
    required: true,
  },
  {
    role: "red_team_attacker",
    label: "红队攻击官",
    description: "可选。在安全类用例中注入攻击，验证防线。",
    required: false,
  },
  {
    role: "business_judge",
    label: "业务法官",
    description: "判断业务目标、流程与事实是否达成。",
    required: true,
  },
  {
    role: "safety_judge",
    label: "安全法官",
    description: "检查安全红线；fatal 失败不允许被仲裁推翻。",
    required: true,
  },
  {
    role: "moderator",
    label: "首席仲裁",
    description: "评委分歧时，基于证据做最终仲裁。",
    required: true,
  },
] as const;

function initialMembers(team: EvaluationTeam | null): TeamMember[] {
  return roleDefinitions.map((definition) => {
    const existing = team?.members.find((member) => member.role === definition.role);
    return {
      role: definition.role,
      model: existing?.model ?? "gpt-4o-mini",
      api_base: existing?.api_base ?? "https://api.openai.com/v1",
      api_key: "",
      api_key_configured: existing?.api_key_configured ?? false,
      enabled: definition.required ? true : (existing?.enabled ?? false),
    };
  });
}

export function TeamForm({
  team,
  workspaceId,
  onSaved,
  onCancel,
}: {
  team: EvaluationTeam | null;
  workspaceId: string;
  onSaved: () => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(team?.name ?? "");
  const [maxTurns, setMaxTurns] = useState(team?.max_turns ?? 4);
  const [timeoutSeconds, setTimeoutSeconds] = useState(team?.timeout_seconds ?? 30);
  const [maxCalls, setMaxCalls] = useState(team?.max_calls ?? 30);
  const [members, setMembers] = useState<TeamMember[]>(() => initialMembers(team));
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function patchMember(role: string, patch: Partial<TeamMember>) {
    setMembers((current) =>
      current.map((member) => (member.role === role ? { ...member, ...patch } : member)),
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!name.trim()) {
      setError("请填写团队名称");
      return;
    }
    const enabled = members.filter((member) => member.enabled);
    for (const member of enabled) {
      if (!member.model.trim() || !member.api_base.trim()) {
        setError(`请填写 ${roleDefinitions.find((item) => item.role === member.role)?.label} 的模型与 API Base`);
        return;
      }
      if (!/^https?:\/\//i.test(member.api_base.trim())) {
        setError("API Base 必须是 HTTP(S) 地址");
        return;
      }
    }
    const required = ["user_simulator", "business_judge", "safety_judge", "moderator"];
    if (!required.every((role) => enabled.some((member) => member.role === role))) {
      setError("用户模拟官、业务法官、安全法官和首席仲裁都是必选角色");
      return;
    }

    setSaving(true);
    try {
      const payload = {
        workspace_id: workspaceId,
        name: name.trim(),
        members: members.map((member) => ({
          role: member.role,
          model: member.model.trim(),
          api_base: member.api_base.trim(),
          api_key: member.api_key ?? "",
          enabled: member.enabled,
        })),
        max_turns: maxTurns,
        timeout_seconds: timeoutSeconds,
        max_calls: maxCalls,
      };
      if (team) await api.updateTeam(team.id, payload);
      else await api.createTeam(payload);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      <div className="grid gap-4 sm:grid-cols-4">
        <div className="sm:col-span-2">
          <Field label="团队名称" required>
            <Input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="例如：退款业务评审团"
            />
          </Field>
        </div>
        <Field label="最大轮次">
          <Input
            type="number"
            min={2}
            max={12}
            value={maxTurns}
            onChange={(event) => setMaxTurns(Number(event.target.value) || 4)}
          />
        </Field>
        <Field label="超时（秒）">
          <Input
            type="number"
            min={5}
            max={120}
            value={timeoutSeconds}
            onChange={(event) => setTimeoutSeconds(Number(event.target.value) || 30)}
          />
        </Field>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="调用预算" hint="每次用例允许的最大模型调用次数">
          <Input
            type="number"
            min={5}
            max={100}
            value={maxCalls}
            onChange={(event) => setMaxCalls(Number(event.target.value) || 30)}
          />
        </Field>
      </div>

      <div className="space-y-3">
        {roleDefinitions.map((definition) => {
          const member = members.find((item) => item.role === definition.role);
          if (!member) return null;
          return (
            <div
              key={definition.role}
              className="rounded-xl border border-app-line bg-app-surface p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-sm font-semibold text-app-text">{definition.label}</h3>
                    {definition.required ? (
                      <Badge tone="info">必选</Badge>
                    ) : (
                      <Badge tone="neutral">可选</Badge>
                    )}
                    {member.api_key_configured && (
                      <Badge tone="success">
                        <KeyRound className="mr-1 h-3 w-3" />
                        密钥已配置
                      </Badge>
                    )}
                  </div>
                  <p className="mt-1 text-xs text-app-muted">{definition.description}</p>
                </div>
                <label className="inline-flex cursor-pointer items-center gap-2 text-xs text-app-muted">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-app-lineStrong text-brand focus:ring-brand/30"
                    checked={member.enabled}
                    disabled={definition.required}
                    onChange={(event) =>
                      patchMember(definition.role, { enabled: event.target.checked })
                    }
                  />
                  启用
                </label>
              </div>

              {member.enabled && (
                <div className="mt-3 grid gap-3 sm:grid-cols-[1fr_1.4fr_1fr]">
                  <Field label="模型">
                    <Input
                      value={member.model}
                      onChange={(event) => patchMember(definition.role, { model: event.target.value })}
                      placeholder="gpt-4o-mini"
                    />
                  </Field>
                  <Field label="API Base">
                    <Input
                      value={member.api_base}
                      onChange={(event) =>
                        patchMember(definition.role, { api_base: event.target.value })
                      }
                      placeholder="https://api.openai.com/v1"
                    />
                  </Field>
                  <Field
                    label="API Key"
                    hint={member.api_key_configured ? "留空保持不变" : "仅本地加密保存"}
                  >
                    <Input
                      type="password"
                      value={member.api_key ?? ""}
                      onChange={(event) =>
                        patchMember(definition.role, { api_key: event.target.value })
                      }
                      placeholder={member.api_key_configured ? "••••••••" : "sk-…"}
                    />
                  </Field>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="flex items-start gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-xs leading-5 text-blue-800">
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
        评测团队会真实调用模型。每次运行受最大轮次、超时和调用预算限制；密钥不会回显。
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex justify-end gap-2 border-t border-app-line pt-4">
        <Button type="button" variant="ghost" onClick={onCancel}>
          取消
        </Button>
        <Button type="submit" loading={saving}>
          {team ? "保存修改" : "创建评测团队"}
        </Button>
      </div>
    </form>
  );
}
