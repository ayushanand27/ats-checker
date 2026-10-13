import { Check, CircleHelp, Minus, X } from "lucide-react";
import type { RequirementCheck } from "@/lib/types";

const ICON = {
  pass: <Check className="h-4 w-4 text-pass" strokeWidth={2.5} />,
  partial: <Minus className="h-4 w-4 text-warn" strokeWidth={2.5} />,
  fail: <X className="h-4 w-4 text-fail" strokeWidth={2.5} />,
  unknown: <CircleHelp className="h-4 w-4 text-text-muted" strokeWidth={2} />,
} as const;

export function RequirementsPanel({ checks }: { checks: RequirementCheck[] }) {
  if (!checks.length) return null;
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-text">JD requirement checks</h3>
      <p className="text-xs text-text-muted">
        What recruiter searches look for besides skills: the exact job title, degree level, years of experience,
        and acronyms written in both forms.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        {checks.map((c) => (
          <div key={c.name} className="flex gap-3 rounded-md border border-border bg-surface p-4">
            <span className="mt-0.5 shrink-0">{ICON[c.status as keyof typeof ICON] ?? ICON.unknown}</span>
            <div className="min-w-0">
              <p className="text-sm font-medium text-text">{c.name}</p>
              <p className="mt-0.5 text-xs leading-relaxed text-text-muted">{c.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
