"use client";

import { SkillPills } from "@/components/analyze/SkillPills";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { KeywordAnalysis } from "@/lib/types";

interface KeywordAnalysisPanelProps {
  analysis: KeywordAnalysis;
}

export function KeywordAnalysisPanel({ analysis }: KeywordAnalysisPanelProps) {
  const placement = analysis.placement_summary;
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-text">
        Keyword match
        <span className="ml-2 tabular-nums text-text-muted">
          {analysis.keyword_score}%
        </span>
      </h3>
      <p className="text-xs text-text-muted">
        Industry ATS checkers weight keyword overlap ~30–40%. Exact JD terms score higher
        than synonyms; placement in summary, skills, and experience bullets matters.
      </p>

      <div className="grid gap-3 sm:grid-cols-3">
        <Card className="bg-surface/50">
          <CardContent className="p-3">
            <p className="text-[10px] uppercase tracking-wider text-text-muted">In summary</p>
            <p className="tabular-nums text-lg font-semibold">{placement.summary ?? 0}</p>
          </CardContent>
        </Card>
        <Card className="bg-surface/50">
          <CardContent className="p-3">
            <p className="text-[10px] uppercase tracking-wider text-text-muted">In skills</p>
            <p className="tabular-nums text-lg font-semibold">{placement.skills ?? 0}</p>
          </CardContent>
        </Card>
        <Card className="bg-surface/50">
          <CardContent className="p-3">
            <p className="text-[10px] uppercase tracking-wider text-text-muted">In experience</p>
            <p className="tabular-nums text-lg font-semibold">{placement.experience ?? 0}</p>
          </CardContent>
        </Card>
      </div>

      {!!analysis.missing_keywords.length && (
        <div>
          <p className="mb-2 text-xs uppercase tracking-wider text-text-muted">
            Missing JD keywords
          </p>
          <SkillPills skills={analysis.missing_keywords} variant="missing" />
        </div>
      )}

      {!!analysis.density_warnings.length && (
        <Card>
          <CardHeader className="p-4 pb-2">
            <CardTitle className="text-xs font-medium uppercase tracking-wider text-text-muted">
              Keyword density
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 p-4 pt-0 text-xs text-text-muted">
            {analysis.density_warnings.map((w, i) => (
              <p key={i}>{w}</p>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
