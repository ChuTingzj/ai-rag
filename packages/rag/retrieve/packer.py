from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from domain.models import Evidence


class PackedContext(BaseModel):
    text: str
    blocks: list[str] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)


def _approx_tokens(text: str) -> int:
    return max(1, len(text.split()))


class ContextPacker:
    """Upgrade child hits to parent text, dedupe, and format [E{n}] blocks."""

    def pack(self, evidences: list[Evidence], max_tokens: int) -> PackedContext:
        blocks: list[str] = []
        evidence_ids: list[UUID] = []
        seen_parent_keys: set[str] = set()
        used_tokens = 0

        for evidence in evidences:
            body = (evidence.parent_text or evidence.text).strip()
            if not body:
                continue
            dedupe_key = body
            if dedupe_key in seen_parent_keys:
                continue

            header_parts: list[str] = []
            if evidence.title:
                header_parts.append(evidence.title)
            label = f"[E{len(blocks) + 1}]"
            block = f"{label} {' — '.join(header_parts)}\n{body}".strip()
            block_tokens = _approx_tokens(block)
            if used_tokens + block_tokens > max_tokens and blocks:
                break

            seen_parent_keys.add(dedupe_key)
            blocks.append(block)
            evidence_ids.append(evidence.evidence_id)
            used_tokens += block_tokens

        return PackedContext(
            text="\n\n".join(blocks),
            blocks=blocks,
            evidence_ids=evidence_ids,
        )
