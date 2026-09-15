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
    <div className="flex flex-col gap-2">
      {citations.map((c) => (
        <button
          key={c.evidence_id}
          type="button"
          className={cn(
            "flex w-full gap-2 rounded-md border border-transparent bg-muted p-2 text-left text-xs text-foreground transition-colors hover:border-border",
            activeCitation === c.evidence_id && "border-primary",
          )}
          onClick={() => onSelect(c.evidence_id)}
        >
          <FileText className="mt-0.5 size-[18px] shrink-0" aria-hidden="true" />
          <span>
            <strong>{c.title ?? "未命名文档"}</strong>
            <br />
            {c.snippet?.slice(0, 120) ?? "—"}
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
          <section className="flex min-w-0 flex-1 flex-col border-r border-border" aria-label="对话">
            <div className="sticky top-0 z-10 space-y-1 border-b border-border bg-card px-4 py-3 md:px-6">
              <Label htmlFor={kbSelectId}>知识库</Label>
              <Select
                value={selectedKb || undefined}
                onValueChange={setSelectedKb}
              >
                <SelectTrigger id={kbSelectId} className="max-w-sm">
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

            <ScrollArea className="flex-1">
              <div className="flex flex-col gap-4 p-4 md:p-6">
                {messages.length === 0 ? (
                  <div className="text-sm text-muted-foreground">
                    <p>输入问题开始检索与生成回答。</p>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {EXAMPLES.map((ex) => (
                        <button
                          key={ex}
                          type="button"
                          className="rounded-full border border-border bg-muted px-3 py-1 text-xs transition-colors hover:bg-primary/10"
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
                        className="ml-auto max-w-[min(640px,90%)] rounded-md border border-border bg-primary/12 p-4 animate-in fade-in duration-200"
                      >
                        {msg.text}
                      </div>
                    ) : (
                      <div
                        key={i}
                        className="mr-auto max-w-[min(720px,95%)] rounded-md border border-border bg-card p-4 animate-in fade-in duration-200"
                        aria-busy={loading && i === messages.length - 1 ? true : undefined}
                      >
                        {msg.text}
                        {msg.route ? (
                          <Badge variant="secondary" className="ml-2 align-middle">
                            {msg.route}
                          </Badge>
                        ) : null}
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
                  <div className="mr-auto max-w-[min(720px,95%)] space-y-2 rounded-md border border-border bg-card p-4" aria-busy="true">
                    <Skeleton className="h-3 w-4/5" />
                    <Skeleton className="h-3 w-3/5" />
                    <Skeleton className="h-3 w-[70%]" />
                  </div>
                ) : null}
              </div>
            </ScrollArea>

            <form
              className="flex items-end gap-3 border-t border-border bg-card px-4 py-3 md:px-6"
              onSubmit={(e) => {
                e.preventDefault();
                void send(question);
              }}
            >
              <div className="min-w-0 flex-1 space-y-1">
                <Label htmlFor={questionId}>问题</Label>
                <Textarea
                  id={questionId}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  disabled={loading}
                  className="min-h-[72px] resize-y"
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
                <Send className="size-5" aria-hidden="true" />
              </Button>
            </form>
          </section>

          <aside
            className="hidden w-80 shrink-0 flex-col bg-card md:flex"
            aria-label="引用来源"
          >
            <div className="border-b border-border px-6 py-3 font-bold">引用</div>
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
