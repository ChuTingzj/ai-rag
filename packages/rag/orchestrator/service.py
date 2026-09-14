from __future__ import annotations

from acl.gateway import AclGateway
from domain.models import QueryContext, QueryRequest, QueryResponse, RefuseReason
from domain.protocols import Retriever
from generate.generator import Generator
from retrieve.packer import ContextPacker


class OrchestratorService:
    """M1 single-route pipeline: retrieve → ACL → pack → generate."""

    def __init__(
        self,
        retriever: Retriever,
        acl: AclGateway,
        packer: ContextPacker,
        generator: Generator,
        *,
        top_k: int = 8,
        max_context_tokens: int = 4096,
    ) -> None:
        self._retriever = retriever
        self._acl = acl
        self._packer = packer
        self._generator = generator
        self._top_k = top_k
        self._max_context_tokens = max_context_tokens

    async def run(self, request: QueryRequest) -> QueryResponse:
        context = QueryContext(
            question=request.question,
            kb_ids=request.kb_ids,
            user_id=request.user_id,
        )
        evidences = await self._retriever.retrieve(context, top_k=self._top_k)
        filtered = self._acl.filter(request.user_id, evidences)
        if not filtered:
            return QueryResponse(
                answer="",
                route="single",
                refuse_reason=RefuseReason.NO_EVIDENCE,
            )

        packed = self._packer.pack(filtered, self._max_context_tokens)
        if not packed.evidence_ids:
            return QueryResponse(
                answer="",
                route="single",
                refuse_reason=RefuseReason.NO_EVIDENCE,
            )

        generated = await self._generator.generate(request.question, packed)
        if generated.refuse_reason is not None:
            return QueryResponse(
                answer="",
                route="single",
                refuse_reason=generated.refuse_reason,
            )

        return QueryResponse(
            answer=generated.answer,
            citations=generated.citations,
            route="single",
        )
