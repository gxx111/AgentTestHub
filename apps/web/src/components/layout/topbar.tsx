"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { BookOpen, Menu } from "lucide-react";
import { api } from "@/lib/api";

const labels: Array<[string, string]> = [
  ["/overview", "概览"],
  ["/evaluations/experiments", "评测实验 / 实验详情"],
  ["/evaluations/runs", "评测实验 / 运行详情"],
  ["/evaluations", "评测实验"],
  ["/agents", "Agent 资产"],
  ["/datasets", "数据集"],
  ["/teams", "评测团队"],
  ["/settings", "工作区设置"],
];

function currentLabel(pathname: string): string {
  for (const [prefix, label] of labels) {
    if (pathname === prefix || pathname.startsWith(`${prefix}/`)) return label;
  }
  return "工作台";
}

export function Topbar({ onMenu }: { onMenu: () => void }) {
  const pathname = usePathname();
  const [health, setHealth] = useState<"checking" | "ok" | "down">("checking");

  useEffect(() => {
    let cancelled = false;
    api
      .health()
      .then(() => {
        if (!cancelled) setHealth("ok");
      })
      .catch(() => {
        if (!cancelled) setHealth("down");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-4 border-b border-app-line bg-app-surface/95 px-4 backdrop-blur sm:px-6 lg:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={onMenu}
          className="rounded-lg p-2 text-app-muted hover:bg-app-subtle hover:text-app-text lg:hidden"
          aria-label="打开导航"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="min-w-0">
          <p className="text-[11px] text-app-muted">Agent Release Gate</p>
          <h2 className="truncate text-sm font-semibold text-app-text">{currentLabel(pathname)}</h2>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <span className="hidden items-center gap-2 rounded-full border border-app-line bg-app-subtle px-3 py-1.5 text-xs text-app-muted sm:inline-flex">
          <span
            className={
              health === "ok"
                ? "h-2 w-2 rounded-full bg-emerald-500"
                : health === "down"
                  ? "h-2 w-2 rounded-full bg-red-500"
                  : "h-2 w-2 animate-pulse rounded-full bg-amber-500"
            }
          />
          {health === "ok" ? "API 已连接" : health === "down" ? "API 不可用" : "检查 API…"}
        </span>
        <a
          href="https://github.com/gxx111/AgentTestHub/tree/main/docs"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs text-app-muted hover:bg-app-subtle hover:text-app-text"
        >
          <BookOpen className="h-4 w-4" />
          <span className="hidden sm:inline">文档</span>
        </a>
      </div>
    </header>
  );
}
