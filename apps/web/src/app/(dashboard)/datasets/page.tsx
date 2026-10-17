"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Database,
  FlaskConical,
  Pencil,
  Plus,
  Search,
  Trash2,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useResource } from "@/hooks/use-resource";
import type { Dataset, DatasetDetail, TestCase } from "@/lib/types";
import { categoryLabel, formatDate } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/field";
import { Modal } from "@/components/ui/modal";
import { PageHeader } from "@/components/ui/page-header";
import { Spinner } from "@/components/ui/spinner";
import { useToast } from "@/components/ui/toast";
import { DatasetForm } from "@/components/datasets/dataset-form";
import { CaseForm } from "@/components/datasets/case-form";

export default function DatasetsPage() {
  const { workspaceId } = useAuth();
  const router = useRouter();
  const toast = useToast();
  const datasets = useResource<Dataset[]>(
    `datasets:${workspaceId}`,
    () => api.listDatasets(workspaceId as string),
    Boolean(workspaceId),
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [datasetModal, setDatasetModal] = useState(false);
  const [editingDataset, setEditingDataset] = useState<Dataset | null>(null);
  const [caseModal, setCaseModal] = useState(false);
  const [editingCase, setEditingCase] = useState<TestCase | null>(null);

  const detail = useResource<DatasetDetail>(
    `dataset:${selectedId}`,
    () => api.getDataset(selectedId as string),
    Boolean(selectedId),
  );

  useEffect(() => {
    const list = datasets.data ?? [];
    if (list.length === 0) {
      setSelectedId(null);
      return;
    }
    if (!selectedId || !list.some((item) => item.id === selectedId)) {
      setSelectedId(list[0].id);
    }
  }, [datasets.data, selectedId]);

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return datasets.data ?? [];
    return (datasets.data ?? []).filter(
      (dataset) =>
        dataset.name.toLowerCase().includes(query) ||
        dataset.domain.toLowerCase().includes(query) ||
        dataset.description?.toLowerCase().includes(query),
    );
  }, [datasets.data, search]);

  async function removeDataset(dataset: Dataset) {
    if (!window.confirm(`删除数据集「${dataset.name}」及其所有用例？`)) return;
    try {
      await api.deleteDataset(dataset.id);
      setSelectedId(null);
      toast.push("数据集已删除", "success");
      await datasets.refresh();
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "删除失败", "error");
    }
  }

  async function removeCase(testCase: TestCase) {
    if (!window.confirm(`删除用例「${testCase.title}」？`)) return;
    try {
      await api.deleteCase(testCase.id);
      toast.push("用例已删除", "success");
      await Promise.all([detail.refresh(), datasets.refresh()]);
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "删除失败", "error");
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="资产"
        title="数据集"
        description="把真实业务任务、边界条件和世界状态断言组织成可复用的评测集。"
        actions={
          <Button
            icon={<Plus className="h-4 w-4" />}
            onClick={() => {
              setEditingDataset(null);
              setDatasetModal(true);
            }}
          >
            创建数据集
          </Button>
        }
      />

      {datasets.error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {datasets.error}
          <button className="ml-3 underline" onClick={() => void datasets.refresh()}>
            重试
          </button>
        </div>
      )}

      <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
        <aside className="rounded-xl border border-app-line bg-app-surface p-3">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-app-muted" />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="搜索数据集"
              className="pl-9"
            />
          </div>

          <div className="mt-3 space-y-1">
            {datasets.loading ? (
              <div className="flex justify-center py-10">
                <Spinner className="h-5 w-5 text-brand" />
              </div>
            ) : filtered.length === 0 ? (
              <p className="px-3 py-8 text-center text-sm text-app-muted">没有匹配的数据集</p>
            ) : (
              filtered.map((dataset) => (
                <button
                  key={dataset.id}
                  type="button"
                  onClick={() => setSelectedId(dataset.id)}
                  className={
                    selectedId === dataset.id
                      ? "w-full rounded-lg border border-brand/30 bg-brand-soft px-3 py-3 text-left"
                      : "w-full rounded-lg border border-transparent px-3 py-3 text-left hover:bg-app-subtle"
                  }
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-medium text-app-text">{dataset.name}</span>
                    <Badge>{dataset.case_count ?? 0} 用例</Badge>
                  </div>
                  <p className="mt-1 truncate text-xs text-app-muted">
                    {dataset.description || "未填写描述"}
                  </p>
                  <p className="mt-1 text-[11px] text-app-muted">
                    {dataset.domain} · {formatDate(dataset.created_at)}
                  </p>
                </button>
              ))
            )}
          </div>
        </aside>

        <section className="min-w-0">
          {!selectedId ? (
            <EmptyState
              icon={<Database className="h-8 w-8" />}
              title="还没有数据集"
              description="创建一个数据集，然后添加用例、预期状态和 Rubric。"
              action={
                <Button
                  icon={<Plus className="h-4 w-4" />}
                  onClick={() => {
                    setEditingDataset(null);
                    setDatasetModal(true);
                  }}
                >
                  创建数据集
                </Button>
              }
            />
          ) : detail.loading ? (
            <div className="flex justify-center py-20">
              <Spinner className="h-6 w-6 text-brand" />
            </div>
          ) : detail.error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {detail.error}
              <button className="ml-3 underline" onClick={() => void detail.refresh()}>
                重试
              </button>
            </div>
          ) : detail.data ? (
            <div className="space-y-5">
              <div className="rounded-xl border border-app-line bg-app-surface p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="text-lg font-semibold text-app-text">{detail.data.name}</h2>
                      <Badge tone="info">{detail.data.domain}</Badge>
                      <Badge>{detail.data.cases.length} 用例</Badge>
                    </div>
                    <p className="mt-2 max-w-2xl text-sm text-app-muted">
                      {detail.data.description || "未填写描述"}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={<FlaskConical className="h-3.5 w-3.5" />}
                      onClick={() => router.push(`/evaluations?dataset=${detail.data?.id}`)}
                    >
                      去评测
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={<Pencil className="h-3.5 w-3.5" />}
                      onClick={() => {
                        setEditingDataset(detail.data);
                        setDatasetModal(true);
                      }}
                    >
                      编辑
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={<Trash2 className="h-3.5 w-3.5" />}
                      onClick={() => void removeDataset(detail.data as Dataset)}
                    >
                      删除
                    </Button>
                  </div>
                </div>

                {detail.data.init_sql && (
                  <details className="mt-4 rounded-lg border border-app-line bg-app-subtle p-3">
                    <summary className="cursor-pointer text-sm font-medium text-app-text">
                      查看初始化 SQL
                    </summary>
                    <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-xs leading-5 text-app-muted">
                      {detail.data.init_sql}
                    </pre>
                  </details>
                )}
              </div>

              <div className="rounded-xl border border-app-line bg-app-surface">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-app-line px-5 py-4">
                  <div>
                    <h3 className="text-sm font-semibold text-app-text">测试用例</h3>
                    <p className="mt-0.5 text-xs text-app-muted">
                      每条用例包含输入、预期世界状态和 Rubric。
                    </p>
                  </div>
                  <Button
                    size="sm"
                    icon={<Plus className="h-3.5 w-3.5" />}
                    onClick={() => {
                      setEditingCase(null);
                      setCaseModal(true);
                    }}
                  >
                    添加用例
                  </Button>
                </div>

                {detail.data.cases.length === 0 ? (
                  <div className="p-5">
                    <EmptyState
                      title="还没有用例"
                      description="添加第一条用例，定义用户输入、预期状态和检查项。"
                      action={
                        <Button
                          size="sm"
                          icon={<Plus className="h-3.5 w-3.5" />}
                          onClick={() => {
                            setEditingCase(null);
                            setCaseModal(true);
                          }}
                        >
                          添加用例
                        </Button>
                      }
                    />
                  </div>
                ) : (
                  <div className="divide-y divide-app-line">
                    {detail.data.cases.map((testCase) => (
                      <article key={testCase.id} className="px-5 py-4">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-2">
                              <h4 className="text-sm font-medium text-app-text">{testCase.title}</h4>
                              <Badge>{categoryLabel(testCase.category)}</Badge>
                              <Badge tone="info">{testCase.rubrics.length} Rubric</Badge>
                              <Badge>{testCase.expected_state.length} 状态断言</Badge>
                            </div>
                            <p className="mt-2 line-clamp-2 text-sm text-app-muted">
                              {testCase.prompt}
                            </p>
                            {testCase.description && (
                              <p className="mt-1 text-xs text-app-muted">{testCase.description}</p>
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              icon={<Pencil className="h-3.5 w-3.5" />}
                              onClick={() => {
                                setEditingCase(testCase);
                                setCaseModal(true);
                              }}
                            >
                              编辑
                            </Button>
                            <button
                              type="button"
                              aria-label="删除用例"
                              onClick={() => void removeCase(testCase)}
                              className="rounded-md p-2 text-app-muted hover:bg-red-50 hover:text-red-600"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </section>
      </div>

      <Modal
        open={datasetModal}
        onClose={() => setDatasetModal(false)}
        title={editingDataset ? "编辑数据集" : "创建数据集"}
        size="lg"
      >
        {workspaceId && (
          <DatasetForm
            dataset={editingDataset}
            workspaceId={workspaceId}
            onCancel={() => setDatasetModal(false)}
            onSaved={(datasetId) => {
              setDatasetModal(false);
              if (datasetId) setSelectedId(datasetId);
              toast.push(editingDataset ? "数据集已更新" : "数据集已创建", "success");
              void datasets.refresh();
              void detail.refresh();
            }}
          />
        )}
      </Modal>

      <Modal
        open={caseModal}
        onClose={() => setCaseModal(false)}
        title={editingCase ? "编辑用例" : "添加用例"}
        description="Rubric 与预期状态使用 JSON 编辑，保存前会校验格式。"
        size="xl"
      >
        {selectedId && (
          <CaseForm
            datasetId={selectedId}
            testCase={editingCase}
            onCancel={() => setCaseModal(false)}
            onSaved={() => {
              setCaseModal(false);
              toast.push(editingCase ? "用例已更新" : "用例已添加", "success");
              void detail.refresh();
              void datasets.refresh();
            }}
          />
        )}
      </Modal>
    </div>
  );
}
