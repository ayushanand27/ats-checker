"use client";

import { Clock, Loader2, Save, Sparkles, Trash2, UserCheck } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import {
  deleteHistoryItem,
  getHistoryItem,
  getProfile,
  listHistory,
  saveProfile,
  tailorProfile,
} from "@/lib/api";
import type {
  AnalyzeResponse,
  HistoryItem,
  ResumeStruct,
  RewriteResponse,
  TemplateChoice,
} from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface ProfilePanelProps {
  jdText: string;
  template: TemplateChoice;
  currentResume: ResumeStruct | null;
  onLoadAnalysis: (
    res: AnalyzeResponse,
    rewrite: RewriteResponse | null,
    tailoredResume: ResumeStruct | null,
  ) => void;
}

export function ProfilePanel({
  jdText,
  template,
  currentResume,
  onLoadAnalysis,
}: ProfilePanelProps) {
  const { user } = useAuth();
  const [profile, setProfile] = useState<ResumeStruct | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [p, h] = await Promise.all([getProfile(), listHistory()]);
      setProfile(p.profile);
      setUpdatedAt(p.updated_at);
      setHistory(h);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load profile");
    }
  }, []);

  useEffect(() => {
    if (user) void refresh();
  }, [user, refresh]);

  if (!user) return null;

  const handleSaveProfile = async () => {
    if (!currentResume) return;
    setBusy("save");
    setError(null);
    setMsg(null);
    try {
      const res = await saveProfile(currentResume);
      setProfile(res.profile);
      setUpdatedAt(res.updated_at);
      setMsg("Saved as your master profile. Next time, just paste a JD.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setBusy(null);
    }
  };

  const handleTailor = async () => {
    setBusy("tailor");
    setError(null);
    setMsg(null);
    try {
      const res = await tailorProfile({
        jdText: jdText.trim() || undefined,
        template,
        useAi: true,
        save: true,
      });
      onLoadAnalysis(res.analysis, res.rewrite, res.tailored_resume);
      setMsg(
        res.ai_used
          ? `Tailored to this JD with AI. Score: ${res.analysis.core_score}.`
          : `Scored your profile against this JD. Score: ${res.analysis.core_score}. (Add GROQ_API_KEY for AI tailoring.)`,
      );
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Tailoring failed");
    } finally {
      setBusy(null);
    }
  };

  const handleLoadHistory = async (id: number) => {
    setBusy(`hist-${id}`);
    setError(null);
    try {
      const item = await getHistoryItem(id);
      onLoadAnalysis(item.result, null, item.result.resume_struct);
      setMsg(`Loaded saved analysis from ${new Date(item.created_at).toLocaleString()}.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load analysis");
    } finally {
      setBusy(null);
    }
  };

  const handleDelete = async (id: number) => {
    setBusy(`del-${id}`);
    try {
      await deleteHistoryItem(id);
      setHistory((h) => h.filter((it) => it.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <Card className="border-accent/30">
      <CardHeader className="p-4 pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <UserCheck className="h-4 w-4 text-accent" />
          Your profile & history
        </CardTitle>
        <CardDescription>
          {profile
            ? "Paste a job description above, then generate a tailored resume from your saved profile."
            : "Analyze a resume, then save it as your master profile to reuse it for any JD."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 p-4 pt-2">
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            onClick={handleTailor}
            disabled={busy !== null || !profile}
          >
            {busy === "tailor" ? (
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Sparkles className="mr-1 h-3.5 w-3.5" />
            )}
            Generate from my profile
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleSaveProfile}
            disabled={busy !== null || !currentResume}
          >
            {busy === "save" ? (
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Save className="mr-1 h-3.5 w-3.5" />
            )}
            Save current resume as my profile
          </Button>
        </div>

        {profile && (
          <p className="text-[11px] text-text-muted">
            Master profile: <span className="text-text">{profile.name || "Unnamed"}</span>
            {" · "}
            {(profile.skills?.length ?? 0)} skills, {(profile.experience?.length ?? 0)} roles
            {updatedAt && ` · updated ${new Date(updatedAt).toLocaleDateString()}`}
          </p>
        )}

        {msg && <p className="text-xs text-score-high">{msg}</p>}
        {error && <p className="text-xs text-fail">{error}</p>}

        {history.length > 0 && (
          <div className="space-y-2">
            <p className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-text-muted">
              <Clock className="h-3 w-3" /> Recent analyses
            </p>
            <ul className="space-y-1">
              {history.map((it) => (
                <li
                  key={it.id}
                  className="flex items-center justify-between gap-2 rounded-md border border-border bg-surface/50 px-3 py-2 text-xs"
                >
                  <button
                    type="button"
                    className="flex-1 text-left hover:text-accent"
                    onClick={() => handleLoadHistory(it.id)}
                    disabled={busy !== null}
                  >
                    {busy === `hist-${it.id}` && (
                      <Loader2 className="mr-1 inline h-3 w-3 animate-spin" />
                    )}
                    <span className="text-text">{it.jd_title || "Untitled role"}</span>
                    {it.core_score != null && (
                      <span className="ml-2 tabular-nums text-text-muted">
                        {it.core_score}
                      </span>
                    )}
                    <span className="ml-2 text-text-muted">
                      {new Date(it.created_at).toLocaleDateString()}
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(it.id)}
                    disabled={busy !== null}
                    aria-label="Delete analysis"
                    className="text-text-muted hover:text-fail"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
