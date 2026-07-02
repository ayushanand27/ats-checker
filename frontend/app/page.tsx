import Link from "next/link";
import { ArrowRight, FileSearch, MessageSquare, Sparkles, Download } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const FEATURES = [
  {
    icon: FileSearch,
    title: "2-Layer ATS Score",
    desc: "Structure checks + semantic skill match against the JD",
  },
  {
    icon: MessageSquare,
    title: "AI Resume Chat",
    desc: "Paste a JD and build your resume step-by-step via Groq chat",
  },
  {
    icon: Sparkles,
    title: "AI Rewrite",
    desc: "Optional Groq suggestions you review before using",
  },
  {
    icon: Download,
    title: "Multi-Format Export",
    desc: "PDF, DOCX, and TeX from one structured source",
  },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-canvas text-text">
      <header className="mx-auto flex max-w-tool items-center justify-between px-4 py-5 sm:px-6">
        <span className="font-serif text-lg tracking-tight text-text">
          ResumeMatch
        </span>
        <Link
          href="/analyze"
          className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
        >
          Open tool
        </Link>
      </header>

      <main className="mx-auto max-w-tool px-4 pb-24 pt-16 sm:px-6 sm:pt-20">
        <div className="max-w-2xl">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-text-muted">
            Professional ATS Suite
          </p>
          <h1 className="mt-4 font-serif text-4xl leading-[1.1] tracking-tight text-text sm:text-5xl">
            Score your resume with precision.
          </h1>
          <p className="mt-6 text-[15px] leading-relaxed text-text-muted">
            Match against any job description, review AI rewrite suggestions, and
            export polished documents — the workflow recruiters charge hundreds for,
            built as a precise audit instrument.
          </p>
          <Link
            href="/analyze"
            className={cn(
              buttonVariants({ size: "lg" }),
              "mt-10 inline-flex gap-2",
            )}
          >
            Get Started
            <ArrowRight className="h-4 w-4" strokeWidth={1.5} />
          </Link>
        </div>

        <div className="mt-20 grid gap-3 sm:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="rounded-md border border-border bg-surface p-5 transition-colors duration-micro hover:bg-surface-hover"
            >
              <Icon className="h-5 w-5 text-accent" strokeWidth={1.5} />
              <h3 className="mt-3 text-sm font-semibold text-text">{title}</h3>
              <p className="mt-1.5 text-xs leading-relaxed text-text-muted">{desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
