import type { ResumeStruct, RewriteResponse } from "@/lib/types";
import { ResumePreviewCompare } from "@/components/analyze/ResumePreview";

interface BeforeAfterProps {
  original: ResumeStruct;
  rewritten: RewriteResponse;
}

export function BeforeAfter({ original, rewritten }: BeforeAfterProps) {
  return <ResumePreviewCompare original={original} rewritten={rewritten} />;
}
