"use client";

import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface ScoreComparisonProps {
  before: number;
  after: number;
  label?: string;
}

export function ScoreComparison({ before, after, label = "After AI optimization" }: ScoreComparisonProps) {
  const delta = Math.round((after - before) * 10) / 10;
  const improved = delta > 0;
  const same = delta === 0;

  return (
    <Card className="border-accent/30 bg-accent/5">
      <CardContent className="flex flex-wrap items-center gap-4 p-4">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-text-muted">Before</p>
          <p className="tabular-nums text-2xl font-semibold">{before}</p>
        </div>
        <div className="text-text-muted">→</div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-text-muted">{label}</p>
          <p className="tabular-nums text-2xl font-semibold">{after}</p>
        </div>
        <div
          className={cn(
            "ml-auto flex items-center gap-1 rounded-full px-3 py-1 text-sm font-medium",
            same && "bg-surface text-text-muted",
            improved && "bg-score-high/20 text-score-high",
            !same && !improved && "bg-destructive/15 text-destructive",
          )}
        >
          {same ? (
            <>
              <Minus className="h-4 w-4" />
              No change
            </>
          ) : improved ? (
            <>
              <ArrowUp className="h-4 w-4" />+{delta}
            </>
          ) : (
            <>
              <ArrowDown className="h-4 w-4" />
              {delta}
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
