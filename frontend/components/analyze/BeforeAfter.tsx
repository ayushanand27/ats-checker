import type { ResumeStruct, RewriteResponse } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function CompareBody({
  data,
  isAfter,
}: {
  data: ResumeStruct | RewriteResponse;
  isAfter?: boolean;
}) {
  const summary = "summary" in data ? data.summary : "";
  const skills = data.skills ?? [];
  const experience = data.experience ?? [];
  const exp0 = experience[0];

  return (
    <div className="space-y-3 text-sm text-text">
      <div>
        <p className="text-[11px] font-medium uppercase tracking-wider text-text-muted">
          Summary
        </p>
        <p className="mt-1.5 leading-relaxed">{summary || "—"}</p>
      </div>
      <div>
        <p className="text-[11px] font-medium uppercase tracking-wider text-text-muted">
          Skills
        </p>
        <p className="mt-1.5 leading-relaxed">{skills.length ? skills.join(", ") : "—"}</p>
      </div>
      {exp0 && (
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wider text-text-muted">
            Experience (first role)
          </p>
          <p className="mt-1.5 font-medium">
            {exp0.title} @ {exp0.company}
          </p>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-relaxed text-text-muted">
            {(exp0.bullets ?? []).slice(0, 3).map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        </div>
      )}
      {isAfter && (
        <p className="text-xs text-accent">AI-suggested — review before using</p>
      )}
    </div>
  );
}

interface BeforeAfterProps {
  original: ResumeStruct;
  rewritten: RewriteResponse;
}

export function BeforeAfter({ original, rewritten }: BeforeAfterProps) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Card className="overflow-hidden">
        <CardHeader className="border-b border-border py-3">
          <CardTitle className="text-xs font-medium uppercase tracking-wider text-text-muted">
            Before
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <CompareBody data={original} />
        </CardContent>
      </Card>
      <Card className="overflow-hidden border-accent/40">
        <CardHeader className="border-b border-border py-3">
          <CardTitle className="text-xs font-medium uppercase tracking-wider text-accent">
            After — AI suggested
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <CompareBody data={rewritten} isAfter />
        </CardContent>
      </Card>
    </div>
  );
}
