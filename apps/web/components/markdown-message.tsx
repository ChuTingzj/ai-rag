"use client";

import type { Components } from "react-markdown";
import ReactMarkdown, { defaultUrlTransform } from "react-markdown";
import remarkGfm from "remark-gfm";

import type { CitationOut } from "@/lib/api-client";
import { cn } from "@/lib/utils";

const CITATION_MARKER_RE = /\[E(\d+)\]/g;
const CITATION_HREF_RE = /^citation:(\d+)$/;

function linkifyCitationMarkers(text: string): string {
  return text.replace(CITATION_MARKER_RE, "[[E$1]](citation:$1)");
}

function citationUrlTransform(url: string): string {
  if (CITATION_HREF_RE.test(url)) return url;
  return defaultUrlTransform(url);
}

function buildCitationByIndex(
  citations: CitationOut[],
): Map<number, CitationOut> {
  const map = new Map<number, CitationOut>();
  for (const citation of citations) {
    if (citation.index != null) {
      map.set(citation.index, citation);
    }
  }
  return map;
}

function buildComponents(
  citationByIndex: Map<number, CitationOut>,
  onSelectCitation?: (citation: CitationOut) => void,
): Components {
  return {
    h1: ({ children }) => (
      <h1 className="mb-3 mt-4 text-base font-bold text-foreground first:mt-0">
        {children}
      </h1>
    ),
    h2: ({ children }) => (
      <h2 className="mb-2 mt-4 text-sm font-bold text-foreground first:mt-0">
        {children}
      </h2>
    ),
    h3: ({ children }) => (
      <h3 className="mb-2 mt-3 text-sm font-semibold text-foreground first:mt-0">
        {children}
      </h3>
    ),
    p: ({ children }) => (
      <p className="mb-3 text-sm leading-relaxed text-foreground last:mb-0">
        {children}
      </p>
    ),
    ul: ({ children }) => (
      <ul className="mb-3 list-disc space-y-1.5 pl-5 text-sm last:mb-0">
        {children}
      </ul>
    ),
    ol: ({ children }) => (
      <ol className="mb-3 list-decimal space-y-1.5 pl-5 text-sm last:mb-0">
        {children}
      </ol>
    ),
    li: ({ children }) => (
      <li className="leading-relaxed text-foreground">{children}</li>
    ),
    strong: ({ children }) => (
      <strong className="font-semibold text-foreground">{children}</strong>
    ),
    em: ({ children }) => <em className="italic">{children}</em>,
    a: ({ href, children }) => {
      const match = href ? CITATION_HREF_RE.exec(href) : null;
      if (match) {
        const index = Number(match[1]);
        const citation = citationByIndex.get(index);
        const canPreview = Boolean(citation?.document_id && onSelectCitation);
        const label = citation?.title
          ? `引用 E${index}：${citation.title}`
          : `引用 E${index}`;

        return (
          <button
            type="button"
            disabled={!canPreview}
            aria-label={label}
            title={label}
            onClick={() => {
              if (canPreview && citation) onSelectCitation?.(citation);
            }}
            className={cn(
              "mx-0.5 inline-flex translate-y-px items-center rounded px-1 py-0.5 align-baseline text-[0.8em] font-medium leading-none",
              canPreview
                ? "cursor-pointer bg-secondary text-primary transition-colors hover:bg-secondary/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                : "cursor-default bg-muted text-muted-foreground opacity-70",
            )}
          >
            {children}
          </button>
        );
      }

      return (
        <a
          href={href}
          target="_blank"
          rel="noreferrer"
          className="font-medium text-primary underline-offset-2 hover:underline"
        >
          {children}
        </a>
      );
    },
    code: ({ className, children }) => (
      <code
        className={
          className ??
          "rounded bg-muted px-1 py-0.5 font-mono text-[0.85em] text-foreground"
        }
      >
        {children}
      </code>
    ),
    pre: ({ children }) => (
      <pre className="mb-3 overflow-x-auto rounded-lg border border-border bg-muted p-3 font-mono text-xs leading-relaxed text-foreground last:mb-0">
        {children}
      </pre>
    ),
    blockquote: ({ children }) => (
      <blockquote className="mb-3 border-l-2 border-border pl-3 text-sm text-muted-foreground last:mb-0">
        {children}
      </blockquote>
    ),
    hr: () => <hr className="my-4 border-border" />,
    table: ({ children }) => (
      <div className="mb-3 overflow-x-auto last:mb-0">
        <table className="w-full border-collapse text-left text-sm">
          {children}
        </table>
      </div>
    ),
    thead: ({ children }) => (
      <thead className="border-b border-border bg-muted/60">{children}</thead>
    ),
    th: ({ children }) => (
      <th className="px-2 py-1.5 font-semibold text-foreground">{children}</th>
    ),
    td: ({ children }) => (
      <td className="border-t border-border px-2 py-1.5 text-foreground">
        {children}
      </td>
    ),
  };
}

type MarkdownMessageProps = {
  content: string;
  citations?: CitationOut[];
  onSelectCitation?: (citation: CitationOut) => void;
};

export function MarkdownMessage({
  content,
  citations = [],
  onSelectCitation,
}: MarkdownMessageProps) {
  const citationByIndex = buildCitationByIndex(citations);
  const components = buildComponents(citationByIndex, onSelectCitation);

  return (
    <div className="markdown-message min-w-0">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        urlTransform={citationUrlTransform}
        components={components}
      >
        {linkifyCitationMarkers(content)}
      </ReactMarkdown>
    </div>
  );
}
