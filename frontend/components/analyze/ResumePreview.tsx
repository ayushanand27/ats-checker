"use client";

import type { ResumeStruct, RewriteResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

type ResumeBodyData = ResumeStruct & Partial<RewriteResponse>;

function ResumeBody({ data, compact }: { data: ResumeBodyData; compact?: boolean }) {
  const contact = "contact" in data ? data.contact : undefined;
  const experience = data.experience ?? [];
  const education = data.education ?? [];
  const projects = data.projects ?? [];
  const achievements = "achievements" in data ? (data.achievements as string[]) : [];

  return (
    <div className={cn("space-y-4 text-sm text-text", compact && "text-xs")}>
      {data.name && (
        <div className="text-center">
          <h2 className="font-serif text-lg font-semibold">{String(data.name)}</h2>
          {contact && (
            <p className="mt-1 text-text-muted">
              {[
                contact.location,
                contact.phone,
                contact.email,
                contact.linkedin,
                contact.github,
              ]
                .filter(Boolean)
                .join(" | ")}
            </p>
          )}
        </div>
      )}

      {data.summary && (
        <section>
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
            Summary
          </h3>
          <p className="mt-1 leading-relaxed">{data.summary}</p>
        </section>
      )}

      {!!data.skills?.length && (
        <section>
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
            Skills
          </h3>
          <p className="mt-1">{data.skills.join(", ")}</p>
        </section>
      )}

      {!!experience.length && (
        <section>
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
            Experience
          </h3>
          <div className="mt-2 space-y-3">
            {experience.map((exp, i) => (
              <div key={i}>
                <p className="font-medium">
                  {exp.title}
                  {exp.company ? ` — ${exp.company}` : ""}
                </p>
                <p className="text-xs text-text-muted">
                  {[exp.location, exp.dates].filter(Boolean).join(" · ")}
                </p>
                <ul className="mt-1 list-disc space-y-0.5 pl-4 text-text-muted">
                  {(exp.bullets ?? []).map((b, j) => (
                    <li key={j}>{b}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {!!education.length && (
        <section>
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
            Education
          </h3>
          <ul className="mt-1 space-y-1">
            {education.map((edu, i) => (
              <li key={i}>
                {edu.degree}
                {edu.gpa ? ` (CGPA: ${edu.gpa})` : ""}
                {edu.institution ? ` — ${edu.institution}` : ""}
                {edu.dates ? ` (${edu.dates})` : ""}
              </li>
            ))}
          </ul>
        </section>
      )}

      {!!projects.length && (
        <section>
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
            Projects
          </h3>
          <div className="mt-2 space-y-2">
            {projects.map((proj, i) => (
              <div key={i}>
                <p className="font-medium">
                  {String(proj.name ?? "Project")}
                  {proj.tech_stack ? ` | ${String(proj.tech_stack)}` : ""}
                </p>
                <ul className="mt-0.5 list-disc pl-4 text-text-muted">
                  {((proj.bullets as string[]) ?? []).map((b, j) => (
                    <li key={j}>{b}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {!!achievements?.length && (
        <section>
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
            Achievements
          </h3>
          <ul className="mt-1 list-disc pl-4 text-text-muted">
            {achievements.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

interface ResumePreviewProps {
  resume: ResumeStruct;
  rewritten?: RewriteResponse | null;
  className?: string;
}

export function ResumePreview({ resume, rewritten, className }: ResumePreviewProps) {
  const payload = rewritten
    ? {
        ...resume,
        summary: rewritten.summary || resume.summary,
        skills: rewritten.skills?.length ? rewritten.skills : resume.skills,
        experience: rewritten.experience?.length ? rewritten.experience : resume.experience,
        education: rewritten.education?.length ? rewritten.education : resume.education,
        projects: rewritten.projects?.length ? rewritten.projects : resume.projects,
      }
    : resume;

  return (
    <div
      className={cn(
        "max-h-[70vh] overflow-y-auto rounded-md border border-border bg-canvas p-6 shadow-inner",
        className,
      )}
    >
      <ResumeBody data={payload as ResumeStruct} />
    </div>
  );
}

export function ResumePreviewCompare({
  original,
  rewritten,
}: {
  original: ResumeStruct;
  rewritten: RewriteResponse;
}) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <div className="rounded-md border border-border bg-canvas p-4">
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-text-muted">Before</p>
        <ResumeBody data={original} compact />
      </div>
      <div className="rounded-md border border-accent/40 bg-canvas p-4">
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-accent">
          After — AI suggested
        </p>
        <ResumeBody
          data={{ ...original, ...rewritten } as ResumeStruct}
          compact
        />
      </div>
    </div>
  );
}
