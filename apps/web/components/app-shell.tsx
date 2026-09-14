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
