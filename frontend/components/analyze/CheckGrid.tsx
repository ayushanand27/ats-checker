import { Check, X } from "lucide-react";
import type { Layer1Check } from "@/lib/types";
import { cn } from "@/lib/utils";

interface CheckGridProps {
  checks: Layer1Check[];
}

export function CheckGrid({ checks }: CheckGridProps) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {checks.map((check) => (
        <div
          key={check.name}
          className={cn(
            "flex gap-3 rounded-md border border-border bg-surface p-4 transition-colors duration-micro hover:bg-surface-hover",
          )}
        >
          <span className="mt-0.5 shrink-0">
            {check.passed ? (
              <Check className="h-4 w-4 text-pass" strokeWidth={2.5} />
            ) : (
              <X className="h-4 w-4 text-fail" strokeWidth={2.5} />
            )}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-medium text-text">{check.name}</p>
            <p className="mt-0.5 text-xs leading-relaxed text-text-muted">{check.reason}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
