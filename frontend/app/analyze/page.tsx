"use client";

import { Loader2 } from "lucide-react";
import Link from "next/link";
import { useCallback, useState } from "react";
import { BeforeAfter } from "@/components/analyze/BeforeAfter";
import { CheckGrid } from "@/components/analyze/CheckGrid";
import { FileDropzone } from "@/components/analyze/FileDropzone";
import { ScoreGauge } from "@/components/analyze/ScoreGauge";
import { SkillPills } from "@/components/analyze/SkillPills";
import { StepLabel } from "@/components/analyze/StepLabel";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { analyzeResume, downloadBlob, generateResume, rewriteResume } from "@/lib/api";
import type {
  AnalyzeResponse,
  OutputFormat,
  RewriteResponse,
  TemplateChoice,
} from "@/lib/types";

const TEMPLATE_OPTIONS: { label: string; value: TemplateChoice }[] = [
  { label: "Jack's Tech Resume", value: "jacks_tech" },
  { label: "Classic Non-Tech Resume", value: "classic_nontech" },
  { label: "Upload Custom Template", value: "custom" },
];

type LoadingAction = "analyze" | "rewrite" | "generate" | null;

export default function AnalyzePage() {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [skipJd, setSkipJd] = useState(false);
  const [template, setTemplate] = useState<TemplateChoice>("jacks_tech");
  const [customTemplateFile, setCustomTemplateFile] = useState<File | null>(null);

  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [rewrite, setRewrite] = useState<RewriteResponse | null>(null);

  const [fmtDocx, setFmtDocx] = useState(true);
  const [fmtPdf, setFmtPdf] = useState(true);
  const [fmtTex, setFmtTex] = useState(false);

  const [loading, setLoading] = useState<LoadingAction>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const isCustom = template === "custom";

  const showError = useCallback((msg: string) => {
    setError(msg);
    setSuccess(null);
  }, []);

  const handleAnalyze = async () => {
    if (!resumeFile) {
      showError("Please upload a resume first.");
      return;
    }
    setLoading("analyze");
    setError(null);
    setSuccess(null);
    setRewrite(null);
    try {
      const data = await analyzeResume({
        resume: resumeFile,
        template,
        jdText: skipJd ? undefined : jdText,
        jdFile: skipJd ? null : jdFile,
      });
      setResult(data);
      if (data.parse_warning) {
        setSuccess(`Analysis complete. Note: ${data.parse_warning}`);
      }
    } catch (e) {
      showError(e instanceof Error ? e.message : "Analysis failed");
      setResult(null);
    } finally {
      setLoading(null);
    }
  };

  const handleRewrite = async () => {
    if (!result) return;
    setLoading("rewrite");
    setError(null);
    try {
      const data = await rewriteResume({
        resume_struct: result.resume_struct,
        jd_struct: result.jd_struct,
        gaps: result.gaps,
      });
      setRewrite(data);
      setSuccess("AI suggestions ready — review before generating downloads.");
    } catch (e) {
      showError(e instanceof Error ? e.message : "AI rewrite failed");
    } finally {
      setLoading(null);
    }
  };

  const handleGenerate = async () => {
    if (!result) return;
    const formats: OutputFormat[] = [];
    if (isCustom) {
      formats.push("docx");
    } else {
      if (fmtDocx) formats.push("docx");
      if (fmtPdf) formats.push("pdf");
      if (fmtTex) formats.push("tex");
    }
    if (!formats.length) {
      showError("Select at least one output format.");
      return;
    }
    if (isCustom && !customTemplateFile) {
      showError("Upload a custom .docx template before generating.");
      return;
    }

    setLoading("generate");
    setError(null);
    const errors: string[] = [];

    for (const format of formats) {
      try {
        const { blob, filename } = await generateResume({
          resumeStruct: result.resume_struct,
          template,
          format,
          rewritten: rewrite,
          customTemplate: isCustom ? customTemplateFile : null,
        });
        downloadBlob(blob, filename);
      } catch (e) {
        errors.push(
          `${format.toUpperCase()}: ${e instanceof Error ? e.message : "failed"}`,
        );
      }
    }

    setLoading(null);
    if (errors.length === formats.length) {
      showError(errors.join(" | "));
    } else if (errors.length) {
      setSuccess(`Some downloads succeeded. Issues: ${errors.join(" | ")}`);
      setError(null);
    } else {
      setSuccess(`Downloaded ${formats.length} file(s) successfully.`);
    }
  };

  const scoreLabel =
    result?.layer2 != null
      ? "ATS Match Score"
      : result?.jd_provided
        ? "ATS Structure Score"
        : "General ATS Score";
  const scoreHint =
    result && !result.jd_provided
      ? "Add a job description for tailored skill matching (Layer 1 only)."
      : result?.jd_provided && !result.layer2
        ? "Skill match not applicable — JD has no extractable skills. Score reflects structure only."
        : undefined;

  const activeStep = result ? 2 : 1;

  return (
    <div className="min-h-screen bg-canvas text-text">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-tool items-center justify-between px-4 py-4 sm:px-6">
          <Link
            href="/"
            className="font-serif text-lg tracking-tight text-text focus-ring rounded-sm"
          >
            ResumeMatch
          </Link>
          <span className="text-xs uppercase tracking-wider text-text-muted">ATS Tool</span>
        </div>
      </header>

      <main className="mx-auto max-w-tool space-y-8 px-4 py-8 sm:px-6">
        {error && (
          <Alert variant="destructive">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {success && !error && (
          <Alert className="border-score-high/30">
            <AlertTitle className="text-score-high">Success</AlertTitle>
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        )}

        <section className="space-y-4">
          <StepLabel
            step={1}
            title="Upload & Configure"
            subtitle="Resume required · Job description optional for tailored matching"
            active={activeStep === 1}
          />

          <div className="grid gap-3 md:grid-cols-2">
            <FileDropzone
              accept=".pdf,.docx,.txt"
              label="Drop resume here"
              hint="PDF, DOCX, or TXT · max 200MB"
              file={resumeFile}
              onFile={setResumeFile}
              disabled={loading !== null}
            />
            <Card>
              <CardHeader className="space-y-0 p-4 pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle>Job description</CardTitle>
                  <label className="flex cursor-pointer items-center gap-2 text-xs text-text-muted">
                    <input
                      type="checkbox"
                      checked={skipJd}
                      onChange={(e) => setSkipJd(e.target.checked)}
                      className="rounded border-border bg-canvas focus-ring"
                    />
                    Skip (optional)
                  </label>
                </div>
                <CardDescription>Tailored Layer 2 skill match</CardDescription>
              </CardHeader>
              <CardContent className="p-4 pt-2">
                {skipJd ? (
                  <p className="text-xs leading-relaxed text-text-muted">
                    JD skipped — general ATS structure score only.
                  </p>
                ) : (
                  <Tabs defaultValue="paste">
                    <TabsList className="h-8 w-full">
                      <TabsTrigger value="paste" className="flex-1">
                        Paste text
                      </TabsTrigger>
                      <TabsTrigger value="upload" className="flex-1">
                        Upload file
                      </TabsTrigger>
                    </TabsList>
                    <TabsContent value="paste" className="mt-3">
                      <Textarea
                        placeholder="Paste the full job description…"
                        className="min-h-[120px] resize-y"
                        value={jdText}
                        onChange={(e) => setJdText(e.target.value)}
                        disabled={loading !== null}
                      />
                    </TabsContent>
                    <TabsContent value="upload" className="mt-3">
                      <FileDropzone
                        accept=".pdf,.docx,.txt"
                        label="Drop JD file"
                        file={jdFile}
                        onFile={setJdFile}
                        disabled={loading !== null}
                      />
                    </TabsContent>
                  </Tabs>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-medium uppercase tracking-wider text-text-muted">
              Output template
            </label>
            <Select
              value={template}
              onValueChange={(v) => setTemplate(v as TemplateChoice)}
              disabled={loading !== null}
            >
              <SelectTrigger className="w-full max-w-md">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TEMPLATE_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {isCustom && (
              <FileDropzone
                accept=".docx"
                label="Custom .docx template (Jinja2 placeholders)"
                file={customTemplateFile}
                onFile={setCustomTemplateFile}
                disabled={loading !== null}
              />
            )}
          </div>

          <Button
            size="lg"
            onClick={handleAnalyze}
            disabled={loading !== null || !resumeFile}
          >
            {loading === "analyze" && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Analyze Resume
          </Button>
        </section>

        {loading === "analyze" && (
          <section className="space-y-3">
            <Skeleton className="h-6 w-40" />
            <Skeleton className="mx-auto h-[210px] w-[220px]" />
            <div className="grid gap-3 sm:grid-cols-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-[72px]" />
              ))}
            </div>
          </section>
        )}

        {result && loading !== "analyze" && (
          <>
            <section className="space-y-4 border-t border-border pt-8">
              <StepLabel
                step={2}
                title="ATS Score"
                subtitle="Two-layer analysis — structure + skill alignment"
                active
              />

              <Card>
                <CardContent className="p-5">
                  <div className="grid gap-6 md:grid-cols-2">
                    <ScoreGauge
                      score={result.core_score}
                      label={scoreLabel}
                      hint={scoreHint}
                    />
                    <div className="flex flex-col justify-center gap-5 border-t border-border pt-5 md:border-l md:border-t-0 md:pl-6 md:pt-0">
                      <div>
                        <p className="text-xs uppercase tracking-wider text-text-muted">
                          Layer 1 — Structure
                        </p>
                        <p className="tabular-nums text-2xl font-semibold text-text">
                          {result.layer1.score}
                          <span className="text-base font-normal text-text-muted">/100</span>
                        </p>
                      </div>
                      {result.layer2 ? (
                        <div>
                          <p className="text-xs uppercase tracking-wider text-text-muted">
                            Layer 2 — Skill match
                          </p>
                          <p className="tabular-nums text-2xl font-semibold text-text">
                            {result.layer2.score}
                            <span className="text-base font-normal text-text-muted">/100</span>
                          </p>
                        </div>
                      ) : result.jd_provided ? (
                        <div>
                          <p className="text-xs uppercase tracking-wider text-text-muted">
                            Layer 2 — Skill match
                          </p>
                          <p className="text-sm leading-relaxed text-text-muted">
                            Not applicable — JD has no extractable skills to match
                          </p>
                        </div>
                      ) : null}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="space-y-3">
                <h3 className="text-sm font-medium text-text">
                  Layer 1 — Structure &amp; Hygiene
                  <span className="ml-2 tabular-nums text-text-muted">
                    {result.layer1.score}/100
                  </span>
                </h3>
                <CheckGrid checks={result.layer1.checks} />
              </div>

              {result.jd_provided && result.layer2 && (
                <div className="space-y-3">
                  <h3 className="text-sm font-medium text-text">
                    Layer 2 — Skill Match
                    <span className="ml-2 tabular-nums text-text-muted">
                      {result.layer2.score}/100
                    </span>
                  </h3>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <p className="mb-2 text-xs uppercase tracking-wider text-text-muted">
                        Matched required
                      </p>
                      <SkillPills skills={result.layer2.matched_required} variant="matched" />
                    </div>
                    <div>
                      <p className="mb-2 text-xs uppercase tracking-wider text-text-muted">
                        Missing required
                      </p>
                      <SkillPills
                        skills={result.layer2.missing_required}
                        variant="missing"
                        emptyLabel="All required skills matched"
                      />
                    </div>
                  </div>
                  {!!result.layer2.matched_preferred?.length && (
                    <div>
                      <p className="mb-2 text-xs uppercase tracking-wider text-text-muted">
                        Matched preferred
                      </p>
                      <SkillPills skills={result.layer2.matched_preferred} variant="preferred" />
                    </div>
                  )}
                  {!!result.layer2.missing_preferred?.length && (
                    <div>
                      <p className="mb-2 text-xs uppercase tracking-wider text-text-muted">
                        Missing preferred
                      </p>
                      <SkillPills skills={result.layer2.missing_preferred} variant="missing" />
                    </div>
                  )}
                  {result.layer2.experience_note && (
                    <Alert>
                      <AlertDescription className="text-xs">
                        {result.layer2.experience_note}
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}
            </section>

            <section className="space-y-4 border-t border-border pt-8">
              <StepLabel
                step={3}
                title="AI Suggestions"
                subtitle="Optional — review every change before export"
              />
              <p className="text-xs text-text-muted">
                One Groq API call — review every change before export
              </p>
              <Button onClick={handleRewrite} disabled={loading !== null}>
                {loading === "rewrite" && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Get AI Suggestions
              </Button>

              {rewrite && (
                <div className="space-y-3">
                  {rewrite.change_log?.length > 0 && (
                    <Card>
                      <CardHeader className="p-4 pb-2">
                        <CardTitle className="text-xs font-medium uppercase tracking-wider text-text-muted">
                          What changed
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="p-4 pt-0">
                        <ul className="list-disc space-y-1 pl-4 text-xs leading-relaxed text-text-muted">
                          {rewrite.change_log.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}
                  <BeforeAfter original={result.resume_struct} rewritten={rewrite} />
                </div>
              )}
            </section>

            <section className="space-y-4 border-t border-border pt-8">
              <StepLabel step={4} title="Download" subtitle="Generate polished resume files" />
              <p className="text-xs text-text-muted">
                Uses AI suggestions if available; otherwise exports parsed content
              </p>

              {isCustom ? (
                <Alert>
                  <AlertDescription className="text-xs">
                    Custom templates support DOCX only. PDF/TeX require built-in templates.
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="flex flex-wrap gap-4">
                  {(
                    [
                      ["DOCX", fmtDocx, setFmtDocx],
                      ["PDF", fmtPdf, setFmtPdf],
                      ["TeX", fmtTex, setFmtTex],
                    ] as const
                  ).map(([label, checked, setter]) => (
                    <label
                      key={label}
                      className="flex cursor-pointer items-center gap-2 text-xs text-text-muted"
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(e) => setter(e.target.checked)}
                        className="rounded border-border bg-canvas focus-ring"
                      />
                      {label}
                    </label>
                  ))}
                </div>
              )}

              <Button variant="outline" onClick={handleGenerate} disabled={loading !== null}>
                {loading === "generate" && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Generate &amp; Download
              </Button>
            </section>
          </>
        )}

        {!result && loading !== "analyze" && (
          <Card className="border-dashed bg-transparent">
            <CardContent className="py-10 text-center text-xs text-text-muted">
              Upload a resume and click Analyze to see your ATS score.
            </CardContent>
          </Card>
        )}

        <footer className="border-t border-border pt-6 text-[11px] leading-relaxed text-text-muted">
          ATS Compatibility Score is deterministic. AI suggestions are optional and never
          fabricate experience. Independent tool — not affiliated with any employer ATS.
        </footer>
      </main>
    </div>
  );
}
