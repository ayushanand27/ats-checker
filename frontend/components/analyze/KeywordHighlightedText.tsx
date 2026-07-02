"use client";

import type { KeywordAnalysis } from "@/lib/types";
import { cn } from "@/lib/utils";

interface KeywordHighlightedTextProps {
  text: string;
  analysis: KeywordAnalysis | null | undefined;
  className?: string;
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function KeywordHighlightedText({
  text,
  analysis,
  className,
}: KeywordHighlightedTextProps) {
  if (!text?.trim() || !analysis?.matched_keywords?.length) {
    return (
      <pre
        className={cn(
          "max-h-64 overflow-auto whitespace-pre-wrap rounded-md border border-border bg-canvas/50 p-3 text-xs leading-relaxed text-text-muted",
          className,
        )}
      >
        {text || "No raw text available."}
      </pre>
    );
  }

  const keywords = Array.from(
    new Set(analysis.matched_keywords.map((m) => m.keyword).filter(Boolean)),
  ).sort((a, b) => b.length - a.length);

  const pattern = new RegExp(
    `(${keywords.map(escapeRegex).join("|")})`,
    "gi",
  );

  const parts = text.split(pattern);

  return (
    <div className="space-y-2">
      <p className="text-xs text-text-muted">
        <span className="mr-3 inline-flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-sm bg-score-high/60" />
          Matched JD keyword
        </span>
        {!!analysis.missing_keywords.length && (
          <span className="inline-flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-sm bg-destructive/50" />
            Missing — add where truthful
          </span>
        )}
      </p>
      <pre
        className={cn(
          "max-h-64 overflow-auto whitespace-pre-wrap rounded-md border border-border bg-canvas/50 p-3 text-xs leading-relaxed text-text",
          className,
        )}
      >
        {parts.map((part, i) => {
          const isMatch = keywords.some(
            (k) => k.toLowerCase() === part.toLowerCase(),
          );
          if (isMatch) {
            return (
              <mark
                key={i}
                className="rounded-sm bg-score-high/25 px-0.5 text-text"
              >
                {part}
              </mark>
            );
          }
          return <span key={i}>{part}</span>;
        })}
      </pre>
      {!!analysis.missing_keywords.length && (
        <p className="text-[11px] text-text-muted">
          Not in resume: {analysis.missing_keywords.slice(0, 8).join(", ")}
          {analysis.missing_keywords.length > 8 ? "…" : ""}
        </p>
      )}
    </div>
  );
}
