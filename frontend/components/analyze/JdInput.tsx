"use client";

import { Loader2 } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { FileDropzone } from "@/components/analyze/FileDropzone";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

type JdMode = "paste" | "upload" | "url";

interface JdInputProps {
  mode: JdMode;
  onModeChange: (mode: JdMode) => void;
  jdText: string;
  onJdTextChange: (text: string) => void;
  jdFile: File | null;
  onJdFileChange: (file: File | null) => void;
  jdUrl: string;
  onJdUrlChange: (url: string) => void;
  onFetchUrl?: (url: string) => Promise<void>;
  disabled?: boolean;
}

export function JdInput({
  mode,
  onModeChange,
  jdText,
  onJdTextChange,
  jdFile,
  onJdFileChange,
  jdUrl,
  onJdUrlChange,
  onFetchUrl,
  disabled,
}: JdInputProps) {
  const [fetching, setFetching] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const handleFetch = async () => {
    if (!onFetchUrl || !jdUrl.trim()) return;
    setFetching(true);
    setFetchError(null);
    try {
      await onFetchUrl(jdUrl.trim());
      onModeChange("paste");
    } catch (e) {
      setFetchError(e instanceof Error ? e.message : "Could not fetch URL");
    } finally {
      setFetching(false);
    }
  };

  return (
    <div className="flex w-full flex-col">
      <div
        className="grid w-full grid-cols-3 rounded-md border border-border bg-canvas p-0.5"
        role="tablist"
        aria-label="Job description input method"
      >
        {(
          [
            ["paste", "Paste text"],
            ["upload", "Upload file"],
            ["url", "From URL"],
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
              if (value === "paste") {
                onJdFileChange(null);
                onJdUrlChange("");
              } else if (value === "upload") {
                onJdTextChange("");
                onJdUrlChange("");
              } else {
                onJdTextChange("");
                onJdFileChange(null);
              }
              onModeChange(value);
            }}
            className={cn(
              "rounded-sm px-2 py-2 text-xs font-medium transition-colors duration-micro",
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
        ) : mode === "upload" ? (
          <FileDropzone
            accept=".pdf,.docx,.txt"
            label="Drop JD file here"
            hint="PDF, DOCX, or TXT"
            file={jdFile}
            onFile={onJdFileChange}
            disabled={disabled}
            className="w-full min-h-[140px]"
          />
        ) : (
          <div className="space-y-2">
            <div className="flex gap-2">
              <Input
                type="url"
                placeholder="https://company.com/careers/job-id"
                value={jdUrl}
                onChange={(e) => onJdUrlChange(e.target.value)}
                disabled={disabled || fetching}
                aria-label="Job posting URL"
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => void handleFetch()}
                disabled={disabled || fetching || !jdUrl.trim()}
              >
                {fetching ? <Loader2 className="h-4 w-4 animate-spin" /> : "Fetch"}
              </Button>
            </div>
            <p className="text-[11px] text-text-muted">
              Pulls text from public job pages (LinkedIn may block). Fetched text loads into Paste.
            </p>
            {fetchError && (
              <p className="text-xs text-fail" role="alert">
                {fetchError}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
