"use client";

import { ArrowsClockwise, UploadSimple } from "@phosphor-icons/react";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useId, useRef, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
import { StatusPill } from "@/components/status-pill";
import ui from "@/components/ui.module.css";
import { apiBaseUrl } from "@/lib/api-base";
import {
  apiFetch,
  type DocumentOut,
  type IndexJobOut,
  type KnowledgeBaseOut,
} from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth-token";

import styles from "../kbs.module.css";

type Tab = "documents" | "connector" | "jobs";

export default function KnowledgeBaseDetailPage() {
  const params = useParams<{ id: string }>();
  const kbId = params.id;
  const fileInputRef = useRef<HTMLInputElement>(null);
  const appIdField = useId();
  const appSecretField = useId();
  const spaceIdField = useId();

  const [tab, setTab] = useState<Tab>("documents");
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

  const pollJob = useCallback(async (jobId: string) => {
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
  }, [loadDocs]);

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
        <div className={styles.page}>
          <header className={styles.header}>
            <div>
              <h1 className={styles.title}>{kb?.name ?? "知识库"}</h1>
              <p style={{ margin: 0, color: "var(--color-muted-foreground)" }}>
                {kb?.description ?? ""}
              </p>
            </div>
            <button type="button" className={ui.btnSecondary} onClick={() => void triggerSync()}>
              <ArrowsClockwise size={18} aria-hidden="true" />
              同步飞书
            </button>
          </header>

          {message ? (
            <p style={{ color: "var(--color-muted-foreground)", fontSize: "0.875rem" }}>{message}</p>
          ) : null}

          <div className={styles.tabs} role="tablist">
            {(
              [
                ["documents", "文档"],
                ["connector", "连接器"],
                ["jobs", "任务"],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                type="button"
                role="tab"
                aria-selected={tab === key}
                className={`${styles.tab} ${tab === key ? styles.tabActive : ""}`}
                onClick={() => setTab(key)}
              >
                {label}
              </button>
            ))}
          </div>

          {tab === "documents" ? (
            <>
              <div
                className={styles.uploadZone}
                role="button"
                tabIndex={0}
                onClick={() => fileInputRef.current?.click()}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") fileInputRef.current?.click();
                }}
                aria-busy={uploading}
              >
                <UploadSimple size={32} aria-hidden="true" />
                <p>点击上传文档</p>
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
              </div>
              <table className={styles.table} style={{ marginTop: "var(--space-lg)" }}>
                <thead>
                  <tr>
                    <th>标题</th>
                    <th>来源</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  {docs.map((d) => (
                    <tr key={d.id}>
                      <td>{d.title ?? "—"}</td>
                      <td>{d.source}</td>
                      <td>
                        <StatusPill status={d.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : null}

          {tab === "connector" ? (
            <form onSubmit={bindFeishu} className={ui.card} style={{ maxWidth: 480 }}>
              <p style={{ marginTop: 0, fontSize: "0.875rem", color: "var(--color-muted-foreground)" }}>
                绑定飞书 Wiki 空间以同步文档
              </p>
              <div className={ui.field}>
                <label className={ui.label} htmlFor={appIdField}>
                  App ID
                </label>
                <input
                  id={appIdField}
                  className={ui.input}
                  value={appId}
                  onChange={(e) => setAppId(e.target.value)}
                  required
                />
              </div>
              <div className={ui.field}>
                <label className={ui.label} htmlFor={appSecretField}>
                  App Secret
                </label>
                <input
                  id={appSecretField}
                  className={ui.input}
                  type="password"
                  value={appSecret}
                  onChange={(e) => setAppSecret(e.target.value)}
                  required
                />
              </div>
              <div className={ui.field}>
                <label className={ui.label} htmlFor={spaceIdField}>
                  Space ID
                </label>
                <input
                  id={spaceIdField}
                  className={ui.input}
                  value={spaceId}
                  onChange={(e) => setSpaceId(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className={ui.btnSecondary}>
                绑定飞书
              </button>
            </form>
          ) : null}

          {tab === "jobs" ? (
            <div className={ui.card}>
              {jobs.length === 0 ? (
                <p style={{ color: "var(--color-muted-foreground)" }}>暂无任务记录</p>
              ) : (
                jobs.map((job) => (
                  <div key={job.id} className={styles.jobRow}>
                    <div style={{ display: "flex", gap: "var(--space-sm)", alignItems: "center" }}>
                      <span>{job.job_type ?? "job"}</span>
                      <StatusPill status={job.state ?? "pending"} />
                    </div>
                    {job.error ? <div className={styles.jobError}>{job.error}</div> : null}
                  </div>
                ))
              )}
            </div>
          ) : null}
        </div>
      </AppShell>
    </AuthGate>
  );
}
