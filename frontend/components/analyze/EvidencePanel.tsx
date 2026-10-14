import { AlertTriangle, CheckCircle2, ListChecks, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AnalyzeResponse, SkillMatchDetail } from "@/lib/types";
import { cn } from "@/lib/utils";

function ViaTag({ d }: { d: SkillMatchDetail }) {
  if (d.via === "exact") return <span className="text-text-muted">exact</span>;
  if (d.via === "alias") return <span className="text-text-muted">alias of {d.resume_skill}</span>;
  return (
    <span className="text-warn">
      ≈ {d.resume_skill} ({d.similarity.toFixed(2)})
    </span>
  );
}

export function EvidencePanel({ result }: { result: AnalyzeResponse }) {
  const details = result.layer2?.match_details ?? [];
  const warnings = result.keyword_analysis?.stuffing_warnings ?? [];
  const lam = result.layer2?.list_credit ?? result.keyword_analysis?.list_credit ?? 0.5;
  if (!details.length && !warnings.length) return null;

  const demonstrated = details.filter((d) => d.evidence !== "listed_only");
  const listed = details.filter((d) => d.evidence === "listed_only");

  return (
    <Card>
      <CardHeader className="p-4 pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <ListChecks className="h-4 w-4 text-accent" />
          Skill evidence check
        </CardTitle>
        <p className="text-xs text-text-muted">
          A skill used in a project or experience sentence earns full credit. A skill that only appears in a
          skills list earns {Math.round(lam * 100)}% — so pasting the JD&apos;s keywords no longer games the score.
        </p>
      </CardHeader>
      <CardContent className="space-y-3 p-4 pt-0">
        {warnings.map((w, i) => (
          <div key={i} className="flex gap-2 rounded-md border border-fail/30 bg-fail/5 px-3 py-2 text-xs text-text">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-fail" />
            <span>{w}</span>
          </div>
        ))}
        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <p className="mb-2 flex items-center gap-1.5 text-xs uppercase tracking-wider text-text-muted">
              <CheckCircle2 className="h-3.5 w-3.5 text-pass" /> Demonstrated ({demonstrated.length})
            </p>
            <ul className="space-y-1">
              {demonstrated.map((d) => (
                <li key={d.jd_skill} className="flex justify-between gap-2 text-xs">
                  <span className="font-medium text-text">{d.jd_skill}</span>
                  <span className="text-right"><ViaTag d={d} /> · {Math.round(d.credit * 100)}%</span>
                </li>
              ))}
              {!demonstrated.length && <li className="text-xs text-text-muted">None yet</li>}
            </ul>
          </div>
          <div>
            <p className="mb-2 flex items-center gap-1.5 text-xs uppercase tracking-wider text-text-muted">
              <Sparkles className="h-3.5 w-3.5 text-warn" /> Listed only ({listed.length})
            </p>
            <ul className="space-y-1">
              {listed.map((d) => (
                <li key={d.jd_skill} className="flex justify-between gap-2 text-xs">
                  <span className={cn("font-medium text-text")}>{d.jd_skill}</span>
                  <span className="text-right"><ViaTag d={d} /> · {Math.round(d.credit * 100)}%</span>
                </li>
              ))}
              {!listed.length && <li className="text-xs text-text-muted">Every matched skill is backed by a sentence</li>}
            </ul>
            {!!listed.length && (
              <p className="mt-2 text-[11px] text-text-muted">
                Add one bullet per skill that shows it in use (what you built, and the result).
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
