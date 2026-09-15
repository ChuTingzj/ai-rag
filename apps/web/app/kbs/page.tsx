"use client";

import { Plus } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useId, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch, type KnowledgeBaseOut } from "@/lib/api-client";

export default function KnowledgeBasesPage() {
  const nameId = useId();
  const descId = useId();
  const [kbs, setKbs] = useState<KnowledgeBaseOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await apiFetch<KnowledgeBaseOut[]>("/knowledge-bases");
      setKbs(list);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function createKb(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await apiFetch<KnowledgeBaseOut>("/knowledge-bases", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || null,
        }),
      });
      setModalOpen(false);
      setName("");
      setDescription("");
      await load();
    } catch {
      setError("创建失败");
    } finally {
      setCreating(false);
    }
  }

  return (
    <AuthGate>
      <AppShell>
        <div className="flex-1 p-6">
          <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <h1 className="text-xl font-bold">知识库</h1>
            <Button type="button" onClick={() => setModalOpen(true)}>
              <Plus className="size-[18px]" aria-hidden="true" />
              新建知识库
            </Button>
          </header>

          {loading ? (
            <Skeleton className="h-[120px] w-full" aria-busy="true" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>名称</TableHead>
                  <TableHead>描述</TableHead>
                  <TableHead>创建时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {kbs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className="text-muted-foreground">
                      暂无知识库，点击「新建知识库」开始
                    </TableCell>
                  </TableRow>
                ) : (
                  kbs.map((kb) => (
                    <TableRow key={kb.id}>
                      <TableCell>
                        <Link
                          href={`/kbs/${kb.id}`}
                          className="font-semibold text-primary hover:underline"
                        >
                          {kb.name}
                        </Link>
                      </TableCell>
                      <TableCell>{kb.description ?? "—"}</TableCell>
                      <TableCell>
                        {new Date(kb.created_at).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}

          <Dialog open={modalOpen} onOpenChange={setModalOpen}>
            <DialogContent className="max-w-[420px]">
              <DialogHeader>
                <DialogTitle>新建知识库</DialogTitle>
              </DialogHeader>
              {error ? (
                <div className="rounded-md bg-destructive/12 px-3 py-2 text-sm text-destructive">
                  {error}
                </div>
              ) : null}
              <form onSubmit={createKb} className="space-y-4">
                <div className="space-y-1">
                  <Label htmlFor={nameId}>名称</Label>
                  <Input
                    id={nameId}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor={descId}>描述</Label>
                  <Input
                    id={descId}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setModalOpen(false)}
                  >
                    取消
                  </Button>
                  <Button type="submit" disabled={creating}>
                    {creating ? "创建中…" : "创建"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </AppShell>
    </AuthGate>
  );
}
