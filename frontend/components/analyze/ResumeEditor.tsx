"use client";

import { Loader2, Save } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { ExperienceEntry, ResumeStruct } from "@/lib/types";

interface ResumeEditorProps {
  resume: ResumeStruct;
  disabled?: boolean;
  onSave: (updated: ResumeStruct) => void | Promise<void>;
}

export function ResumeEditor({ resume, disabled, onSave }: ResumeEditorProps) {
  const [draft, setDraft] = useState<ResumeStruct>({ ...resume });
  const [saving, setSaving] = useState(false);

  const updateExp = (idx: number, field: keyof ExperienceEntry, value: string) => {
    const experience = [...(draft.experience ?? [])];
    experience[idx] = { ...experience[idx], [field]: value };
    setDraft({ ...draft, experience });
  };

  const updateBullet = (expIdx: number, bulletIdx: number, value: string) => {
    const experience = [...(draft.experience ?? [])];
    const bullets = [...(experience[expIdx].bullets ?? [])];
    bullets[bulletIdx] = value;
    experience[expIdx] = { ...experience[expIdx], bullets };
    setDraft({ ...draft, experience });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(draft);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between p-4 pb-2">
        <CardTitle className="text-sm">Edit resume</CardTitle>
        <Button size="sm" onClick={handleSave} disabled={disabled || saving}>
          {saving ? (
            <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
          ) : (
            <Save className="mr-1 h-3.5 w-3.5" />
          )}
          Save &amp; re-score
        </Button>
      </CardHeader>
      <CardContent className="space-y-4 p-4 pt-2">
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label className="text-[10px] uppercase tracking-wider text-text-muted">Name</label>
            <Input
              value={draft.name ?? ""}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              disabled={disabled}
              className="mt-1"
            />
          </div>
          <div>
            <label className="text-[10px] uppercase tracking-wider text-text-muted">Skills (comma-separated)</label>
            <Input
              value={(draft.skills ?? []).join(", ")}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  skills: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                })
              }
              disabled={disabled}
              className="mt-1"
            />
          </div>
        </div>

        <div>
          <label className="text-[10px] uppercase tracking-wider text-text-muted">Summary</label>
          <Textarea
            value={draft.summary ?? ""}
            onChange={(e) => setDraft({ ...draft, summary: e.target.value })}
            disabled={disabled}
            className="mt-1 min-h-[80px]"
          />
        </div>

        {(draft.experience ?? []).map((exp, i) => (
          <div key={i} className="space-y-2 rounded-md border border-border p-3">
            <div className="grid gap-2 sm:grid-cols-2">
              <Input
                placeholder="Job title"
                value={exp.title ?? ""}
                onChange={(e) => updateExp(i, "title", e.target.value)}
                disabled={disabled}
              />
              <Input
                placeholder="Company"
                value={exp.company ?? ""}
                onChange={(e) => updateExp(i, "company", e.target.value)}
                disabled={disabled}
              />
            </div>
            {(exp.bullets ?? []).map((b, j) => (
              <Textarea
                key={j}
                value={b}
                onChange={(e) => updateBullet(i, j, e.target.value)}
                disabled={disabled}
                className="min-h-[48px] text-xs"
              />
            ))}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
