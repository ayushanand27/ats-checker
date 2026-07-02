"use client";

import { Loader2, MessageSquare, Send } from "lucide-react";
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

  const scrollToBottom = useCallback(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, []);

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
    if (!started && jdText.trim() && !disabled) {
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

  if (!jdText.trim()) {
    return (
      <div className="rounded-md border border-dashed border-border bg-canvas/50 px-4 py-10 text-center text-sm text-text-muted">
        Paste or upload a job description first — the chat will ask tailored questions to
        build your resume.
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-[380px] w-full flex-col rounded-md border border-border bg-canvas">
      <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div className="flex items-center gap-2 text-sm font-medium text-text">
          <MessageSquare className="h-4 w-4 text-accent" strokeWidth={1.5} />
          Resume builder chat
        </div>
        <span className="text-xs text-text-muted">
          {isComplete ? "Complete" : `${progress}%`}
        </span>
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
            Thorough interview (~20–30 questions) · metrics &amp; tech stack per bullet · Groq free tier
          </p>
        </div>
      )}
    </div>
  );
}
