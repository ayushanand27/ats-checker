"use client";

import type { TopFix } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface TopFixesProps {
  fixes: TopFix[];
}

export function TopFixes({ fixes }: TopFixesProps) {
  if (!fixes.length) {
    return (
      <Card className="border-score-high/30">
        <CardContent className="p-4 text-sm text-score-high">
          No critical fixes — your resume aligns well with industry ATS expectations for this run.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="p-4 pb-2">
        <CardTitle className="text-sm font-medium">Top fixes — do these first</CardTitle>
        <p className="text-xs text-text-muted">
          Prioritized by impact on ATS parsing and JD alignment (industry-standard coaching order).
        </p>
      </CardHeader>
      <CardContent className="space-y-2 p-4 pt-0">
        {fixes.map((fix) => (
          <div
            key={fix.priority}
            className={cn(
              "rounded-md border px-3 py-2.5",
              fix.severity === "high" ? "border-fail/30 bg-fail/5" : "border-border bg-surface/50",
            )}
          >
            <div className="flex items-start gap-2">
              <span className="tabular-nums text-xs font-semibold text-accent">{fix.priority}</span>
              <div>
                <p className="text-sm font-medium text-text">{fix.title}</p>
                <p className="mt-0.5 text-xs leading-relaxed text-text-muted">{fix.detail}</p>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
