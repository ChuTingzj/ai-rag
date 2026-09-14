from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from domain.models import Citation, RefuseReason
from domain.protocols import LLMProvider
from generate.citations import CitationValidator
from generate.prompts import build_messages
from retrieve.packer import PackedContext


class GenerateResult(BaseModel):
    answer: str = ""
    citations: list[Citation] = Field(default_factory=list)
    refuse_reason: RefuseReason | None = None


class Generator:
    def __init__(
        self,
        llm: LLMProvider,
        *,
        validator: CitationValidator | None = None,
        model: str | None = None,
    ) -> None:
        self._llm = llm
        self._validator = validator or CitationValidator(strictness="strict")
        self._model = model

    async def generate(self, question: str, packed: PackedContext) -> GenerateResult:
        evidence_count = len(packed.evidence_ids)
        if evidence_count == 0:
            return GenerateResult(refuse_reason=RefuseReason.NO_EVIDENCE)

        messages = build_messages(question, packed)
        llm_result = await self._llm.complete(messages, model=self._model)
        answer = llm_result.text.strip()

        validation = self._validator.validate(answer, evidence_count=evidence_count)
        if not validation.ok:
            return GenerateResult(refuse_reason=validation.refuse_reason)

        citations = _citations_from_indices(
            validation.citation_indices,
            packed.evidence_ids,
        )
        return GenerateResult(answer=answer, citations=citations)


def _citations_from_indices(
    indices: set[int],
    evidence_ids: list[UUID],
) -> list[Citation]:
    ordered = sorted(indices)
    citations: list[Citation] = []
    for index in ordered:
        if index < 1 or index > len(evidence_ids):
            continue
        citations.append(
            Citation(
                evidence_id=evidence_ids[index - 1],
                index=index,
            )
        )
    return citations
