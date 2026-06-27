import { cn } from "@/lib/utils";

type PillVariant = "matched" | "missing" | "preferred";

interface SkillPillsProps {
  skills: string[];
  variant?: PillVariant;
  emptyLabel?: string;
}

const variantClass: Record<PillVariant, string> = {
  matched: "border-border bg-surface text-pass",
  missing: "border-border bg-surface text-fail",
  preferred: "border-border bg-surface text-text-muted",
};

export function SkillPills({
  skills,
  variant = "matched",
  emptyLabel = "None",
}: SkillPillsProps) {
  if (!skills.length) {
    return <p className="text-xs text-text-muted">{emptyLabel}</p>;
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {skills.map((skill) => (
        <span
          key={skill}
          className={cn(
            "inline-flex rounded-md border px-2 py-0.5 text-xs font-medium",
            variantClass[variant],
          )}
        >
          {skill}
        </span>
      ))}
    </div>
  );
}
