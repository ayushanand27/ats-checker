import { cn } from "@/lib/utils";

interface StepLabelProps {
  step: number;
  title: string;
  subtitle?: string;
  active?: boolean;
}

export function StepLabel({ step, title, subtitle, active }: StepLabelProps) {
  const stepStr = String(step).padStart(2, "0");
  return (
    <div className="flex items-start gap-3">
      <span
        className={cn(
          "shrink-0 font-mono text-xs tabular-nums tracking-wider",
          active ? "text-accent" : "text-text-muted",
        )}
      >
        {stepStr}
        <span className="mx-1.5 text-border">·</span>
      </span>
      <div>
        <h2
          className={cn(
            "text-base font-semibold tracking-tight",
            active ? "text-text" : "text-text-muted",
          )}
        >
          {title}
        </h2>
        {subtitle && (
          <p className="mt-0.5 text-xs text-text-muted">{subtitle}</p>
        )}
      </div>
    </div>
  );
}
