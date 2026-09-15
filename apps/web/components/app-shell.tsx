"use client";

import {
  BookOpen,
  ListChecks,
  LogOut,
  MessageSquare,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { clearAccessToken } from "@/lib/auth-token";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "问答", icon: MessageSquare },
  { href: "/kbs", label: "知识库", icon: BookOpen },
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
    <div className="flex min-h-screen bg-background font-sans text-foreground">
      <nav
        aria-label="主导航"
        className="flex w-14 shrink-0 flex-col gap-6 border-r border-sidebar-border bg-sidebar px-2 py-4 md:w-56 md:px-3 md:py-6"
      >
        <div className="px-2">
          <p className="hidden text-[1.05rem] font-extrabold tracking-tight text-sidebar-foreground md:block">
            企业知识助手
          </p>
          <p className="text-center text-xs font-extrabold text-primary md:hidden" aria-hidden>
            知
          </p>
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
                  className={cn(
                    "flex items-center gap-2 rounded-md px-2.5 py-2 text-sm text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground md:px-3",
                    active &&
                      "bg-primary/12 font-semibold text-primary hover:bg-primary/12 hover:text-primary",
                  )}
                >
                  <Icon className="size-5 shrink-0" aria-hidden="true" />
                  <span className="hidden md:inline">{label}</span>
                </Link>
              </li>
            );
          })}
        </ul>

        <div className="mt-auto space-y-3">
          <Separator />
          <Button
            type="button"
            variant="ghost"
            className="w-full justify-start gap-2 px-2.5 text-muted-foreground md:px-3"
            onClick={signOut}
          >
            <LogOut className="size-5 shrink-0" aria-hidden="true" />
            <span className="hidden md:inline">退出</span>
          </Button>
        </div>
      </nav>
      <main className="flex min-w-0 flex-1 flex-col">{children}</main>
    </div>
  );
}
