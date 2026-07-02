import type { AnalyzeResponse, RewriteResponse, TemplateChoice } from "./types";

const SESSION_KEY = "resumematch-analyze-session";

export interface AnalyzeSession {
  result: AnalyzeResponse;
  rewrite: RewriteResponse | null;
  beforeScore: number | null;
  template: TemplateChoice;
  savedAt: string;
}

export function saveAnalyzeSession(session: AnalyzeSession): void {
  try {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  } catch {
    /* quota or private mode */
  }
}

export function loadAnalyzeSession(): AnalyzeSession | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as AnalyzeSession;
  } catch {
    return null;
  }
}

export function clearAnalyzeSession(): void {
  try {
    localStorage.removeItem(SESSION_KEY);
  } catch {
    /* ignore */
  }
}
