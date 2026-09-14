"use client";

import { FileText, PaperPlaneTilt } from "@phosphor-icons/react";
import { useCallback, useEffect, useId, useRef, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
import ui from "@/components/ui.module.css";
import {
  apiFetch,
  type CitationOut,
  type KnowledgeBaseOut,
  type QueryResponseOut,
} from "@/lib/api-client";

import styles from "./chat.module.css";

type ChatMessage =
  | { role: "user"; text: string }
  | { role: "assistant"; text: string; route?: string; citations?: CitationOut[] };

const EXAMPLES = [
  "这份文档的核心结论是什么？",
  "对比两个知识库中的政策差异",
  "列出最近上传文件的摘要",
];

export default function ChatPage() {
  const kbSelectId = useId();
  const questionId = useId();
  const [kbs, setKbs] = useState<KnowledgeBaseOut[]>([]);
  const [selectedKb, setSelectedKb] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeCitation, setActiveCitation] = useState<string | null>(null);
  const [citationsOpen, setCitationsOpen] = useState(false);
  const snippetRefs = useRef<Record<string, HTMLParagraphElement | null>>({});

  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
  const citations =
    lastAssistant?.role === "assistant" ? lastAssistant.citations ?? [] : [];

  useEffect(() => {
    apiFetch<KnowledgeBaseOut[]>("/knowledge-bases")
      .then((list) => {
        setKbs(list);
        if (list[0]) setSelectedKb(list[0].id);
      })
      .catch(() => setKbs([]));
  }, []);

  const send = useCallback(
    async (text: string) => {
      const q = text.trim();
      if (!q || !selectedKb || loading) return;

      setMessages((prev) => [...prev, { role: "user", text: q }]);
      setQuestion("");
      setLoading(true);
      setActiveCitation(null);

      try {
        const res = await apiFetch<QueryResponseOut>("/query", {
          method: "POST",
          body: JSON.stringify({ question: q, kb_ids: [selectedKb] }),
        });
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: res.answer,
            route: res.route,
            citations: res.citations,
          },
        ]);
        if (res.citations.length > 0) setCitationsOpen(true);
      } catch {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", text: "查询失败，请稍后重试。" },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [loading, selectedKb],
  );

  function focusCitation(id: string) {
    setActiveCitation(id);
    const el = snippetRefs.current[id];
    el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  return (
    <AuthGate>
      <AppShell>
        <div className={styles.layout}>
          <section className={styles.transcript} aria-label="对话">
            <div className={styles.toolbar}>
              <label className={ui.label} htmlFor={kbSelectId}>
                知识库
              </label>
              <select
                id={kbSelectId}
                className={ui.input}
                value={selectedKb}
                onChange={(e) => setSelectedKb(e.target.value)}
                style={{ maxWidth: 360 }}
              >
                {kbs.length === 0 ? (
                  <option value="">暂无知识库</option>
                ) : (
                  kbs.map((kb) => (
                    <option key={kb.id} value={kb.id}>
                      {kb.name}
                    </option>
                  ))
                )}
              </select>
            </div>

            <div className={styles.messages}>
              {messages.length === 0 ? (
                <div className={styles.empty}>
                  <p>输入问题开始检索与生成回答。</p>
                  <div className={styles.examples}>
                    {EXAMPLES.map((ex) => (
                      <button
                        key={ex}
                        type="button"
                        className={styles.chip}
                        onClick={() => send(ex)}
                      >
                        {ex}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map((msg, i) =>
                  msg.role === "user" ? (
                    <div key={i} className={styles.messageUser}>
                      {msg.text}
                    </div>
                  ) : (
                    <div
                      key={i}
                      className={styles.messageAssistant}
                      aria-busy={loading && i === messages.length - 1 ? true : undefined}
                    >
                      {msg.text}
                      {msg.route ? (
                        <span className={styles.routeBadge}>{msg.route}</span>
                      ) : null}
                      {msg.citations?.map((c) => (
                        <p
                          key={c.evidence_id}
                          ref={(el) => {
                            snippetRefs.current[c.evidence_id] = el;
                          }}
                          id={`cite-${c.evidence_id}`}
                          style={{
                            display: activeCitation === c.evidence_id ? "block" : "none",
                            marginTop: "var(--space-sm)",
                            fontSize: "0.8125rem",
                            color: "var(--color-muted-foreground)",
                          }}
                        >
                          {c.snippet ?? c.title ?? "引用片段"}
                        </p>
                      ))}
                    </div>
                  ),
                )
              )}
              {loading ? (
                <div className={styles.messageAssistant} aria-busy="true">
                  <div className={ui.skeleton} style={{ height: 12, width: "80%" }} />
                  <div
                    className={ui.skeleton}
                    style={{ height: 12, width: "60%", marginTop: 8 }}
                  />
                  <div
                    className={ui.skeleton}
                    style={{ height: 12, width: "70%", marginTop: 8 }}
                  />
                </div>
              ) : null}
            </div>

            <form
              className={styles.composer}
              onSubmit={(e) => {
                e.preventDefault();
                void send(question);
              }}
            >
              <div style={{ flex: 1 }}>
                <label className={ui.label} htmlFor={questionId}>
                  问题
                </label>
                <textarea
                  id={questionId}
                  className={styles.textarea}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  disabled={loading}
                />
              </div>
              <button
                type="button"
                className={`${ui.btnSecondary} ${styles.drawerToggle}`}
                onClick={() => setCitationsOpen((v) => !v)}
              >
                引用
              </button>
              <button
                type="submit"
                className={ui.btnPrimary}
                disabled={loading || !selectedKb || !question.trim()}
                aria-label="发送"
              >
                <PaperPlaneTilt size={20} aria-hidden="true" />
              </button>
            </form>
          </section>

          <aside
            className={`${styles.citations} ${citationsOpen ? styles.citationsOpen : ""}`}
            aria-label="引用来源"
          >
            <div className={styles.citationsHeader}>引用</div>
            <div className={styles.citationList}>
              {citations.length === 0 ? (
                <p style={{ color: "var(--color-muted-foreground)", fontSize: "0.875rem" }}>
                  回答中的引用将显示在此
                </p>
              ) : (
                citations.map((c) => (
                  <button
                    key={c.evidence_id}
                    type="button"
                    className={`${styles.citationItem} ${
                      activeCitation === c.evidence_id ? styles.citationItemActive : ""
                    }`}
                    onClick={() => focusCitation(c.evidence_id)}
                  >
                    <FileText size={18} aria-hidden="true" />
                    <span>
                      <strong>{c.title ?? "未命名文档"}</strong>
                      <br />
                      {c.snippet?.slice(0, 120) ?? "—"}
                    </span>
                  </button>
                ))
              )}
            </div>
          </aside>
        </div>
      </AppShell>
    </AuthGate>
  );
}
