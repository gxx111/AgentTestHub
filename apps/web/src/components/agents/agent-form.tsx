"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { PlugZap } from "lucide-react";
import { api } from "@/lib/api";
import type { Agent, ToolDefinition } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";

const defaultTool: ToolDefinition = {
  name: "db_execute",
  description: "在隔离评测沙盒中执行受控 SQL；危险语句由沙盒拦截。",
  parameters_schema: {
    type: "object",
    properties: {
      sql: { type: "string", description: "要执行的 SQL 语句" },
      params: { type: "array", description: "SQL 参数数组", items: { type: "string" } },
    },
    required: ["sql"],
  },
};

const agentTypes = [
  { value: "litellm", label: "模型 Agent（LiteLLM / OpenAI 兼容）" },
  { value: "smolagents", label: "Agent 运行时（smolagents）" },
  { value: "webhook", label: "外部 Webhook" },
  { value: "mock", label: "本地 Mock（仅流程验证）" },
];

export function AgentForm({
  agent,
  workspaceId,
  onSaved,
  onCancel,
}: {
  agent: Agent | null;
  workspaceId: string;
  onSaved: () => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(agent?.name ?? "");
  const [agentType, setAgentType] = useState(agent?.agent_type ?? "litellm");
  const [modelName, setModelName] = useState(agent?.model_name ?? "");
  const [description, setDescription] = useState(agent?.description ?? "");
  const [systemPrompt, setSystemPrompt] = useState(agent?.system_prompt ?? "");
  const [apiBase, setApiBase] = useState(String(agent?.config?.api_base ?? ""));
  const [apiKey, setApiKey] = useState("");
  const [webhookUrl, setWebhookUrl] = useState(String(agent?.config?.webhook_url ?? ""));
  const [toolsJson, setToolsJson] = useState(JSON.stringify(agent?.tools ?? [], null, 2));
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const isModelAgent = agentType === "litellm" || agentType === "smolagents";
  const keyConfigured = Boolean(agent?.config?.api_key_configured);

  function parseTools(): ToolDefinition[] {
    const parsed = toolsJson.trim() ? (JSON.parse(toolsJson) as unknown) : [];
    if (!Array.isArray(parsed)) throw new Error("工具定义必须是 JSON 数组");
    return parsed as ToolDefinition[];
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!name.trim()) {
      setError("请填写 Agent 名称");
      return;
    }
    if (isModelAgent && !modelName.trim()) {
      setError("请填写模型名称");
      return;
    }
    if (agentType === "webhook" && !webhookUrl.trim()) {
      setError("请填写 Webhook URL");
      return;
    }

    let tools: ToolDefinition[];
    try {
      tools = parseTools();
    } catch (err) {
      setError(err instanceof Error ? err.message : "工具 JSON 格式不正确");
      return;
    }
    if (agentType === "smolagents" && tools.length === 0) tools = [defaultTool];

    const config: Record<string, unknown> = {};
    if (agentType === "webhook") {
      config.webhook_url = webhookUrl.trim();
    } else if (isModelAgent) {
      if (apiBase.trim()) config.api_base = apiBase.trim();
      if (apiKey.trim()) config.api_key = apiKey.trim();
      config.temperature = 0;
    }

    const payload: Record<string, unknown> = {
      name: name.trim(),
      agent_type: agentType,
      model_name: modelName.trim() || "mock",
      description: description.trim(),
      system_prompt: systemPrompt,
      tools,
      config,
    };
    if (!agent) payload.workspace_id = workspaceId;

    setSaving(true);
    try {
      if (agent) await api.updateAgent(agent.id, payload);
      else await api.createAgent(payload);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    setTestResult(null);
    setTesting(true);
    try {
      const result = await api.testConnection({
        agent_type: agentType,
        model_name: modelName.trim() || "mock",
        api_key: apiKey.trim() || undefined,
        api_base: apiBase.trim() || undefined,
        webhook_url: webhookUrl.trim() || undefined,
      });
      setTestResult(
        typeof result.message === "string"
          ? result.message
          : result.status === "ok"
            ? "连接正常"
            : "连接失败",
      );
    } catch (err) {
      setTestResult(err instanceof Error ? err.message : "连接测试失败");
    } finally {
      setTesting(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Agent 名称" required>
          <Input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="例如：退款客服 Agent"
          />
        </Field>
        <Field label="接入类型" required>
          <Select value={agentType} onChange={(event) => setAgentType(event.target.value)}>
            {agentTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
            <option value="mas_team" disabled>
              多 Agent 团队（实验性，暂不可执行）
            </option>
          </Select>
        </Field>
      </div>

      <Field label="模型 / 版本" hint="LiteLLM 会按模型名前缀自动推断供应商">
        <Input
          value={modelName}
          onChange={(event) => setModelName(event.target.value)}
          placeholder="例如：qwen-plus / gpt-4o-mini / deepseek-chat"
        />
      </Field>

      {isModelAgent && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="OpenAI 兼容 API Base">
            <Input
              value={apiBase}
              onChange={(event) => setApiBase(event.target.value)}
              placeholder="https://gateway.example.com/v1"
            />
          </Field>
          <Field
            label="API Key"
            hint={keyConfigured ? "已保存密钥；留空保持不变" : "本地模型通常可留空"}
          >
            <Input
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder={keyConfigured ? "••••••••（已配置）" : "sk-…"}
            />
          </Field>
        </div>
      )}

      {agentType === "webhook" && (
        <Field label="Webhook URL" required hint="评测时会向该端点 POST prompt / task_id / tools">
          <Input
            value={webhookUrl}
            onChange={(event) => setWebhookUrl(event.target.value)}
            placeholder="https://agent.example.com/evaluate"
          />
        </Field>
      )}

      <Field label="描述">
        <Textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          rows={2}
          placeholder="这个 Agent 负责什么业务？"
        />
      </Field>

      <Field label="System Prompt">
        <Textarea
          value={systemPrompt}
          onChange={(event) => setSystemPrompt(event.target.value)}
          rows={4}
          placeholder="你是一个专业的业务助理…"
        />
      </Field>

      <details className="rounded-lg border border-app-line bg-app-subtle p-3">
        <summary className="cursor-pointer text-sm font-medium text-app-text">
          高级：工具定义（JSON）
        </summary>
        <p className="mt-1 text-xs text-app-muted">
          smolagents 未填写时会自动注入内置 db_execute 工具。其他类型可留空。
        </p>
        <Textarea
          className="mt-3 font-mono text-xs"
          value={toolsJson}
          onChange={(event) => setToolsJson(event.target.value)}
          rows={8}
        />
      </details>

      {testResult && (
        <div className="rounded-lg border border-app-line bg-app-subtle px-3 py-2 text-sm text-app-text">
          {testResult}
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-app-line pt-4">
        <Button
          type="button"
          variant="secondary"
          loading={testing}
          icon={<PlugZap className="h-4 w-4" />}
          onClick={() => void handleTest()}
        >
          测试连接
        </Button>
        <div className="flex items-center gap-2">
          <Button type="button" variant="ghost" onClick={onCancel}>
            取消
          </Button>
          <Button type="submit" loading={saving}>
            {agent ? "保存修改" : "创建 Agent"}
          </Button>
        </div>
      </div>
    </form>
  );
}
