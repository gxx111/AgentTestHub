import { cn } from "@/lib/utils";

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      role="status"
      aria-label="加载中"
      className={cn(
        "inline-block h-5 w-5 animate-spin rounded-full border-2 border-current border-r-transparent",
        className,
      )}
    />
  );
}

export function FullPageSpinner({ label = "正在加载工作区…" }: { label?: string }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-app-bg text-app-muted">
      <Spinner className="h-6 w-6 text-brand" />
      <p className="text-sm">{label}</p>
    </div>
  );
}
