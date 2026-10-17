import { cn } from "@/lib/utils";

export function ScoreRing({
  value,
  size = 128,
  label,
  tone = "brand",
}: {
  value: number;
  size?: number;
  label?: string;
  tone?: "brand" | "success" | "warning" | "danger";
}) {
  const clamped = Math.max(0, Math.min(1, Number.isFinite(value) ? value : 0));
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - clamped);
  const colors = {
    brand: "#2563eb",
    success: "#16a34a",
    warning: "#d97706",
    danger: "#dc2626",
  };

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg viewBox="0 0 100 100" className="h-full w-full">
        <circle cx="50" cy="50" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="8" />
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke={colors[tone]}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-semibold tracking-tight text-app-text">
          {(clamped * 100).toFixed(0)}%
        </span>
        {label && <span className="mt-0.5 text-[11px] text-app-muted">{label}</span>}
      </div>
    </div>
  );
}

export function MiniBar({
  value,
  className,
}: {
  value: number;
  className?: string;
}) {
  const clamped = Math.max(0, Math.min(1, Number.isFinite(value) ? value : 0));
  return (
    <div className={cn("flex h-10 items-end gap-1", className)}>
      <div
        className="w-2 rounded-sm bg-brand/80 transition-all"
        style={{ height: `${Math.max(8, clamped * 100)}%` }}
      />
    </div>
  );
}
