# Shared UI components

Framework: Next.js 16 App Router + React 19. Component library: **custom CSS Modules** (no shadcn yet). Icons: `@phosphor-icons/react`.

## StatusPill

- Path: `apps/web/components/status-pill.tsx`
- Description: Maps job/document status strings to Chinese labels and pill styles
- Props: `status: string`

```tsx
import ui from "./ui.module.css";

const STATUS_MAP: Record<string, { label: string; className: string }> = {
  pending: { label: "待处理", className: ui.statusPending },
  indexing: { label: "索引中", className: ui.statusIndexing },
  ready: { label: "就绪", className: ui.statusReady },
  failed: { label: "失败", className: ui.statusFailed },
  completed: { label: "完成", className: ui.statusReady },
  running: { label: "运行中", className: ui.statusIndexing },
};

type StatusPillProps = {
  status: string;
};

export function StatusPill({ status }: StatusPillProps) {
  const key = status.toLowerCase();
  const mapped = STATUS_MAP[key] ?? {
    label: status,
    className: ui.statusPending,
  };
  return (
    <span className={`${ui.statusPill} ${mapped.className}`}>
      {mapped.label}
    </span>
  );
}
```

## AuthGate

- Path: `apps/web/components/auth-gate.tsx`
- Description: Client auth check; redirects to `/login` when no token
- Props: `children: ReactNode`

```tsx
"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { getAccessToken } from "@/lib/auth-token";

type AuthGateProps = {
  children: ReactNode;
};

export function AuthGate({ children }: AuthGateProps) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getAccessToken()) {
      router.replace("/login");
      return;
    }
    setReady(true);
  }, [router]);

  if (!ready) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          background: "var(--color-background)",
        }}
        aria-busy="true"
      >
        <p style={{ color: "var(--color-muted-foreground)" }}>加载中…</p>
      </div>
    );
  }

  return children;
}
```

## UI primitives (`ui.module.css`)

- Path: `apps/web/components/ui.module.css`
- Description: Shared button, input, label, field, card, error, status pill, skeleton classes

```css
.btnBase {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-weight: 600;
  font-size: 0.9375rem;
  cursor: pointer;
  transition: opacity var(--transition-fast), background var(--transition-fast);
  border: none;
}

.btnPrimary {
  composes: btnBase;
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.btnPrimary:hover:not(:disabled) {
  opacity: 0.92;
}

.btnPrimary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btnSecondary {
  composes: btnBase;
  background: var(--color-muted);
  color: var(--color-foreground);
  border: 1px solid var(--color-border);
}

.btnAccent {
  composes: btnBase;
  background: var(--color-accent);
  color: var(--color-on-accent);
}

.btnDestructive {
  composes: btnBase;
  background: var(--color-destructive);
  color: var(--color-on-destructive);
}

.input {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-card);
  color: var(--color-card-foreground);
  font-family: var(--font-sans);
  font-size: 0.9375rem;
}

.input:focus {
  outline: 2px solid var(--color-ring);
  outline-offset: 2px;
}

.label {
  display: block;
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: var(--space-xs);
}

.field {
  margin-bottom: var(--space-md);
}

.card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
}

.errorSummary {
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--color-destructive) 12%, white);
  color: var(--color-destructive);
  font-size: 0.875rem;
  margin-bottom: var(--space-md);
}

.statusPill {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: 2px var(--space-sm);
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid var(--color-border);
}

.statusPending {
  background: var(--color-muted);
  color: var(--color-muted-foreground);
}

.statusIndexing {
  background: color-mix(in srgb, var(--color-secondary) 20%, white);
  color: var(--color-foreground);
}

.statusReady {
  background: color-mix(in srgb, var(--color-primary) 15%, white);
  color: var(--color-primary);
}

.statusFailed {
  background: color-mix(in srgb, var(--color-destructive) 12%, white);
  color: var(--color-destructive);
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-muted) 25%,
    color-mix(in srgb, var(--color-muted) 70%, white) 50%,
    var(--color-muted) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
  border-radius: var(--radius-md);
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
```
