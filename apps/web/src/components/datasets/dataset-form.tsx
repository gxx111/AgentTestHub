"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { api } from "@/lib/api";
import type { Dataset } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";

const domains = [
  { value: "general", label: "通用" },
  { value: "ecommerce", label: "电商" },
  { value: "finance", label: "金融" },
  { value: "coding", label: "代码" },
  { value: "security", label: "安全" },
];

export function DatasetForm({
  dataset,
  workspaceId,
  onSaved,
  onCancel,
}: {
  dataset: Dataset | null;
  workspaceId: string;
  onSaved: (datasetId?: string) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(dataset?.name ?? "");
  const [domain, setDomain] = useState(dataset?.domain ?? "general");
  const [description, setDescription] = useState(dataset?.description ?? "");
  const [initSql, setInitSql] = useState(dataset?.init_sql ?? "");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!name.trim()) {
      setError("请填写数据集名称");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        name: name.trim(),
        domain,
        description: description.trim(),
        init_sql: initSql,
      };
      if (dataset) {
        await api.updateDataset(dataset.id, payload);
        onSaved(dataset.id);
      } else {
        const result = await api.createDataset({ ...payload, workspace_id: workspaceId });
        onSaved(result.dataset_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="数据集名称" required>
          <Input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="例如：退款回归集"
          />
        </Field>
        <Field label="业务域">
          <Select value={domain} onChange={(event) => setDomain(event.target.value)}>
            {domains.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </Select>
        </Field>
      </div>

      <Field label="描述">
        <Textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          rows={2}
          placeholder="覆盖哪些业务场景与风险？"
        />
      </Field>

      <Field
        label="初始化 SQL"
        hint="可选。评测每个用例前会在隔离沙盒中执行，用于建表与种子数据。"
      >
        <Textarea
          className="font-mono text-xs"
          value={initSql}
          onChange={(event) => setInitSql(event.target.value)}
          rows={8}
          placeholder={"CREATE TABLE orders (...);\nINSERT INTO orders VALUES (...);"}
        />
      </Field>

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
          {dataset ? "保存修改" : "创建数据集"}
        </Button>
      </div>
    </form>
  );
}
