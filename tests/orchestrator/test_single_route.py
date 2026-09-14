from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import pytest

from acl.gateway import AclGateway
from domain.models import Evidence, LLMResult, Message, QueryContext, QueryRequest, RefuseReason
from generate.generator import Generator
from orchestrator.service import OrchestratorService
from retrieve.packer import ContextPacker


@dataclass
class StubRetriever:
    evidences: list[Evidence] = field(default_factory=list)

    async def retrieve(self, query: QueryContext, *, top_k: int) -> list[Evidence]:
        _ = query, top_k
        return list(self.evidences)


@dataclass
class StubLLM:
    content: str = "费用上限为 3000 元[E1]。"

    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResult:
        _ = messages, model, temperature, max_tokens
        return LLMResult(content=self.content, model="stub")


def _evidence(text: str = "费用上限 3000 元") -> Evidence:
    return Evidence(
        evidence_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        kb_id=uuid.uuid4(),
        text=text,
        title="政策",
        score=0.9,
        parent_text=text,
    )


@pytest.mark.asyncio
async def test_single_route_returns_cited_answer():
    ev = _evidence()
    orchestrator = OrchestratorService(
        retriever=StubRetriever(evidences=[ev]),
        acl=AclGateway(),
        packer=ContextPacker(),
        generator=Generator(StubLLM()),
    )
    request = QueryRequest(
        user_id=uuid.uuid4(),
        question="费用上限是多少？",
        kb_ids=[ev.kb_id],
    )
    response = await orchestrator.run(request)
    assert response.route == "single"
    assert response.refuse_reason is None
    assert "[E1]" in response.answer or "3000" in response.answer
    assert len(response.citations) == 1
    assert response.citations[0].evidence_id == ev.evidence_id
    assert response.citations[0].index == 1


@pytest.mark.asyncio
async def test_empty_evidence_no_evidence_refuse():
    orchestrator = OrchestratorService(
        retriever=StubRetriever(evidences=[]),
        acl=AclGateway(),
        packer=ContextPacker(),
        generator=Generator(StubLLM()),
    )
    request = QueryRequest(
        user_id=uuid.uuid4(),
        question="费用上限是多少？",
        kb_ids=[uuid.uuid4()],
    )
    response = await orchestrator.run(request)
    assert response.route == "single"
    assert response.refuse_reason == RefuseReason.NO_EVIDENCE
    assert response.answer == ""
