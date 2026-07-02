"use client";

import { cn } from "@/lib/utils";
import { FileDropzone } from "@/components/analyze/FileDropzone";
import { Textarea } from "@/components/ui/textarea";

type JdMode = "paste" | "upload";

interface JdInputProps {
  mode: JdMode;
  onModeChange: (mode: JdMode) => void;
  jdText: string;
  onJdTextChange: (text: string) => void;
  jdFile: File | null;
  onJdFileChange: (file: File | null) => void;
  disabled?: boolean;
}

export function JdInput({
  mode,
  onModeChange,
  jdText,
  onJdTextChange,
  jdFile,
  onJdFileChange,
  disabled,
}: JdInputProps) {
  return (
    <div className="flex w-full flex-col">
      <div
        className="grid w-full grid-cols-2 rounded-md border border-border bg-canvas p-0.5"
        role="tablist"
        aria-label="Job description input method"
      >
        {(
          [
            ["paste", "Paste text"],
            ["upload", "Upload file"],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            type="button"
            role="tab"
            aria-selected={mode === value}
            disabled={disabled}
            onClick={() => {
              if (value === mode) return;
              if (value === "paste") onJdFileChange(null);
              else onJdTextChange("");
              onModeChange(value);
            }}
            className={cn(
              "rounded-sm px-3 py-2 text-xs font-medium transition-colors duration-micro",
              mode === value
                ? "bg-surface text-text shadow-sm"
                : "text-text-muted hover:text-text",
              disabled && "cursor-not-allowed opacity-50",
            )}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mt-3 w-full" role="tabpanel">
        {mode === "paste" ? (
          <Textarea
            placeholder="Paste the full job description here…"
            className="min-h-[140px] w-full resize-y"
            value={jdText}
            onChange={(e) => onJdTextChange(e.target.value)}
            disabled={disabled}
            aria-label="Job description text"
          />
        ) : (
          <FileDropzone
            accept=".pdf,.docx,.txt"
            label="Drop JD file here"
            hint="PDF, DOCX, or TXT"
            file={jdFile}
            onFile={onJdFileChange}
            disabled={disabled}
            className="w-full min-h-[140px]"
          />
        )}
      </div>
    </div>
  );
}
