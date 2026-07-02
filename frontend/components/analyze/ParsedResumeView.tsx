"use client";

import type { ResumeStruct } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ParsedResumeViewProps {
  resume: ResumeStruct;
}

function Field({ label, value }: { label: string; value?: string | null }) {
  if (!value?.trim()) return null;
  return (
    <div>
      <p className="text-[11px] font-medium uppercase tracking-wider text-text-muted">{label}</p>
      <p className="mt-0.5 text-sm text-text">{value}</p>
    </div>
  );
}

export function ParsedResumeView({ resume }: ParsedResumeViewProps) {
  const contact = resume.contact ?? {};
  const sections = resume.sections_found ?? [];

  return (
    <Card>
      <CardHeader className="p-4 pb-2">
        <CardTitle className="text-sm font-medium">What the ATS extracted</CardTitle>
        <p className="text-xs text-text-muted">
          This is the structured data parsers pull from your resume — verify it matches what you
          intended.
        </p>
      </CardHeader>
      <CardContent className="grid gap-4 p-4 pt-2 sm:grid-cols-2">
        <div className="space-y-3">
          <Field label="Name" value={resume.name as string} />
          <Field label="Email" value={contact.email as string} />
          <Field label="Phone" value={contact.phone as string} />
          <Field label="Location" value={contact.location as string} />
          <Field label="LinkedIn" value={contact.linkedin as string} />
          <Field label="GitHub" value={contact.github as string} />
          <div>
            <p className="text-[11px] font-medium uppercase tracking-wider text-text-muted">
              Sections detected
            </p>
            <p className="mt-0.5 text-sm text-text">
              {sections.length ? sections.join(", ") : "None"}
            </p>
          </div>
        </div>
        <div className="space-y-3">
          <Field
            label="Summary"
            value={(resume.summary as string)?.slice(0, 280) + ((resume.summary as string)?.length > 280 ? "…" : "")}
          />
          <div>
            <p className="text-[11px] font-medium uppercase tracking-wider text-text-muted">
              Skills ({resume.skills?.length ?? 0})
            </p>
            <p className="mt-0.5 text-sm leading-relaxed text-text">
              {resume.skills?.length ? resume.skills.join(", ") : "—"}
            </p>
          </div>
          <div>
            <p className="text-[11px] font-medium uppercase tracking-wider text-text-muted">
              Experience ({resume.experience?.length ?? 0} roles)
            </p>
            <ul className="mt-1 space-y-1 text-sm text-text">
              {(resume.experience ?? []).slice(0, 4).map((exp, i) => (
                <li key={i}>
                  {exp.title}
                  {exp.company ? ` @ ${exp.company}` : ""}
                  {exp.dates ? ` (${exp.dates})` : ""}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-[11px] font-medium uppercase tracking-wider text-text-muted">
              Education
            </p>
            <ul className="mt-1 space-y-1 text-sm text-text">
              {(resume.education ?? []).map((edu, i) => (
                <li key={i}>
                  {edu.degree}
                  {edu.institution ? `, ${edu.institution}` : ""}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
