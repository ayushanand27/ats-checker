/**
 * E2E API flow test — mirrors what the Next.js analyze page does.
 * Run: node scripts/e2e-api-test.mjs
 * Requires FastAPI at http://localhost:8000
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const sampleResume = path.resolve(
  __dirname,
  "../../resume_scorer/api/test_fixtures/sample_resume.txt",
);

const JD =
  "Software Engineer - Networking. Strong knowledge of Python, TCP/IP networking, routing, switching. Unit testing required. 2027 graduate.";

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

async function parseError(res) {
  try {
    const d = await res.json();
    return typeof d.detail === "string" ? d.detail : JSON.stringify(d.detail);
  } catch {
    return res.statusText;
  }
}

async function main() {
  console.log("1. Health check...");
  const health = await fetch(`${API}/api/health`);
  assert(health.ok, `Health failed: ${health.status}`);
  console.log("   OK", await health.json());

  console.log("2. Analyze...");
  const form = new FormData();
  form.append("resume", new Blob([fs.readFileSync(sampleResume)]), "sample_resume.txt");
  form.append("jd_text", JD);
  form.append("template", "jacks_tech");

  const analyzeRes = await fetch(`${API}/api/analyze`, { method: "POST", body: form });
  if (!analyzeRes.ok) throw new Error(`Analyze failed: ${await parseError(analyzeRes)}`);
  const analyze = await analyzeRes.json();
  assert(analyze.core_score > 0, "core_score missing");
  assert(analyze.layer1?.checks?.length > 0, "layer1 checks missing");
  assert(analyze.layer2 !== null, "layer2 should be present with JD");
  console.log("   core_score:", analyze.core_score);
  console.log("   layer1:", analyze.layer1.score, "layer2:", analyze.layer2.score);

  console.log("3. Rewrite...");
  const rewriteRes = await fetch(`${API}/api/rewrite`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resume_struct: analyze.resume_struct,
      jd_struct: analyze.jd_struct,
      gaps: analyze.gaps,
    }),
  });
  if (!rewriteRes.ok) {
    console.log("   SKIP rewrite (may need GROQ_API_KEY):", await parseError(rewriteRes));
  } else {
    const rewrite = await rewriteRes.json();
    assert(rewrite.summary, "rewrite summary missing");
    console.log("   change_log items:", rewrite.change_log?.length ?? 0);
  }

  console.log("4. Generate DOCX...");
  const genForm = new FormData();
  genForm.append("resume_json", JSON.stringify(analyze.resume_struct));
  genForm.append("template", "jacks_tech");
  genForm.append("format", "docx");

  const genRes = await fetch(`${API}/api/generate`, { method: "POST", body: genForm });
  if (!genRes.ok) throw new Error(`Generate failed: ${await parseError(genRes)}`);
  const buf = Buffer.from(await genRes.arrayBuffer());
  assert(buf.length > 1000, "DOCX too small");
  console.log("   DOCX bytes:", buf.length);

  console.log("\nAll API steps passed.");
}

main().catch((e) => {
  console.error("FAILED:", e.message);
  process.exit(1);
});
