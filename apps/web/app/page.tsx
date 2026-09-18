"use client";

import { Send } from "lucide-react";
import { useCallback, useEffect, useId, useState } from "react";

import { AnswerCitations } from "@/components/answer-citations";
import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
import { DocumentPreviewSheet } from "@/components/document-preview-sheet";
import { MarkdownMessage } from "@/components/markdown-message";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import {
  apiFetch,
  type CitationOut,
  type KnowledgeBaseOut,
  type QueryResponseOut,
} from "@/lib/api-client";

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
  const [previewCitation, setPreviewCitation] = useState<CitationOut | null>(
    null,
  );
  const [previewOpen, setPreviewOpen] = useState(false);

  useEffect(() => {
    apiFetch<KnowledgeBaseOut[]>("/knowledge-bases")
      .then((list) => {
        setKbs(list);
        if (list[0]) setSelectedKb(list[0].id);
      })
      .catch(() => setKbs([]));
  }, []);

  const openPreview = useCallback((citation: CitationOut) => {
    setPreviewCitation(citation);
    setPreviewOpen(true);
  }, []);

  const send = useCallback(
    async (text: string) => {
      const q = text.trim();
      if (!q || !selectedKb || loading) return;

      setMessages((prev) => [...prev, { role: "user", text: q }]);
      setQuestion("");
      setLoading(true);

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

  return (
    <AuthGate>
      <AppShell>
        <div className="flex h-screen min-h-0 flex-1">
          <section
            className="flex min-w-0 flex-1 flex-col"
            aria-label="对话"
          >
            <div className="sticky top-0 z-10 flex items-end gap-4 border-b border-border bg-card/90 px-4 py-4 backdrop-blur md:px-6">
              <div className="min-w-0 flex-1 space-y-1.5">
                <Label
                  htmlFor={kbSelectId}
                  className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground"
                >
                  知识库
                </Label>
                <Select
                  value={selectedKb || undefined}
                  onValueChange={setSelectedKb}
                >
                  <SelectTrigger
                    id={kbSelectId}
                    className="h-10 max-w-md border-border bg-background"
                  >
                    <SelectValue placeholder="暂无知识库" />
                  </SelectTrigger>
                  <SelectContent>
                    {kbs.length === 0 ? (
                      <SelectItem value="__empty" disabled>
                        暂无知识库
                      </SelectItem>
                    ) : (
                      kbs.map((kb) => (
                        <SelectItem key={kb.id} value={kb.id}>
                          {kb.name}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>
              {selectedKb ? (
                <span className="mb-1 hidden items-center gap-1 rounded-full bg-secondary px-2.5 py-1 text-xs font-semibold text-primary sm:inline-flex">
                  <span className="size-1.5 rounded-full bg-primary" />
                  已连接
                </span>
              ) : null}
            </div>

            <ScrollArea className="flex-1 bg-background">
              <div className="mx-auto flex max-w-3xl flex-col gap-5 px-4 py-8 md:px-6">
                {messages.length === 0 && !loading ? (
                  <div className="rounded-lg border border-dashed border-border bg-card px-5 py-6 text-sm text-muted-foreground">
                    <p className="font-semibold text-foreground">
                      输入问题开始检索与生成回答。
                    </p>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {EXAMPLES.map((ex) => (
                        <button
                          key={ex}
                          type="button"
                          className="rounded-full border border-border bg-muted px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:border-primary hover:bg-secondary"
                          onClick={() => void send(ex)}
                        >
                          {ex}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  messages.map((msg, i) =>
                    msg.role === "user" ? (
                      <div
                        key={i}
                        className="ml-auto max-w-[min(640px,85%)] rounded-lg bg-primary px-4 py-3 text-sm font-medium leading-relaxed text-primary-foreground shadow-[0_1px_2px_rgb(15_23_42_/_0.06)] animate-in fade-in duration-200"
                      >
                        {msg.text}
                      </div>
                    ) : (
                      <div
                        key={i}
                        className="mr-auto w-full max-w-[min(720px,92%)] rounded-lg border border-border bg-card px-4 py-4 text-sm leading-relaxed shadow-[0_1px_2px_rgb(15_23_42_/_0.06)] animate-in fade-in duration-200"
                      >
                        {msg.route ? (
                          <div className="mb-2">
                            <Badge variant="default" className="uppercase tracking-wide">
                              {msg.route}
                            </Badge>
                          </div>
                        ) : null}
                        <MarkdownMessage
                          content={msg.text}
                          citations={msg.citations}
                          onSelectCitation={openPreview}
                        />
                        {msg.citations && msg.citations.length > 0 ? (
                          <AnswerCitations
                            citations={msg.citations}
                            onSelect={openPreview}
                          />
                        ) : null}
                      </div>
                    ),
                  )
                )}
                {loading ? (
                  <div
                    className="mr-auto w-full max-w-[min(720px,92%)] space-y-3 rounded-lg border border-border bg-card px-4 py-4 shadow-[0_1px_2px_rgb(15_23_42_/_0.06)] animate-in fade-in duration-200"
                    aria-busy="true"
                    aria-live="polite"
                  >
                    <p className="text-sm text-muted-foreground">
                      正在检索与生成回答…
                    </p>
                    <div className="space-y-2">
                      <Skeleton className="h-3 w-48" />
                      <Skeleton className="h-3 w-36" />
                      <Skeleton className="h-3 w-40" />
                    </div>
                  </div>
                ) : null}
              </div>
            </ScrollArea>

            <div className="border-t border-border bg-card px-4 py-4 shadow-[0_-4px_16px_rgb(15_23_42_/_0.04)] md:px-6">
              <form
                className="mx-auto flex max-w-3xl items-end gap-3 rounded-lg border border-border bg-background p-3 transition-[border-color,box-shadow] focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/20"
                onSubmit={(e) => {
                  e.preventDefault();
                  void send(question);
                }}
              >
                <div className="min-w-0 flex-1 space-y-1">
                  <Label htmlFor={questionId} className="sr-only">
                    问题
                  </Label>
                  <Textarea
                    id={questionId}
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    disabled={loading}
                    placeholder="向知识库提问…"
                    className="min-h-[64px] resize-none border-0 bg-transparent px-2 py-1 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
                  />
                </div>
                <Button
                  type="submit"
                  size="icon"
                  disabled={loading || !selectedKb || !question.trim()}
                  aria-label="发送"
                >
                  <Send className="size-[18px]" aria-hidden="true" />
                </Button>
              </form>
            </div>
          </section>
        </div>
        <DocumentPreviewSheet
          citation={previewCitation}
          fallbackKbId={selectedKb}
          open={previewOpen}
          onOpenChange={setPreviewOpen}
        />
      </AppShell>
    </AuthGate>
  );
}
