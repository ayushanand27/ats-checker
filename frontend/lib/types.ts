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
  formatting_checks?: Layer1Check[];
  word_count: number;
  metrics?: { total_bullets?: number; bullets_with_metrics?: number };
}

export interface TopFix {
  priority: number;
  title: string;
  detail: string;
  severity: string;
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
  location?: string | null;
  leetcode?: string | null;
  portfolio?: string | null;
}

export interface ExperienceEntry {
  title?: string;
  company?: string;
  dates?: string;
  location?: string;
  bullets?: string[];
}

export interface EducationEntry {
  degree?: string;
  institution?: string;
  dates?: string;
  gpa?: string;
  location?: string;
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

export interface KeywordAnalysis {
  keyword_score: number;
  match_rate_percent: number;
  matched_keywords: {
    keyword: string;
    required: boolean;
    match_type: string;
    placements: string[];
    count: number;
  }[];
  missing_keywords: string[];
  placement_summary: Record<string, number>;
  density_warnings: string[];
  highlights: { keyword: string; line: string | null; status: string }[];
  total_jd_keywords: number;
  matched_count: number;
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
  top_fixes?: TopFix[];
  score_band?: string;
  keyword_analysis?: KeywordAnalysis | null;
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

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ResumeChatRequest {
  jd_text: string;
  messages?: ChatMessage[];
  user_message?: string | null;
  draft?: ResumeStruct | null;
}

export interface ResumeChatResponse {
  message: string;
  messages: ChatMessage[];
  draft: ResumeStruct;
  is_complete: boolean;
  progress_percent: number;
}

export interface AnalyzeStructuredParams {
  resumeStruct: ResumeStruct;
  jdText?: string;
  template: TemplateChoice;
  source?: "chat" | "rescore" | "editor";
}

export interface PublicUser {
  id: number;
  email: string;
  name?: string | null;
  created_at?: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: PublicUser;
}

export interface ProfileResponse {
  profile: ResumeStruct | null;
  updated_at: string | null;
}

export interface TailorResponse {
  analysis: AnalyzeResponse;
  rewrite: RewriteResponse | null;
  tailored_resume: ResumeStruct;
  analysis_id: number | null;
  ai_used: boolean;
}

export interface HistoryItem {
  id: number;
  jd_title?: string | null;
  core_score?: number | null;
  created_at: string;
}

export interface HistoryDetail {
  id: number;
  jd_title?: string | null;
  jd_text?: string | null;
  core_score?: number | null;
  created_at: string;
  result: AnalyzeResponse;
}
