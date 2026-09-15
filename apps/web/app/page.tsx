"use client";

import { FileText, Send } from "lucide-react";
import { useCallback, useEffect, useId, useRef, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";
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
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import {
  apiFetch,
  type CitationOut,
  type KnowledgeBaseOut,
  type QueryResponseOut,
} from "@/lib/api-client";
import { cn } from "@/lib/utils";

type ChatMessage =
  | { role: "user"; text: string }
  | { role: "assistant"; text: string; route?: string; citations?: CitationOut[] };

const EXAMPLES = [
  "这份文档的核心结论是什么？",
  "对比两个知识库中的政策差异",
  "列出最近上传文件的摘要",
];

function CitationsPanel({
  citations,
  activeCitation,
  onSelect,
}: {
  citations: CitationOut[];
  activeCitation: string | null;
  onSelect: (id: string) => void;
}) {
  if (citations.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">回答中的引用将显示在此</p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {citations.map((c) => (
        <button
          key={c.evidence_id}
          type="button"
          className={cn(
            "flex w-full gap-3 rounded-lg border border-border bg-muted/60 p-3 text-left text-xs text-foreground transition-colors hover:border-primary/40",
            activeCitation === c.evidence_id && "border-primary bg-secondary",
          )}
          onClick={() => onSelect(c.evidence_id)}
        >
          <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-card text-primary">
            <FileText className="size-4" aria-hidden="true" />
          </span>
          <span className="min-w-0">
            <strong className="block text-sm">{c.title ?? "未命名文档"}</strong>
            <span className="mt-1 block leading-relaxed text-muted-foreground">
              {c.snippet?.slice(0, 120) ?? "—"}
            </span>
          </span>
        </button>
      ))}
    </div>
  );
}

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
        <div className="flex h-screen min-h-0 flex-1">
          <section
            className="flex min-w-0 flex-1 flex-col border-r border-border"
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
                {messages.length === 0 ? (
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
                        className="mr-auto max-w-[min(720px,92%)] rounded-lg border border-border bg-card px-4 py-4 text-sm leading-relaxed shadow-[0_1px_2px_rgb(15_23_42_/_0.06)] animate-in fade-in duration-200"
                        aria-busy={
                          loading && i === messages.length - 1 ? true : undefined
                        }
                      >
                        {msg.route ? (
                          <div className="mb-2">
                            <Badge variant="default" className="uppercase tracking-wide">
                              {msg.route}
                            </Badge>
                          </div>
                        ) : null}
                        {msg.text}
                        {msg.citations?.map((c) => (
                          <p
                            key={c.evidence_id}
                            ref={(el) => {
                              snippetRefs.current[c.evidence_id] = el;
                            }}
                            id={`cite-${c.evidence_id}`}
                            className={cn(
                              "mt-2 text-[0.8125rem] text-muted-foreground",
                              activeCitation === c.evidence_id ? "block" : "hidden",
                            )}
                          >
                            {c.snippet ?? c.title ?? "引用片段"}
                          </p>
                        ))}
                      </div>
                    ),
                  )
                )}
                {loading ? (
                  <div
                    className="mr-auto max-w-[min(720px,92%)] space-y-2 rounded-lg border border-border bg-card p-4"
                    aria-busy="true"
                  >
                    <Skeleton className="h-3 w-4/5" />
                    <Skeleton className="h-3 w-3/5" />
                    <Skeleton className="h-3 w-[70%]" />
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
                  type="button"
                  variant="secondary"
                  className="md:hidden"
                  onClick={() => setCitationsOpen(true)}
                >
                  引用
                </Button>
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

          <aside
            className="hidden w-[22rem] shrink-0 flex-col bg-card md:flex"
            aria-label="引用来源"
          >
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <h2 className="text-sm font-bold tracking-tight">引用来源</h2>
              {citations.length > 0 ? (
                <span className="rounded-md bg-muted px-2 py-0.5 text-[11px] font-semibold text-muted-foreground">
                  {citations.length}
                </span>
              ) : null}
            </div>
            <ScrollArea className="flex-1 p-4">
              <CitationsPanel
                citations={citations}
                activeCitation={activeCitation}
                onSelect={focusCitation}
              />
            </ScrollArea>
          </aside>

          <Sheet open={citationsOpen} onOpenChange={setCitationsOpen}>
            <SheetContent side="bottom" className="md:hidden">
              <SheetHeader>
                <SheetTitle>引用</SheetTitle>
              </SheetHeader>
              <div className="mt-4 max-h-[35vh] overflow-y-auto">
                <CitationsPanel
                  citations={citations}
                  activeCitation={activeCitation}
                  onSelect={focusCitation}
                />
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </AppShell>
    </AuthGate>
  );
}
