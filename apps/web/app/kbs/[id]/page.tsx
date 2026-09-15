"use client";

import { RefreshCw, Upload } from "lucide-react";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useId, useRef, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiBaseUrl } from "@/lib/api-base";
import {
  apiFetch,
  type DocumentOut,
  type IndexJobOut,
  type KnowledgeBaseOut,
} from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";

export default function KnowledgeBaseDetailPage() {
  const params = useParams<{ id: string }>();
  const kbId = params.id;
  const fileInputRef = useRef<HTMLInputElement>(null);
  const appIdField = useId();
  const appSecretField = useId();
  const spaceIdField = useId();

  const [tab, setTab] = useState("documents");
  const [kb, setKb] = useState<KnowledgeBaseOut | null>(null);
  const [docs, setDocs] = useState<DocumentOut[]>([]);
  const [jobs, setJobs] = useState<IndexJobOut[]>([]);
  const [appId, setAppId] = useState("");
  const [appSecret, setAppSecret] = useState("");
  const [spaceId, setSpaceId] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const loadKb = useCallback(async () => {
    const data = await apiFetch<KnowledgeBaseOut>(`/knowledge-bases/${kbId}`);
    setKb(data);
  }, [kbId]);

  const loadDocs = useCallback(async () => {
    const data = await apiFetch<DocumentOut[]>(`/knowledge-bases/${kbId}/documents`);
    setDocs(data);
  }, [kbId]);

  const pollJob = useCallback(
    async (jobId: string) => {
      const job = await apiFetch<IndexJobOut>(`/jobs/${jobId}`);
      setJobs((prev) => {
        const rest = prev.filter((j) => j.id !== jobId);
        return [job, ...rest];
      });
      if (job.state === "pending" || job.state === "running") {
        setTimeout(() => void pollJob(jobId), 1500);
      } else {
        void loadDocs();
      }
    },
    [loadDocs],
  );

  useEffect(() => {
    void loadKb();
    void loadDocs();
  }, [loadKb, loadDocs]);

  async function onUpload(file: File) {
    setUploading(true);
    setMessage(null);
    const form = new FormData();
    form.append("file", file);
    const token = getAccessToken();
    try {
      const res = await fetch(`${apiBaseUrl()}/knowledge-bases/${kbId}/documents`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      });
      if (!res.ok) throw new Error("upload failed");
      const body = (await res.json()) as { job_id: string };
      void pollJob(body.job_id);
      setMessage("上传已排队索引");
    } catch {
      setMessage("上传失败");
    } finally {
      setUploading(false);
    }
  }

  async function bindFeishu(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);
    try {
      await apiFetch(`/knowledge-bases/${kbId}/connectors/feishu`, {
        method: "POST",
        body: JSON.stringify({
          app_id: appId,
          app_secret: appSecret,
          space_id: spaceId,
        }),
      });
      setMessage("飞书连接器已绑定");
    } catch {
      setMessage("绑定失败");
    }
  }

  async function triggerSync() {
    setMessage(null);
    try {
      const res = await apiFetch<{ job_id: string }>(`/knowledge-bases/${kbId}/sync`, {
        method: "POST",
      });
      void pollJob(res.job_id);
      setMessage("同步任务已启动");
      setTab("jobs");
    } catch {
      setMessage("请先绑定飞书连接器");
    }
  }

  return (
    <AuthGate>
      <AppShell>
        <div className="flex-1 p-6">
          <header className="mb-4 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-xl font-bold">{kb?.name ?? "知识库"}</h1>
              <p className="m-0 text-sm text-muted-foreground">
                {kb?.description ?? ""}
              </p>
            </div>
            <Button type="button" variant="secondary" onClick={() => void triggerSync()}>
              <RefreshCw className="size-[18px]" aria-hidden="true" />
              同步飞书
            </Button>
          </header>

          {message ? (
            <p className="mb-4 text-sm text-muted-foreground">{message}</p>
          ) : null}

          <Tabs value={tab} onValueChange={setTab}>
            <TabsList>
              <TabsTrigger value="documents">文档</TabsTrigger>
              <TabsTrigger value="connector">连接器</TabsTrigger>
              <TabsTrigger value="jobs">任务</TabsTrigger>
            </TabsList>

            <TabsContent value="documents" className="space-y-6">
              <button
                type="button"
                className="w-full cursor-pointer rounded-md border-2 border-dashed border-border px-8 py-10 text-center transition-colors hover:bg-primary/[0.06]"
                onClick={() => fileInputRef.current?.click()}
                aria-busy={uploading}
              >
                <Upload className="mx-auto size-8 text-muted-foreground" aria-hidden="true" />
                <p className="mt-2 text-sm text-muted-foreground">点击上传文档</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  hidden
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) void onUpload(f);
                    e.target.value = "";
                  }}
                />
              </button>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>标题</TableHead>
                    <TableHead>来源</TableHead>
                    <TableHead>状态</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {docs.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={3} className="text-muted-foreground">
                        暂无文档
                      </TableCell>
                    </TableRow>
                  ) : (
                    docs.map((d) => (
                      <TableRow key={d.id}>
                        <TableCell>{d.title ?? "—"}</TableCell>
                        <TableCell>{d.source}</TableCell>
                        <TableCell>
                          <StatusPill status={d.status} />
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TabsContent>

            <TabsContent value="connector">
              <Card className="max-w-md">
                <CardContent className="space-y-4 pt-6">
                  <p className="text-sm text-muted-foreground">
                    绑定飞书 Wiki 空间以同步文档
                  </p>
                  <form onSubmit={bindFeishu} className="space-y-4">
                    <div className="space-y-1">
                      <Label htmlFor={appIdField}>App ID</Label>
                      <Input
                        id={appIdField}
                        value={appId}
                        onChange={(e) => setAppId(e.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor={appSecretField}>App Secret</Label>
                      <Input
                        id={appSecretField}
                        type="password"
                        value={appSecret}
                        onChange={(e) => setAppSecret(e.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor={spaceIdField}>Space ID</Label>
                      <Input
                        id={spaceIdField}
                        value={spaceId}
                        onChange={(e) => setSpaceId(e.target.value)}
                        required
                      />
                    </div>
                    <Button type="submit" variant="secondary">
                      绑定飞书
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="jobs">
              <Card>
                <CardContent className="pt-6">
                  {jobs.length === 0 ? (
                    <p className="text-sm text-muted-foreground">暂无任务记录</p>
                  ) : (
                    <div className="divide-y divide-border">
                      {jobs.map((job) => (
                        <div key={job.id} className="py-2.5 text-[0.8125rem]">
                          <div className="flex items-center gap-2">
                            <span>{job.job_type ?? "job"}</span>
                            <StatusPill status={job.state ?? "pending"} />
                          </div>
                          {job.error ? (
                            <div className="mt-1 text-destructive">{job.error}</div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </AppShell>
    </AuthGate>
  );
}
