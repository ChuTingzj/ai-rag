"use client";

import {
  BookOpen,
  ListChecks,
  LogOut,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { clearAccessToken } from "@/lib/auth-token";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "问答", icon: MessageSquare },
  { href: "/kbs", label: "知识库", icon: BookOpen },
  { href: "/jobs", label: "任务", icon: ListChecks },
] as const;

const SIDEBAR_COLLAPSED_KEY = "ai-rag.sidebar-collapsed";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      setCollapsed(localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "1");
    } catch {
      // ignore storage errors
    }
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    try {
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, collapsed ? "1" : "0");
    } catch {
      // ignore storage errors
    }
  }, [collapsed, ready]);

  function signOut() {
    clearAccessToken();
    router.push("/login");
  }

  return (
    <div className="flex min-h-screen bg-background font-sans text-foreground">
      <nav
        id="app-shell-sidebar"
        aria-label="主导航"
        data-collapsed={collapsed || undefined}
        className={cn(
          "flex shrink-0 flex-col gap-6 border-r border-sidebar-border bg-sidebar py-4 text-sidebar-foreground transition-[width] duration-200 ease-out md:py-6",
          collapsed ? "w-14 px-2" : "w-56 px-3",
        )}
      >
        <div
          className={cn(
            "flex items-center gap-2",
            collapsed ? "flex-col px-0" : "px-2",
          )}
        >
          <div className={cn("min-w-0", collapsed && "w-full text-center")}>
            {collapsed ? (
              <p
                className="text-center text-xs font-extrabold text-sidebar-primary"
                aria-hidden
              >
                知
              </p>
            ) : (
              <>
                <p className="text-[1.05rem] font-extrabold tracking-tight text-white">
                  企业知识助手
                </p>
                <p className="mt-1 text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
                  Knowledge RAG
                </p>
              </>
            )}
          </div>

          <Button
            type="button"
            variant="ghost"
            size="icon"
            className={cn(
              "size-8 shrink-0 text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
              !collapsed && "ml-auto",
            )}
            aria-label={collapsed ? "展开侧边栏" : "收起侧边栏"}
            aria-expanded={!collapsed}
            aria-controls="app-shell-sidebar"
            title={collapsed ? "展开侧边栏" : "收起侧边栏"}
            onClick={() => setCollapsed((prev) => !prev)}
          >
            {collapsed ? (
              <PanelLeftOpen className="size-4" aria-hidden="true" />
            ) : (
              <PanelLeftClose className="size-4" aria-hidden="true" />
            )}
          </Button>
        </div>

        <ul className="flex flex-1 flex-col gap-1">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active =
              href === "/"
                ? pathname === "/"
                : pathname === href || pathname.startsWith(`${href}/`);
            return (
              <li key={href}>
                <Link
                  href={href}
                  title={collapsed ? label : undefined}
                  className={cn(
                    "flex items-center gap-2 rounded-lg py-2.5 text-sm font-medium text-sidebar-foreground/65 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                    collapsed ? "justify-center px-2" : "px-3",
                    active &&
                      "bg-sidebar-primary font-semibold text-sidebar-primary-foreground shadow-sm hover:bg-sidebar-primary hover:text-sidebar-primary-foreground",
                  )}
                >
                  <Icon className="size-5 shrink-0" aria-hidden="true" />
                  {!collapsed && <span>{label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>

        <div className="mt-auto space-y-3">
          <Separator className="bg-sidebar-border" />
          <Button
            type="button"
            variant="ghost"
            title={collapsed ? "退出" : undefined}
            className={cn(
              "w-full gap-2 text-sidebar-foreground/65 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
              collapsed ? "justify-center px-2" : "justify-start px-3",
            )}
            onClick={signOut}
          >
            <LogOut className="size-5 shrink-0" aria-hidden="true" />
            {!collapsed && <span>退出</span>}
          </Button>
        </div>
      </nav>
      <main className="flex min-w-0 flex-1 flex-col">{children}</main>
    </div>
  );
}
