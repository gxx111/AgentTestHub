import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  note,
  icon,
  tone = "default",
}: {
  label: string;
  value: ReactNode;
  note?: ReactNode;
  icon?: ReactNode;
  tone?: "default" | "success" | "warning" | "danger";
}) {
  const accent =
    tone === "success"
      ? "text-emerald-600 bg-emerald-50"
      : tone === "warning"
        ? "text-amber-600 bg-amber-50"
        : tone === "danger"
          ? "text-red-600 bg-red-50"
          : "text-brand bg-brand-soft";

  return (
    <div className="rounded-xl border border-app-line bg-app-surface p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-app-muted">{label}</p>
        {icon && <span className={cn("rounded-lg p-2", accent)}>{icon}</span>}
      </div>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-app-text">{value}</p>
      {note && <p className="mt-1 text-xs text-app-muted">{note}</p>}
    </div>
  );
}
