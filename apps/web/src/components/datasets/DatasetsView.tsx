"use client";

import React, { useState, useEffect } from "react";
import {
  Database,
  Plus,
  Trash2,
  FolderOpen,
  FileCode2,
  ListPlus,
  CheckCircle2,
  Tag,
  X,
  Layers,
  ChevronRight,
  ChevronDown,
} from "lucide-react";

export interface DatasetItem {
  id: string;
  name: string;
  domain: string;
  description: string;
  init_sql?: string;
  case_count?: number;
  cases?: Array<{
    id: string;
    title: string;
    category: string;
    prompt: string;
    description: string;
    expected_state?: any[];
    rubrics?: any[];
  }>;
}

export function DatasetsView() {
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
  const [selectedDatasetDetail, setSelectedDatasetDetail] = useState<DatasetItem | null>(null);
  const [isNewDatasetModalOpen, setIsNewDatasetModalOpen] = useState(false);
  const [isNewCaseModalOpen, setIsNewCaseModalOpen] = useState(false);

  // 新建数据集表单
  const [newDsName, setNewDsName] = useState("");
  const [newDsDomain, setNewDsDomain] = useState("general");
  const [newDsDesc, setNewDsDesc] = useState("");
  const [newDsSql, setNewDsSql] = useState("");

  // 新建用例表单
  const [newCaseTitle, setNewCaseTitle] = useState("");
  const [newCaseCategory, setNewCaseCategory] = useState("happy_path");
  const [newCasePrompt, setNewCasePrompt] = useState("");
  const [newCaseDesc, setNewCaseDesc] = useState("");

  const fetchDatasets = async () => {
    try {
      const res = await fetch("http://localhost:8005/api/v1/datasets");
      if (res.ok) {
        const data = await res.json();
        setDatasets(data);
        if (data.length > 0 && !selectedDatasetId) {
          setSelectedDatasetId(data[0].id);
        }
      }
    } catch (_) {}
  };

  const fetchDatasetDetail = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8005/api/v1/datasets/${id}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedDatasetDetail(data);
      }
    } catch (_) {}
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  useEffect(() => {
    if (selectedDatasetId) {
      fetchDatasetDetail(selectedDatasetId);
    }
  }, [selectedDatasetId]);

  const handleCreateDataset = async () => {
    if (!newDsName.trim()) return;
    try {
      const res = await fetch("http://localhost:8005/api/v1/datasets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workspace_id: "ws_primary",
          name: newDsName,
          domain: newDsDomain,
          description: newDsDesc,
          init_sql: newDsSql,
        }),
      });
      if (res.ok) {
        setIsNewDatasetModalOpen(false);
        setNewDsName("");
        setNewDsDesc("");
        setNewDsSql("");
        fetchDatasets();
      }
    } catch (_) {}
  };

  const handleCreateCase = async () => {
    if (!selectedDatasetId || !newCasePrompt.trim()) return;
    try {
      const res = await fetch(`http://localhost:8005/api/v1/datasets/${selectedDatasetId}/cases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: newCaseTitle || "自定义业务测试用例",
          category: newCaseCategory,
          prompt: newCasePrompt,
          description: newCaseDesc,
          expected_state: [],
          rubrics: [
            {
              id: "chk_compliance",
              dimension: "通用业务",
              question: "Agent 表现是否符合业务流程预期？",
              expected_verdict: "YES",
              is_fatal: false,
            },
          ],
        }),
      });
      if (res.ok) {
        setIsNewCaseModalOpen(false);
        setNewCaseTitle("");
        setNewCasePrompt("");
        setNewCaseDesc("");
        if (selectedDatasetId) {
          fetchDatasetDetail(selectedDatasetId);
          fetchDatasets();
        }
      }
    } catch (_) {}
  };

  const handleDeleteCase = async (caseId: string) => {
    if (!confirm("确认删除该用例？")) return;
    try {
      await fetch(`http://localhost:8005/api/v1/cases/${caseId}`, { method: "DELETE" });
      if (selectedDatasetId) {
        fetchDatasetDetail(selectedDatasetId);
        fetchDatasets();
      }
    } catch (_) {}
  };

  return (
    <div className="w-full space-y-5 font-sans">
      {/* 顶部标题栏 */}
      <div className="glass-panel rounded-2xl p-5 border border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-pulse/15 text-emerald-pulse border border-emerald-pulse/30 uppercase font-bold">
              数据集 · CRUD
            </span>
            <h2 className="text-sm font-bold text-slate-100 font-mono tracking-tight">
              通用评测数据集与用例工作台 (Datasets & Test Cases)
            </h2>
          </div>
          <p className="text-xs text-slate-400 font-sans">
            支持针对任意领域（电商、金融、政企、医疗、代码）动态新增评测集，管理与维护测试用例库
          </p>
        </div>

        <button
          onClick={() => setIsNewDatasetModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-pulse to-teal-400 text-obsidian-950 font-mono text-xs font-bold shadow-lg shadow-emerald-pulse/20 hover:scale-[1.02] active:scale-[0.98] transition-all shrink-0"
        >
          <Plus className="w-4 h-4" /> 新建评测数据集 (New Dataset)
        </button>
      </div>

      {/* 主体两栏布局：左侧数据集列表，右侧用例列表 */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* 左侧数据集列表 */}
        <div className="lg:col-span-4 space-y-3">
          <div className="text-xs font-bold text-slate-300 font-mono flex items-center justify-between px-1">
            <span>数据集目录 ({datasets.length})</span>
          </div>

          <div className="space-y-2">
            {datasets.map((d) => {
              const isSelected = selectedDatasetId === d.id;
              return (
                <button
                  key={d.id}
                  onClick={() => setSelectedDatasetId(d.id)}
                  className={`w-full text-left p-4 rounded-xl border transition-all text-xs ${
                    isSelected
                      ? "glass-panel border-emerald-pulse/50 bg-emerald-pulse/5 shadow-lg shadow-emerald-pulse/10"
                      : "glass-card hover:border-white/20 text-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">
                      {d.domain}
                    </span>
                    <span className="text-[11px] font-mono text-emerald-pulse font-bold">
                      {d.case_count ?? 0} 个 Cases
                    </span>
                  </div>
                  <h3 className="font-bold text-slate-100 mb-1">{d.name}</h3>
                  <p className="text-[11px] text-slate-400 line-clamp-2">{d.description || "无描述"}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* 右侧用例详情与添加用例 */}
        <div className="lg:col-span-8 glass-panel rounded-2xl p-6 border border-white/10 space-y-5">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div>
              <span className="text-[10px] font-mono text-cyber-cyan block mb-1">
                {selectedDatasetDetail?.id}
              </span>
              <h2 className="text-sm font-bold text-slate-100 font-mono">
                {selectedDatasetDetail?.name || "选择数据集"}
              </h2>
            </div>

            <button
              onClick={() => setIsNewCaseModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyber-cyan/15 text-cyber-cyan border border-cyber-cyan/30 text-xs font-mono font-bold hover:bg-cyber-cyan/25 transition-all"
            >
              <Plus className="w-3.5 h-3.5" /> 添加测试用例 (Add Case)
            </button>
          </div>

          {/* 测试用例列表 */}
          <div className="space-y-3">
            {selectedDatasetDetail?.cases && selectedDatasetDetail.cases.length > 0 ? (
              selectedDatasetDetail.cases.map((c) => (
                <div
                  key={c.id}
                  className="p-4 rounded-xl bg-obsidian-950/80 border border-white/10 space-y-2 hover:border-white/20 transition-all text-xs"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-200">{c.title}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/5 text-slate-400">
                        {c.category}
                      </span>
                    </div>

                    <button
                      onClick={() => handleDeleteCase(c.id)}
                      className="text-slate-500 hover:text-red-400 p-1"
                      title="删除此用例"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <p className="text-slate-300 font-sans leading-relaxed">"{c.prompt}"</p>
                  <span className="text-[11px] text-slate-500 font-mono block">
                    预期: {c.description || "无详细描述"}
                  </span>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-slate-500 font-mono text-xs">
                当前数据集暂无用例，点击右上角「添加测试用例」创建第一条用例。
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 新建数据集模态框 */}
      {isNewDatasetModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="w-full max-w-lg rounded-2xl glass-panel border border-white/15 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-sm font-bold text-white font-mono">创建通用评测数据集</h3>
              <button onClick={() => setIsNewDatasetModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div>
                <label className="text-slate-300 block mb-1">数据集名称:</label>
                <input
                  type="text"
                  value={newDsName}
                  onChange={(e) => setNewDsName(e.target.value)}
                  placeholder="例如: 医疗导诊 Agent 专病筛查数据集"
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white"
                />
              </div>

              <div>
                <label className="text-slate-300 block mb-1">业务领域 (Domain):</label>
                <select
                  value={newDsDomain}
                  onChange={(e) => setNewDsDomain(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white"
                >
                  <option value="general">通用业务 (General)</option>
                  <option value="ecommerce">电商客服 (Ecommerce)</option>
                  <option value="coding">代码重构与安全 (Coding)</option>
                  <option value="finance">金融风控与信贷 (Finance)</option>
                  <option value="medical">医疗健康问诊 (Medical)</option>
                  <option value="custom">私有垂直领域 (Custom)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 block mb-1">场景描述说明:</label>
                <input
                  type="text"
                  value={newDsDesc}
                  onChange={(e) => setNewDsDesc(e.target.value)}
                  placeholder="简述该数据集的评测重点"
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-slate-200"
                />
              </div>

              <div>
                <label className="text-slate-300 block mb-1">沙盒初始化 SQL (可选，模拟真实数据库):</label>
                <textarea
                  value={newDsSql}
                  onChange={(e) => setNewDsSql(e.target.value)}
                  placeholder="CREATE TABLE patients (...); INSERT INTO patients ...;"
                  rows={3}
                  className="w-full bg-black/50 border border-white/10 rounded-lg p-2.5 text-slate-300 font-mono text-[11px]"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
              <button
                type="button"
                onClick={() => setIsNewDatasetModalOpen(false)}
                className="px-4 py-2 rounded-xl glass-card text-xs text-slate-400 hover:text-white"
              >
                取消
              </button>
              <button
                type="button"
                onClick={handleCreateDataset}
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-pulse to-teal-400 text-obsidian-950 font-bold text-xs"
              >
                确认创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 新建用例模态框 */}
      {isNewCaseModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="w-full max-w-lg rounded-2xl glass-panel border border-white/15 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-sm font-bold text-white font-mono">添加测试用例 (Add Case)</h3>
              <button onClick={() => setIsNewCaseModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div>
                <label className="text-slate-300 block mb-1">用例标题:</label>
                <input
                  type="text"
                  value={newCaseTitle}
                  onChange={(e) => setNewCaseTitle(e.target.value)}
                  placeholder="例如: 疑似急危重症患者前置挂号分流"
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white"
                />
              </div>

              <div>
                <label className="text-slate-300 block mb-1">分类:</label>
                <select
                  value={newCaseCategory}
                  onChange={(e) => setNewCaseCategory(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-white"
                >
                  <option value="happy_path">标准正常流 (Happy Path)</option>
                  <option value="edge_case">边界流/风控拦截 (Edge Case)</option>
                  <option value="security_redline">安全红线/越权攻击 (Security)</option>
                  <option value="sop_compliance">SOP 强流程遵循 (SOP Compliance)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 block mb-1">测试 Prompt 输入 (考官第一句话):</label>
                <textarea
                  value={newCasePrompt}
                  onChange={(e) => setNewCasePrompt(e.target.value)}
                  placeholder="用户/考官说的第一句话..."
                  rows={2}
                  className="w-full bg-black/50 border border-white/10 rounded-lg p-2.5 text-white"
                />
              </div>

              <div>
                <label className="text-slate-300 block mb-1">预期行为与产出描述:</label>
                <input
                  type="text"
                  value={newCaseDesc}
                  onChange={(e) => setNewCaseDesc(e.target.value)}
                  placeholder="简述 Agent 应当如何应对或调用工具"
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-slate-300"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
              <button
                type="button"
                onClick={() => setIsNewCaseModalOpen(false)}
                className="px-4 py-2 rounded-xl glass-card text-xs text-slate-400 hover:text-white"
              >
                取消
              </button>
              <button
                type="button"
                onClick={handleCreateCase}
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyber-cyan to-cyber-azure text-obsidian-950 font-bold text-xs"
              >
                确认添加
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
