import type {
  AnalyzeParams,
  AnalyzeResponse,
  GenerateParams,
  RewriteRequest,
  RewriteResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseErrorResponse(res: Response): Promise<string> {
  try {
    const data: { detail?: string | { msg?: string }[] } = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail
        .map((e) => (typeof e === "object" && e?.msg ? e.msg : String(e)))
        .join("; ");
    }
  } catch {
    /* ignore */
  }
  if (res.status === 0 || res.type === "error") {
    return "Network error — is the API running at " + API_BASE + "?";
  }
  return `Request failed (${res.status} ${res.statusText})`;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new ApiError(await parseErrorResponse(res), res.status);
  }
  return res.json() as Promise<T>;
}

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/health`);
  return handleResponse(res);
}

export async function analyzeResume(
  params: AnalyzeParams,
): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append("resume", params.resume);
  form.append("template", params.template);
  if (params.jdText?.trim()) {
    form.append("jd_text", params.jdText.trim());
  }
  if (params.jdFile) {
    form.append("jd_file", params.jdFile);
  }

  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    body: form,
  });
  return handleResponse<AnalyzeResponse>(res);
}

export async function rewriteResume(
  body: RewriteRequest,
): Promise<RewriteResponse> {
  const res = await fetch(`${API_BASE}/api/rewrite`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<RewriteResponse>(res);
}

export async function generateResume(
  params: GenerateParams,
): Promise<{ blob: Blob; filename: string }> {
  const form = new FormData();
  form.append("resume_json", JSON.stringify(params.resumeStruct));
  form.append("template", params.template);
  form.append("format", params.format);
  if (params.rewritten) {
    form.append("rewritten_json", JSON.stringify(params.rewritten));
  }
  if (params.customTemplate) {
    form.append("custom_template", params.customTemplate);
  }

  const res = await fetch(`${API_BASE}/api/generate`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    throw new ApiError(await parseErrorResponse(res), res.status);
  }

  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^";\n]+)"?/);
  const filename = match?.[1] || `resume.${params.format}`;
  return { blob, filename };
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
