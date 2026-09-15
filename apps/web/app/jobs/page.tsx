"use client";

import { ArrowRight, ListChecks } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch, type KnowledgeBaseOut } from "@/lib/api-client";

export default function JobsPage() {
  const [kbs, setKbs] = useState<KnowledgeBaseOut[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await apiFetch<KnowledgeBaseOut[]>("/knowledge-bases");
      setKbs(list);
    } catch {
      setKbs([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <AuthGate>
      <AppShell>
        <div className="flex-1 space-y-6 p-6 md:p-8">
          <header className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-lg bg-secondary text-primary">
              <ListChecks className="size-5" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-xl font-extrabold tracking-tight">任务</h1>
              <p className="text-sm text-muted-foreground">
                索引与同步进度在各知识库详情的「任务」标签中查看
              </p>
            </div>
          </header>

          <Card className="shadow-[0_1px_2px_rgb(15_23_42_/_0.06)]">
            <CardHeader>
              <CardTitle className="text-base font-extrabold">从知识库进入任务</CardTitle>
              <CardDescription>
                当前接口按知识库聚合任务；选择下方知识库可查看上传索引与飞书同步状态。
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-2" aria-busy="true">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : kbs.length === 0 ? (
                <div className="rounded-md border border-dashed border-border bg-muted/40 px-4 py-8 text-center">
                  <p className="text-sm text-muted-foreground">暂无知识库</p>
                  <Button asChild className="mt-4" variant="secondary">
                    <Link href="/kbs">去创建知识库</Link>
                  </Button>
                </div>
              ) : (
                <ul className="divide-y divide-border rounded-md border border-border">
                  {kbs.map((kb) => (
                    <li
                      key={kb.id}
                      className="flex items-center justify-between gap-3 px-4 py-3"
                    >
                      <div>
                        <p className="font-semibold">{kb.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {kb.description ?? "无描述"}
                        </p>
                      </div>
                      <Button asChild variant="outline" size="sm">
                        <Link href={`/kbs/${kb.id}`}>
                          查看任务
                          <ArrowRight className="size-4" aria-hidden="true" />
                        </Link>
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      </AppShell>
    </AuthGate>
  );
}
