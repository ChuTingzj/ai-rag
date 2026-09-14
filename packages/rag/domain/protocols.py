from __future__ import annotations

from typing import Protocol

from domain.models import (
    ChangePage,
    Evidence,
    LLMResult,
    Message,
    QueryContext,
    QueryRequest,
    QueryResponse,
    RawDocument,
    RerankHit,
)


class LLMProvider(Protocol):
    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResult: ...


class EmbeddingProvider(Protocol):
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...

    @property
    def dim(self) -> int: ...


class RerankProvider(Protocol):
    async def rerank(
        self, query: str, documents: list[str], top_n: int
    ) -> list[RerankHit]: ...


class Connector(Protocol):
    id: str

    async def list_changes(self, cursor: str | None) -> ChangePage: ...

    async def fetch_document(self, external_id: str) -> RawDocument: ...


class Retriever(Protocol):
    async def retrieve(
        self, query: QueryContext, *, top_k: int
    ) -> list[Evidence]: ...


class Orchestrator(Protocol):
    async def run(self, request: QueryRequest) -> QueryResponse: ...
