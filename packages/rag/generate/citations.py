from __future__ import annotations

import re

from pydantic import BaseModel, Field

from domain.models import RefuseReason

_CITATION_RE = re.compile(r"\[E(\d+)\]")


def parse_citations(answer: str) -> set[int]:
    return {int(match.group(1)) for match in _CITATION_RE.finditer(answer)}


class CitationValidationResult(BaseModel):
    ok: bool
    refuse_reason: RefuseReason | None = None
    citation_indices: set[int] = Field(default_factory=set)


class CitationValidator:
    def __init__(self, *, strictness: str = "strict") -> None:
        self._strictness = strictness

    def validate(self, answer: str, *, evidence_count: int) -> CitationValidationResult:
        indices = parse_citations(answer)
        if self._strictness != "strict":
            return CitationValidationResult(ok=True, citation_indices=indices)

        if evidence_count > 0 and not indices:
            return CitationValidationResult(
                ok=False,
                refuse_reason=RefuseReason.UNGROUNDED,
            )

        if indices and any(index < 1 or index > evidence_count for index in indices):
            return CitationValidationResult(
                ok=False,
                refuse_reason=RefuseReason.UNGROUNDED,
            )

        return CitationValidationResult(ok=True, citation_indices=indices)
