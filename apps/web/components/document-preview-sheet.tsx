"use client";

import { useEffect, useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ApiError,
  apiFetch,
  type CitationOut,
  type DocumentContentOut,
} from "@/lib/api-client";

type DocumentPreviewSheetProps = {
  citation: CitationOut | null;
  fallbackKbId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

function HighlightedContent({
  content,
  snippet,
}: {
  content: string;
  snippet: string | null;
}) {
  const markRef = useRef<HTMLMarkElement>(null);
  const needle = snippet?.trim() ?? "";
  const index = needle ? content.indexOf(needle) : -1;

  useEffect(() => {
    if (index < 0) return;
    markRef.current?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [index, content]);

  if (index < 0) {
    return (
      <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed text-foreground">
        {content}
      </pre>
    );
  }

  const before = content.slice(0, index);
  const match = content.slice(index, index + needle.length);
  const after = content.slice(index + needle.length);

  return (
    <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed text-foreground">
      {before}
      <mark
        ref={markRef}
        className="rounded-sm bg-primary/15 px-0.5 text-foreground"
      >
        {match}
      </mark>
      {after}
    </pre>
  );
}

export function DocumentPreviewSheet({
  citation,
  fallbackKbId,
  open,
  onOpenChange,
}: DocumentPreviewSheetProps) {
  const [data, setData] = useState<DocumentContentOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open || !citation?.document_id) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }

    const kbId = citation.kb_id ?? fallbackKbId;
    if (!kbId) {
      setData(null);
      setError("无法确定知识库");
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    setData(null);

    void apiFetch<DocumentContentOut>(
      `/knowledge-bases/${kbId}/documents/${citation.document_id}/content`,
    )
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message =
          err instanceof ApiError ? err.message : "加载文档失败，请稍后重试";
        setError(message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [open, citation, fallbackKbId]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="flex w-full flex-col gap-0 p-0 sm:max-w-xl"
      >
        <SheetHeader className="shrink-0 border-b border-border px-6 py-4 pr-12">
          <SheetTitle className="truncate text-base">
            {data?.title ?? citation?.title ?? "文档预览"}
          </SheetTitle>
          {data?.mime_type ? (
            <Badge variant="secondary" className="w-fit font-normal">
              {data.mime_type}
            </Badge>
          ) : null}
        </SheetHeader>
        <ScrollArea className="min-h-0 flex-1">
          <div className="px-6 py-4">
            {loading ? (
              <div className="space-y-3" aria-busy="true" aria-live="polite">
                <Skeleton className="h-3 w-48" />
                <Skeleton className="h-3 w-full max-w-md" />
                <Skeleton className="h-3 w-72" />
                <Skeleton className="h-3 w-56" />
              </div>
            ) : null}
            {error ? (
              <p className="text-sm text-muted-foreground">{error}</p>
            ) : null}
            {data && !loading ? (
              <HighlightedContent
                content={data.content}
                snippet={citation?.snippet ?? null}
              />
            ) : null}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
