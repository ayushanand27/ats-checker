import type { RewriteResponse, ResumeStruct } from "./types";

/** Merge AI rewrite fields into a resume struct for re-scoring / export. */
export function mergeRewrite(
  original: ResumeStruct,
  rewritten: RewriteResponse,
): ResumeStruct {
  return {
    ...original,
    summary: rewritten.summary || original.summary,
    skills: rewritten.skills?.length ? rewritten.skills : original.skills,
    experience: rewritten.experience?.length ? rewritten.experience : original.experience,
    education: rewritten.education?.length ? rewritten.education : original.education,
    projects: rewritten.projects?.length ? rewritten.projects : original.projects,
  };
}
