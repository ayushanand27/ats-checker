"use client";

import { Loader2 } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

interface AuthDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function AuthDialog({ open, onOpenChange, onSuccess }: AuthDialogProps) {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (mode === "login") {
        await login(email.trim(), password);
      } else {
        await register(email.trim(), password, name.trim() || undefined);
      }
      onOpenChange(false);
      onSuccess?.();
      setPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>
            {mode === "login" ? "Sign in" : "Create your account"}
          </DialogTitle>
          <DialogDescription>
            {mode === "login"
              ? "Access your saved profile and tailor resumes from just a job description."
              : "Save your master profile once — then generate tailored resumes from any JD."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-3">
          {mode === "register" && (
            <div>
              <label className="text-[10px] uppercase tracking-wider text-text-muted">
                Name (optional)
              </label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading}
                className="mt-1"
                autoComplete="name"
              />
            </div>
          )}
          <div>
            <label className="text-[10px] uppercase tracking-wider text-text-muted">
              Email
            </label>
            <Input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              className="mt-1"
              autoComplete="email"
            />
          </div>
          <div>
            <label className="text-[10px] uppercase tracking-wider text-text-muted">
              Password{mode === "register" ? " (min 8 characters)" : ""}
            </label>
            <Input
              type="password"
              required
              minLength={mode === "register" ? 8 : undefined}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              className="mt-1"
              autoComplete={mode === "login" ? "current-password" : "new-password"}
            />
          </div>

          {error && (
            <p className="text-xs text-fail" role="alert">
              {error}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {mode === "login" ? "Sign in" : "Create account"}
          </Button>
        </form>

        <button
          type="button"
          className="text-xs text-accent underline-offset-2 hover:underline"
          onClick={() => {
            setMode((m) => (m === "login" ? "register" : "login"));
            setError(null);
          }}
        >
          {mode === "login"
            ? "New here? Create an account"
            : "Already have an account? Sign in"}
        </button>
      </DialogContent>
    </Dialog>
  );
}
