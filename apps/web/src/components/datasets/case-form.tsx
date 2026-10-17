"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { api } from "@/lib/api";
import type { TestCase } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";

const categories = [
  { value: "happy_path", label: "标准流程" },
  { value: "edge_case", label: "边界条件" },
  { value: "security_redline", label: "安全红线" },
  { value: "sop_compliance", label: "SOP 合规" },
  { value: "mas_deadlock", label: "多 Agent 协作" },
];

const defaultRubrics = JSON.stringify(
  [
    {
      id: "chk_task_completed",
      dimension: "任务完成",
      question: "Agent 是否完成了用户请求的业务目标？",
      expected_verdict: "YES",
      is_fatal: false,
    },
  ],
  null,
  2,
);

export function CaseForm({
  datasetId,
  testCase,
  onSaved,
  onCancel,
}: {
  datasetId: string;
  testCase: TestCase | null;
  onSaved: () => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState(testCase?.title ?? "");
  const [category, setCategory] = useState(testCase?.category ?? "happy_path");
  const [prompt, setPrompt] = useState(testCase?.prompt ?? "");
  const [description, setDescription] = useState(testCase?.description ?? "");
  const [expectedState, setExpectedState] = useState(
    JSON.stringify(testCase?.expected_state ?? [], null, 2),
  );
  const [rubrics, setRubrics] = useState(
    JSON.stringify(testCase?.rubrics ?? JSON.parse(defaultRubrics), null, 2),
  );
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!title.trim() || !prompt.trim()) {
      setError("请填写用例标题和初始任务");
      return;
    }

    let expected: unknown;
    let rubricList: unknown;
    try {
      expected = expectedState.trim() ? JSON.parse(expectedState) : [];
      rubricList = rubrics.trim() ? JSON.parse(rubrics) : [];
    } catch {
      setError("预期状态或 Rubric 不是合法 JSON");
      return;
    }
    if (!Array.isArray(expected) || !Array.isArray(rubricList)) {
      setError("预期状态和 Rubric 都必须是 JSON 数组");
      return;
    }

    setSaving(true);
    try {
      const payload = {
        title: title.trim(),
        category,
        prompt: prompt.trim(),
        description: description.trim(),
        expected_state: expected,
        rubrics: rubricList,
      };
      if (testCase) await api.updateCase(testCase.id, payload);
      else await api.addCase(datasetId, payload);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="grid gap-4 sm:grid-cols-[1fr_180px]">
        <Field label="用例标题" required>
          <Input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="例如：无凭证退款请求应被拒绝"
          />
        </Field>
        <Field label="类别">
          <Select value={category} onChange={(event) => setCategory(event.target.value)}>
            {categories.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </Select>
        </Field>
      </div>

      <Field label="初始任务 / 用户输入" required>
        <Textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          rows={3}
          placeholder="用户会对 Agent 说的第一句话…"
        />
      </Field>

      <Field label="预期行为说明">
        <Textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          rows={2}
          placeholder="这条用例要验证什么？"
        />
      </Field>

      <Field
        label="预期世界状态（JSON 数组）"
        hint={'例如 [{"target_identifier":"orders","condition":{"order_id":"ORD_1"},"expected_values":{"status":"CANCELLED"}}]'}
      >
        <Textarea
          className="font-mono text-xs"
          value={expectedState}
          onChange={(event) => setExpectedState(event.target.value)}
          rows={6}
        />
      </Field>

      <Field
        label="Rubric（JSON 数组）"
        hint="每条 Rubric 是一个可用 YES/NO 回答的事实检查项；expected_verdict 是正确答案。"
      >
        <Textarea
          className="font-mono text-xs"
          value={rubrics}
          onChange={(event) => setRubrics(event.target.value)}
          rows={8}
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
          {testCase ? "保存修改" : "添加用例"}
        </Button>
      </div>
    </form>
  );
}
