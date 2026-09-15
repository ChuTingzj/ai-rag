# Layouts

## AppShell

- Path: `apps/web/components/app-shell.tsx` + `app-shell.module.css`
- Description: Left sidebar (220px → 64px icon-only &lt;768px) with brand, nav links (问答/知识库/任务), sign-out; main canvas for children

```tsx
"use client";

import {
  ChatCircle,
  Folder,
  ListChecks,
  SignOut,
} from "@phosphor-icons/react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { clearAccessToken } from "@/lib/auth-token";

import styles from "./app-shell.module.css";

const NAV = [
  { href: "/", label: "问答", icon: ChatCircle },
  { href: "/kbs", label: "知识库", icon: Folder },
  { href: "/jobs", label: "任务", icon: ListChecks },
] as const;

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();

  function signOut() {
    clearAccessToken();
    router.push("/login");
  }

  return (
    <div className={styles.shell}>
      <nav className={styles.nav} aria-label="主导航">
        <div className={styles.brand}>
          <span>企业知识助手</span>
        </div>
        <ul className={styles.navList}>
          {NAV.map(({ href, label, icon: Icon }) => {
            const active =
              href === "/"
                ? pathname === "/"
                : pathname === href || pathname.startsWith(`${href}/`);
            return (
              <li key={href}>
                <Link
                  href={href}
                  className={`${styles.navLink} ${active ? styles.navLinkActive : ""}`}
                >
                  <Icon size={20} aria-hidden="true" />
                  <span className="label">{label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
        <button
          type="button"
          className={styles.navLink}
          onClick={signOut}
          style={{ marginTop: "auto", border: "none", background: "transparent", width: "100%" }}
        >
          <SignOut size={20} aria-hidden="true" />
          <span className="label">退出</span>
        </button>
      </nav>
      <main className={styles.main}>{children}</main>
    </div>
  );
}
```

```css
.shell {
  display: flex;
  min-height: 100vh;
  background: var(--color-background);
  color: var(--color-foreground);
  font-family: var(--font-sans);
}

.nav {
  width: 220px;
  flex-shrink: 0;
  border-right: 1px solid var(--color-border);
  background: var(--color-card);
  padding: var(--space-lg) var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.brand {
  font-weight: 800;
  font-size: 1.05rem;
  letter-spacing: -0.02em;
}

.navList {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.navLink {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  color: var(--color-muted-foreground);
  text-decoration: none;
  transition: background var(--transition-fast), color var(--transition-fast);
  cursor: pointer;
}

.navLink:hover {
  background: var(--color-muted);
  color: var(--color-foreground);
}

.navLinkActive {
  background: color-mix(in srgb, var(--color-primary) 12%, transparent);
  color: var(--color-primary);
  font-weight: 600;
}

.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

@media (max-width: 767px) {
  .nav {
    width: 64px;
    padding: var(--space-md) var(--space-sm);
  }

  .brand span {
    display: none;
  }

  .navLink span.label {
    display: none;
  }
}
```

## Root layout

- Path: `apps/web/app/layout.tsx`
- Description: HTML shell, `lang="zh-CN"`, metadata title「企业知识助手」, imports globals.css
