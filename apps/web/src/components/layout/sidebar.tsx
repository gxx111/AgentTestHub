"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bot,
  Database,
  FlaskConical,
  LayoutDashboard,
  LogOut,
  Settings,
  ShieldCheck,
  Users,
  X,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

const sections = [
  {
    label: "工作台",
    items: [
      { href: "/overview", label: "概览", icon: LayoutDashboard },
      { href: "/evaluations", label: "评测实验", icon: FlaskConical },
    ],
  },
  {
    label: "资产",
    items: [
      { href: "/agents", label: "Agent 资产", icon: Bot },
      { href: "/datasets", label: "数据集", icon: Database },
      { href: "/teams", label: "评测团队", icon: Users },
    ],
  },
  {
    label: "治理",
    items: [{ href: "/settings", label: "工作区设置", icon: Settings }],
  },
];

export function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname();
  const { user, workspaces, workspaceId, switchWorkspace, logout } = useAuth();

  return (
    <>
      {open && (
        <button
          type="button"
          aria-label="关闭导航"
          className="fixed inset-0 z-30 bg-slate-950/50 lg:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-sidebar-line bg-sidebar text-slate-200 transition-transform duration-200",
          open ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        )}
      >
        <div className="flex h-16 items-center gap-3 border-b border-sidebar-line px-5">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-brand text-white">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-white">AgentTestHub</p>
            <p className="truncate text-[11px] text-sidebar-muted">Agent Release Gate</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-sidebar-muted hover:bg-white/10 hover:text-white lg:hidden"
            aria-label="关闭导航"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="border-b border-sidebar-line px-4 py-4">
          <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-sidebar-muted">
            工作区
          </label>
          <select
            value={workspaceId ?? ""}
            onChange={(event) => switchWorkspace(event.target.value)}
            className="w-full rounded-lg border border-sidebar-line bg-sidebar-subtle px-3 py-2 text-sm text-white outline-none focus:border-brand"
          >
            {workspaces.length === 0 && <option value="">无可用工作区</option>}
            {workspaces.map((workspace) => (
              <option key={workspace.id} value={workspace.id}>
                {workspace.name}
              </option>
            ))}
          </select>
        </div>

        <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4">
          {sections.map((section) => (
            <div key={section.label}>
              <p className="px-3 pb-2 text-[11px] font-medium uppercase tracking-wider text-sidebar-muted">
                {section.label}
              </p>
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const active =
                    pathname === item.href ||
                    (item.href !== "/overview" && pathname.startsWith(`${item.href}/`));
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={onClose}
                      className={cn(
                        "relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                        active
                          ? "bg-white/10 font-medium text-white"
                          : "text-slate-300 hover:bg-white/5 hover:text-white",
                      )}
                    >
                      {active && (
                        <span className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-blue-400" />
                      )}
                      <Icon className="h-4 w-4 shrink-0" />
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-sidebar-line p-3">
          <div className="flex items-center gap-3 rounded-lg px-2 py-2">
            <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-white/10 text-sm font-semibold text-white">
              {(user?.name || user?.email || "U").slice(0, 1).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-white">{user?.name || "未登录"}</p>
              <p className="truncate text-[11px] text-sidebar-muted">{user?.email}</p>
            </div>
            <button
              type="button"
              onClick={() => void logout()}
              title="退出登录"
              aria-label="退出登录"
              className="rounded-md p-1.5 text-sidebar-muted hover:bg-white/10 hover:text-white"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
