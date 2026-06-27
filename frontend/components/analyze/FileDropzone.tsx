"use client";

import { Upload } from "lucide-react";
import { useCallback, useState } from "react";
import { cn } from "@/lib/utils";

interface FileDropzoneProps {
  accept: string;
  label: string;
  hint?: string;
  file: File | null;
  onFile: (file: File | null) => void;
  disabled?: boolean;
}

export function FileDropzone({
  accept,
  label,
  hint,
  file,
  onFile,
  disabled,
}: FileDropzoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const inputId = `file-${label.replace(/\s+/g, "-").toLowerCase()}`;

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (disabled) return;
      const f = e.dataTransfer.files?.[0];
      if (f) onFile(f);
    },
    [disabled, onFile],
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={onDrop}
      className={cn(
        "relative rounded-md border border-dashed p-5 text-center transition-colors duration-micro",
        dragOver
          ? "border-accent bg-surface-hover"
          : "border-border bg-surface hover:border-accent/50 hover:bg-surface-hover",
        disabled && "pointer-events-none opacity-50",
      )}
    >
      <input
        id={inputId}
        type="file"
        accept={accept}
        className="absolute inset-0 cursor-pointer opacity-0 focus-visible:outline-none"
        disabled={disabled}
        onChange={(e) => onFile(e.target.files?.[0] ?? null)}
        aria-label={label}
      />
      <Upload className="mx-auto h-5 w-5 text-text-muted" strokeWidth={1.5} />
      <p className="mt-2 text-sm font-medium text-text">{label}</p>
      {hint && <p className="mt-1 text-xs text-text-muted">{hint}</p>}
      {file && (
        <p className="mt-3 inline-block rounded-md border border-border bg-canvas px-2 py-1 text-xs tabular-nums text-text-muted">
          {file.name} · {(file.size / 1024).toFixed(1)} KB
        </p>
      )}
    </div>
  );
}
