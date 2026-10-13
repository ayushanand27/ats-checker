import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ContextualResult } from "@/lib/types";

export function ContextualPanel({ ctx }: { ctx: ContextualResult }) {
  return (
    <Card>
      <CardHeader className="p-4 pb-2">
        <CardTitle className="text-sm font-medium">
          Contextual fit
          <span className="ml-2 tabular-nums text-text-muted">{ctx.score}/100</span>
        </CardTitle>
        <p className="text-xs text-text-muted">
          Compares the meaning of your whole resume with the whole job description, so it also credits
          paraphrases that keyword matching misses. Model: {ctx.model} (runs locally).
        </p>
      </CardHeader>
      <CardContent className="space-y-2 p-4 pt-0 text-xs">
        <p className="text-text">{ctx.verdict}</p>
        <p className="text-text-muted">
          Read in {ctx.chunks} chunk{ctx.chunks === 1 ? "" : "s"} · cosine similarity {ctx.cosine.toFixed(3)}
        </p>
        {ctx.best_chunk_preview && (
          <blockquote className="rounded-md border border-border bg-surface/60 p-3 italic text-text-muted">
            Closest part to the JD: “{ctx.best_chunk_preview}”
          </blockquote>
        )}
      </CardContent>
    </Card>
  );
}
