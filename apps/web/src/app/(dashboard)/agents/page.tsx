"use client";

import { useState } from "react";
import { Bot, Pencil, Plus, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useResource } from "@/hooks/use-resource";
import type { Agent } from "@/lib/types";
import { agentTypeLabel, formatDate } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Modal } from "@/components/ui/modal";
import { PageHeader } from "@/components/ui/page-header";
import { Spinner } from "@/components/ui/spinner";
import { useToast } from "@/components/ui/toast";
import { AgentForm } from "@/components/agents/agent-form";

export default function AgentsPage() {
  const { workspaceId } = useAuth();
  const toast = useToast();
  const agents = useResource<Agent[]>(
    `agents:${workspaceId}`,
    () => api.listAgents(workspaceId as string),
    Boolean(workspaceId),
  );
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Agent | null>(null);
  const agentList = agents.data ?? [];
  const modelAgentCount = agentList.filter(
    (agent) => agent.agent_type === "litellm" || agent.agent_type === "smolagents",
  ).length;
  const configuredKeyCount = agentList.filter((agent) => agent.config?.api_key_configured).length;

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(agent: Agent) {
    setEditing(agent);
    setModalOpen(true);
  }

  async function remove(agent: Agent) {
    if (!window.confirm(`删除 Agent「${agent.name}」？历史实验不会删除。`)) return;
    try {
      await api.deleteAgent(agent.id);
      toast.push("Agent 已删除", "success");
      await agents.refresh();
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "删除失败", "error");
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="资产"
        title="Agent 资产"
        description="注册被测 Agent，作为可复用的评测目标。当前支持模型、smolagents、Webhook 与 Mock。"
        actions={
          <Button icon={<Plus className="h-4 w-4" />} onClick={openCreate}>
            新增 Agent
          </Button>
        }
      />

      {agentList.length > 0 && (
        <div className="mb-5 grid gap-3 sm:grid-cols-3">
          {[
            { label: "总资产", value: agentList.length, note: "已注册" },
            { label: "模型类 Agent", value: modelAgentCount, note: "LiteLLM / smolagents" },
            { label: "密钥已配置", value: configuredKeyCount, note: "本地加密保存" },
          ].map((item) => (
            <div
              key={item.label}
              className="flex items-center justify-between rounded-xl border border-app-line bg-app-surface px-4 py-3"
            >
              <div>
                <p className="text-xs text-app-muted">{item.label}</p>
                <p className="mt-1 text-xl font-semibold text-app-text">{item.value}</p>
              </div>
              <p className="max-w-[45%] text-right text-[11px] leading-4 text-app-muted">
                {item.note}
              </p>
            </div>
          ))}
        </div>
      )}

      {agents.error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {agents.error}
          <button className="ml-3 underline" onClick={() => void agents.refresh()}>
            重试
          </button>
        </div>
      )}

      {agents.loading ? (
        <div className="flex justify-center py-20">
          <Spinner className="h-6 w-6 text-brand" />
        </div>
      ) : (agents.data ?? []).length === 0 ? (
        <EmptyState
          icon={<Bot className="h-8 w-8" />}
          title="还没有 Agent"
          description="先注册一个真实模型或 Webhook，之后就可以创建数据集并运行评测。"
          action={
            <Button icon={<Plus className="h-4 w-4" />} onClick={openCreate}>
              新增 Agent
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {(agents.data ?? []).map((agent) => (
            <article
              key={agent.id}
              className="flex flex-col rounded-xl border border-app-line bg-app-surface p-5"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="grid h-10 w-10 place-items-center rounded-lg bg-brand-soft text-brand">
                  <Bot className="h-5 w-5" />
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<Pencil className="h-3.5 w-3.5" />}
                    onClick={() => openEdit(agent)}
                  >
                    编辑
                  </Button>
                  <button
                    type="button"
                    aria-label="删除 Agent"
                    onClick={() => void remove(agent)}
                    className="rounded-md p-2 text-app-muted hover:bg-red-50 hover:text-red-600"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              <h2 className="mt-4 text-base font-semibold text-app-text">{agent.name}</h2>
              <p className="mt-1 line-clamp-2 min-h-10 text-sm leading-5 text-app-muted">
                {agent.description || "未填写描述"}
              </p>

              <div className="mt-3 flex flex-wrap gap-1.5">
                <Badge tone={agent.agent_type === "mas_team" ? "warning" : "info"}>
                  {agentTypeLabel(agent.agent_type)}
                </Badge>
                <Badge>{agent.model_name || "—"}</Badge>
                {agent.config?.api_key_configured && <Badge tone="success">密钥已配置</Badge>}
              </div>

              <div className="mt-4 space-y-1 border-t border-app-line pt-3 text-xs text-app-muted">
                <p>
                  API Base：
                  <span className="ml-1 font-mono text-app-text">
                    {String(agent.config?.api_base || agent.config?.webhook_url || "—")}
                  </span>
                </p>
                <p>创建于 {formatDate(agent.created_at)}</p>
              </div>
            </article>
          ))}
        </div>
      )}

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? "编辑 Agent" : "新增 Agent"}
        description="配置完成后可先用“测试连接”验证网关，再保存。"
        size="xl"
      >
        {workspaceId && (
          <AgentForm
            agent={editing}
            workspaceId={workspaceId}
            onCancel={() => setModalOpen(false)}
            onSaved={() => {
              setModalOpen(false);
              toast.push(editing ? "Agent 已更新" : "Agent 已创建", "success");
              void agents.refresh();
            }}
          />
        )}
      </Modal>
    </div>
  );
}
