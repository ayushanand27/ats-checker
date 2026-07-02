"use client";

import { LogOut, User } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { AuthDialog } from "@/components/auth/AuthDialog";
import { Button } from "@/components/ui/button";

export function AccountMenu({ onAuthChange }: { onAuthChange?: () => void }) {
  const { user, loading, logout } = useAuth();
  const [authOpen, setAuthOpen] = useState(false);

  if (loading) {
    return <span className="text-xs text-text-muted">…</span>;
  }

  if (!user) {
    return (
      <>
        <Button variant="outline" size="sm" onClick={() => setAuthOpen(true)}>
          <User className="mr-1 h-3.5 w-3.5" />
          Sign in
        </Button>
        <AuthDialog open={authOpen} onOpenChange={setAuthOpen} onSuccess={onAuthChange} />
      </>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="hidden text-xs text-text-muted sm:inline">
        {user.name || user.email}
      </span>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => {
          logout();
          onAuthChange?.();
        }}
        aria-label="Sign out"
      >
        <LogOut className="mr-1 h-3.5 w-3.5" />
        Sign out
      </Button>
    </div>
  );
}
