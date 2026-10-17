import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 rounded-2xl border border-app-line bg-app-subtle/60 px-6 py-12 text-center",
        className,
      )}
    >
      {icon && (
        <div className="grid h-12 w-12 place-items-center rounded-2xl border border-app-line bg-app-surface text-brand shadow-sm">
          {icon}
        </div>
      )}
      <div>
        <h3 className="text-sm font-semibold text-app-text">{title}</h3>
        {description && (
          <p className="mx-auto mt-1.5 max-w-md text-xs leading-5 text-app-muted">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
}
