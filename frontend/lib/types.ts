/** Mirrors resume_scorer/api/schemas.py — keep in sync. */

export type TemplateChoice = "jacks_tech" | "classic_nontech" | "custom";
export type OutputFormat = "docx" | "pdf" | "tex";

export interface ScoreGaps {
  missing_required: string[];
  missing_preferred: string[];
  experience_note: string | null;
}

export interface Layer1Check {
  name: string;
  passed: boolean;
  reason: string;
  weight: number;
  score: number;
}

export interface Layer1Result {
  score: number;
  checks: Layer1Check[];
  word_count: number;
}

export interface Layer2Result {
  score: number;
  matched_required: string[];
  missing_required: string[];
  matched_preferred: string[];
  missing_preferred: string[];
  experience_note: string | null;
}

export interface ResumeContact {
  email?: string | null;
  phone?: string | null;
  linkedin?: string | null;
  github?: string | null;
}

export interface ExperienceEntry {
  title?: string;
  company?: string;
  dates?: string;
  bullets?: string[];
}

export interface EducationEntry {
  degree?: string;
  institution?: string;
  dates?: string;
}

export interface ResumeStruct {
  name?: string;
  contact?: ResumeContact;
  summary?: string;
  skills?: string[];
  experience?: ExperienceEntry[];
  education?: EducationEntry[];
  projects?: Record<string, unknown>[];
  sections_found?: string[];
  experience_years?: number;
  metrics?: { total_bullets?: number; bullets_with_metrics?: number };
  raw_text?: string;
  [key: string]: unknown;
}

export interface JdStruct {
  title?: string;
  required_skills?: string[];
  preferred_skills?: string[];
  all_skills?: string[];
  min_experience_years?: number | null;
  raw_text?: string;
  jd_provided?: boolean;
  [key: string]: unknown;
}

export interface AnalyzeResponse {
  core_score: number;
  jd_provided: boolean;
  template: TemplateChoice;
  parse_warning: string | null;
  resume_struct: ResumeStruct;
  jd_struct: JdStruct | null;
  layer1: Layer1Result;
  layer2: Layer2Result | null;
  gaps: ScoreGaps;
}

export interface RewriteRequest {
  resume_struct: ResumeStruct;
  jd_struct?: JdStruct | null;
  gaps?: ScoreGaps;
}

export interface RewriteResponse {
  summary: string;
  skills: string[];
  experience: ExperienceEntry[];
  education: EducationEntry[];
  projects: Record<string, unknown>[];
  change_log: string[];
}

export interface AnalyzeParams {
  resume: File;
  template: TemplateChoice;
  jdText?: string;
  jdFile?: File | null;
}

export interface GenerateParams {
  resumeStruct: ResumeStruct;
  template: TemplateChoice;
  format: OutputFormat;
  rewritten?: RewriteResponse | null;
  customTemplate?: File | null;
}
