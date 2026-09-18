"use client";

import { ChevronDown, FileText } from "lucide-react";
import { useState } from "react";

import type { CitationOut } from "@/lib/api-client";
import { cn } from "@/lib/utils";

type AnswerCitationsProps = {
  citations: CitationOut[];
  onSelect: (citation: CitationOut) => void;
};

export function AnswerCitations({ citations, onSelect }: AnswerCitationsProps) {
  const [open, setOpen] = useState(false);

  if (citations.length === 0) return null;

  return (
    <div className="mt-3 border-t border-border pt-3">
      <button
        type="button"
        className="flex w-full items-center gap-1.5 text-left text-xs font-semibold text-muted-foreground transition-colors hover:text-foreground"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <ChevronDown
          className={cn(
            "size-3.5 shrink-0 transition-transform",
            open && "rotate-180",
          )}
          aria-hidden="true"
        />
        {citations.length} 个引用来源
      </button>
      {open ? (
        <div className="mt-3 flex flex-col gap-2">
          {citations.map((c) => {
            const canPreview = Boolean(c.document_id);
            return (
              <button
                key={c.evidence_id}
                type="button"
                disabled={!canPreview}
                onClick={() => {
                  if (canPreview) onSelect(c);
                }}
                className={cn(
                  "flex w-full gap-3 rounded-lg border border-border bg-muted/60 p-3 text-left text-xs text-foreground transition-colors",
                  canPreview
                    ? "cursor-pointer hover:border-primary/40 hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    : "cursor-default opacity-70",
                )}
              >
                <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-card text-primary">
                  <FileText className="size-4" aria-hidden="true" />
                </span>
                <span className="min-w-0">
                  <strong className="block text-sm">
                    {c.title ?? "未命名文档"}
                  </strong>
                  <span className="mt-1 block leading-relaxed text-muted-foreground">
                    {c.snippet?.slice(0, 120) ?? "—"}
                  </span>
                </span>
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
