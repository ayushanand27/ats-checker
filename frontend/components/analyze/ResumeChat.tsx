"use client";

import { ChevronDown, ChevronUp, Loader2, MessageSquare, Send } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { resumeChatTurn } from "@/lib/api";
import type { ChatMessage, ResumeStruct } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ResumeChatProps {
  jdText: string;
  disabled?: boolean;
  onDraftChange?: (draft: ResumeStruct, isComplete: boolean) => void;
}

interface StoredChat {
  messages: ChatMessage[];
  draft: ResumeStruct | null;
  progress: number;
  isComplete: boolean;
  started: boolean;
}

function storageKey(jd: string) {
  return `resumematch-chat-${jd.slice(0, 120).replace(/\s+/g, "_")}`;
}

function LiveDraftPanel({ draft }: { draft: ResumeStruct | null }) {
  const [open, setOpen] = useState(true);
  if (!draft) return null;

  const contact = draft.contact ?? {};
  const expCount = draft.experience?.length ?? 0;
  const projCount = draft.projects?.length ?? 0;
  const skillCount = draft.skills?.length ?? 0;

  return (
    <div className="rounded-md border border-border bg-surface/80">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-3 py-2 text-left text-xs font-medium text-text"
      >
        Live draft
        {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
      </button>
      {open && (
        <div className="space-y-2 border-t border-border px-3 py-2 text-xs text-text-muted">
          <p>
            <span className="text-text">{draft.name || "—"}</span>
          </p>
          <p>{contact.email || "No email yet"}</p>
          <p>
            {skillCount} skills · {expCount} roles · {projCount} projects
          </p>
          {draft.summary && (
            <p className="line-clamp-3 leading-relaxed">{draft.summary}</p>
          )}
        </div>
      )}
    </div>
  );
}

export function ResumeChat({ jdText, disabled, onDraftChange }: ResumeChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState<ResumeStruct | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [started, setStarted] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const restoredRef = useRef(false);

  const scrollToBottom = useCallback(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, []);

  // Restore from localStorage
  useEffect(() => {
    if (!jdText.trim() || disabled) return;
    restoredRef.current = false;
    try {
      const raw = localStorage.getItem(storageKey(jdText));
      if (!raw) return;
      const saved: StoredChat = JSON.parse(raw);
      if (saved.messages?.length) {
        setMessages(saved.messages);
        setDraft(saved.draft);
        setProgress(saved.progress ?? 0);
        setIsComplete(saved.isComplete ?? false);
        setStarted(saved.started ?? true);
        if (saved.draft) onDraftChange?.(saved.draft, saved.isComplete ?? false);
        restoredRef.current = true;
      }
    } catch {
      /* ignore corrupt storage */
    }
  }, [disabled, jdText, onDraftChange]);

  // Persist to localStorage
  useEffect(() => {
    if (!jdText.trim() || !started) return;
    const payload: StoredChat = {
      messages,
      draft,
      progress,
      isComplete,
      started,
    };
    try {
      localStorage.setItem(storageKey(jdText), JSON.stringify(payload));
    } catch {
      /* quota exceeded */
    }
  }, [draft, isComplete, jdText, messages, progress, started]);

  const runTurn = useCallback(
    async (userMessage?: string) => {
      if (!jdText.trim()) {
        setError("Add a job description above to start the resume chat.");
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const res = await resumeChatTurn({
          jd_text: jdText.trim(),
          messages,
          user_message: userMessage ?? null,
          draft,
        });
        setMessages(res.messages);
        setDraft(res.draft);
        setIsComplete(res.is_complete);
        setProgress(res.progress_percent);
        onDraftChange?.(res.draft, res.is_complete);
        setStarted(true);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Chat failed");
      } finally {
        setLoading(false);
        setTimeout(scrollToBottom, 50);
        setTimeout(() => inputRef.current?.focus(), 80);
      }
    },
    [draft, jdText, messages, onDraftChange, scrollToBottom],
  );

  useEffect(() => {
    if (!started && jdText.trim() && !disabled && !restoredRef.current) {
      void runTurn();
    }
  }, [disabled, jdText, runTurn, started]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || loading || isComplete || disabled) return;
    setInput("");
    void runTurn(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    localStorage.removeItem(storageKey(jdText));
    setMessages([]);
    setDraft(null);
    setStarted(false);
    setIsComplete(false);
    setProgress(0);
    restoredRef.current = false;
    onDraftChange?.({} as ResumeStruct, false);
  };

  if (!jdText.trim()) {
    return (
      <div className="rounded-md border border-dashed border-border bg-canvas/50 px-4 py-10 text-center text-sm text-text-muted">
        Paste or upload a job description first — the chat will ask tailored questions to
        build your resume.
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-[380px] w-full flex-col gap-2 lg:min-h-[420px]">
      <LiveDraftPanel draft={draft} />

      <div className="flex min-h-0 flex-1 flex-col rounded-md border border-border bg-canvas">
        <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
          <div className="flex items-center gap-2 text-sm font-medium text-text">
            <MessageSquare className="h-4 w-4 text-accent" strokeWidth={1.5} />
            Resume builder chat
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-muted">
              {isComplete ? "Complete" : `${progress}%`}
            </span>
            {started && (
              <Button type="button" variant="ghost" size="xs" onClick={clearChat}>
                Reset
              </Button>
            )}
          </div>
        </div>

        {!isComplete && (
          <div className="px-4 pt-3">
            <Progress value={progress || (started ? 10 : 0)} className="h-1" />
          </div>
        )}

        <div
          ref={scrollRef}
          className="flex-1 space-y-3 overflow-y-auto px-4 py-4"
          aria-live="polite"
        >
          {messages.length === 0 && loading && (
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              Starting interview…
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={`${msg.role}-${i}`}
              className={cn(
                "max-w-[92%] rounded-md px-3 py-2 text-sm leading-relaxed",
                msg.role === "assistant"
                  ? "bg-surface text-text"
                  : "ml-auto bg-accent/15 text-text",
              )}
            >
              {msg.content}
            </div>
          ))}

          {loading && messages.length > 0 && (
            <div className="flex items-center gap-2 text-xs text-text-muted">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Thinking…
            </div>
          )}
        </div>

        {error && (
          <p className="px-4 pb-2 text-xs text-fail" role="alert">
            {error}
          </p>
        )}

        {isComplete ? (
          <div className="border-t border-border px-4 py-3 text-center text-xs text-score-high">
            Resume draft ready — click Analyze below to score and export.
          </div>
        ) : (
          <div className="border-t border-border p-3">
            <div className="flex gap-2">
              <Textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your answer…"
                className="min-h-[44px] max-h-28 resize-none"
                disabled={loading || disabled || !started}
                aria-label="Chat message"
              />
              <Button
                type="button"
                size="icon"
                onClick={handleSend}
                disabled={loading || disabled || !input.trim() || !started}
                aria-label="Send message"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
            <p className="mt-2 text-[11px] text-text-muted">
              Thorough interview (~20–30 questions) · progress saved in browser · Groq
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
