from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class ChunkDraft:
    parent_text: str
    child_text: str
    ordinal: int
    heading: str | None = None


class ParentChildChunker:
    """Split markdown-ish text into parent sections and child retrieval chunks."""

    def __init__(
        self,
        *,
        child_max_chars: int = 800,
        child_overlap_chars: int = 80,
    ) -> None:
        self._child_max_chars = child_max_chars
        self._child_overlap_chars = child_overlap_chars

    def split(self, text: str) -> list[ChunkDraft]:
        normalized = text.replace("\r\n", "\n").strip()
        if not normalized:
            return []

        sections = self._split_sections(normalized)
        drafts: list[ChunkDraft] = []
        ordinal = 0
        for heading, body in sections:
            parent_text = body if heading is None else f"{heading}\n{body}".strip()
            if not parent_text:
                continue
            children = self._split_children(parent_text)
            for child in children:
                drafts.append(
                    ChunkDraft(
                        parent_text=parent_text,
                        child_text=child,
                        ordinal=ordinal,
                        heading=heading,
                    )
                )
                ordinal += 1
        return drafts

    def _split_sections(self, text: str) -> list[tuple[str | None, str]]:
        matches = list(_HEADING_RE.finditer(text))
        if not matches:
            return [(None, text)]

        sections: list[tuple[str | None, str]] = []
        if matches[0].start() > 0:
            preamble = text[: matches[0].start()].strip()
            if preamble:
                sections.append((None, preamble))

        for i, match in enumerate(matches):
            level = match.group(1)
            title = match.group(2).strip()
            heading = f"{level} {title}"
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            sections.append((heading, body))
        return sections

    def _split_children(self, parent_text: str) -> list[str]:
        if len(parent_text) <= self._child_max_chars:
            return [parent_text]

        chunks: list[str] = []
        start = 0
        length = len(parent_text)
        while start < length:
            end = min(start + self._child_max_chars, length)
            if end < length:
                break_at = parent_text.rfind("\n\n", start, end)
                if break_at <= start:
                    break_at = parent_text.rfind(" ", start, end)
                if break_at > start:
                    end = break_at
            piece = parent_text[start:end].strip()
            if piece:
                chunks.append(piece)
            if end >= length:
                break
            start = max(end - self._child_overlap_chars, start + 1)
        return chunks or [parent_text]
