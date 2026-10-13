import type { AnalyzeResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

const LABELS: Record<string, { title: string; hint: string }> = {
  structure: { title: "Structure", hint: "Parseability & formatting (14 checks)" },
  skills: { title: "Skill match", hint: "JD skills, evidence-weighted" },
  context: { title: "Contextual fit", hint: "Whole resume vs whole JD (BGE-small)" },
};

const MODE_NOTE: Record<string, string> = {
  full: "Score = weighted sum of all three layers.",
  structure_skills: "Contextual model unavailable — structure + skill match only.",
  structure_context: "No skills recognised in this JD — structure + contextual fit.",
  structure_only: "No job description — structure health only.",
  structure_only_jd_unmatched: "JD given but no match layer available — structure only, not a job match.",
};

function barColor(v: number) {
  if (v >= 75) return "bg-score-high";
  if (v >= 50) return "bg-score-mid";
  return "bg-score-low";
}

export function ScoreBreakdownPanel({ result }: { result: AnalyzeResponse }) {
  const bd = result.score_breakdown;
  if (!bd) return null;
  const keys = Object.keys(bd.weights);
  return (
    <div className="space-y-4">
      {keys.map((k) => {
        const value = bd.components[k] ?? 0;
        const label = LABELS[k] ?? { title: k, hint: "" };
        return (
          <div key={k}>
            <div className="flex items-baseline justify-between gap-2">
              <p className="text-xs uppercase tracking-wider text-text-muted">
                {label.title}
                <span className="ml-1.5 normal-case tracking-normal text-text-muted/80">
                  × {Math.round(bd.weights[k] * 100)}%
                </span>
              </p>
              <p className="tabular-nums text-lg font-semibold text-text">
                {value}
                <span className="text-xs font-normal text-text-muted">/100</span>
              </p>
            </div>
            <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-border">
              <div className={cn("h-full rounded-full", barColor(value))} style={{ width: `${Math.min(100, value)}%` }} />
            </div>
            <p className="mt-1 text-[11px] text-text-muted">{label.hint}</p>
          </div>
        );
      })}
      <p className="text-[11px] leading-relaxed text-text-muted">{MODE_NOTE[bd.mode] ?? ""}</p>
    </div>
  );
}
