"use client";

import { Plus } from "@phosphor-icons/react";
import Link from "next/link";
import { useCallback, useEffect, useId, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
import ui from "@/components/ui.module.css";
import { apiFetch, type KnowledgeBaseOut } from "@/lib/api-client";

import styles from "./kbs.module.css";

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
        <div className={styles.page}>
          <header className={styles.header}>
            <h1 className={styles.title}>知识库</h1>
            <button
              type="button"
              className={ui.btnPrimary}
              onClick={() => setModalOpen(true)}
            >
              <Plus size={18} aria-hidden="true" />
              新建知识库
            </button>
          </header>

          {loading ? (
            <div className={ui.skeleton} style={{ height: 120 }} aria-busy="true" />
          ) : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>名称</th>
                  <th>描述</th>
                  <th>创建时间</th>
                </tr>
              </thead>
              <tbody>
                {kbs.length === 0 ? (
                  <tr>
                    <td colSpan={3} style={{ color: "var(--color-muted-foreground)" }}>
                      暂无知识库，点击「新建知识库」开始
                    </td>
                  </tr>
                ) : (
                  kbs.map((kb) => (
                    <tr key={kb.id}>
                      <td>
                        <Link href={`/kbs/${kb.id}`}>{kb.name}</Link>
                      </td>
                      <td>{kb.description ?? "—"}</td>
                      <td>{new Date(kb.created_at).toLocaleString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}

          {modalOpen ? (
            <div
              className={styles.modalBackdrop}
              role="dialog"
              aria-modal="true"
              aria-labelledby="create-kb-title"
            >
              <div className={`${ui.card} ${styles.modal}`}>
                <h2 id="create-kb-title" className={styles.title}>
                  新建知识库
                </h2>
                {error ? <div className={ui.errorSummary}>{error}</div> : null}
                <form onSubmit={createKb}>
                  <div className={ui.field}>
                    <label className={ui.label} htmlFor={nameId}>
                      名称
                    </label>
                    <input
                      id={nameId}
                      className={ui.input}
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                    />
                  </div>
                  <div className={ui.field}>
                    <label className={ui.label} htmlFor={descId}>
                      描述
                    </label>
                    <input
                      id={descId}
                      className={ui.input}
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                    />
                  </div>
                  <div style={{ display: "flex", gap: "var(--space-sm)", justifyContent: "flex-end" }}>
                    <button
                      type="button"
                      className={ui.btnSecondary}
                      onClick={() => setModalOpen(false)}
                    >
                      取消
                    </button>
                    <button type="submit" className={ui.btnPrimary} disabled={creating}>
                      {creating ? "创建中…" : "创建"}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          ) : null}
        </div>
      </AppShell>
    </AuthGate>
  );
}
