from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import joinedload

from db.models import Chunk, Document
from domain.models import Evidence, QueryContext
from domain.protocols import EmbeddingProvider
from providers.registry import Settings, get_embedding

_DENSE_LIMIT = 50


class NaiveRetriever:
    """Dense vector search only (no lexical fusion or rerank)."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        embedding: EmbeddingProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        cfg = settings or Settings()
        self._session_factory = session_factory
        self._embedding = embedding or get_embedding(cfg)

    async def retrieve(
        self,
        context: QueryContext,
        *,
        top_k: int = 8,
    ) -> list[Evidence]:
        if not context.kb_ids or not context.question.strip():
            return []

        query_vec = await self._embedding.embed_query(context.question)
        async with self._session_factory() as session:
            stmt: Select[Any] = (
                select(Chunk)
                .options(joinedload(Chunk.document))
                .where(Chunk.kb_id.in_(context.kb_ids))
                .order_by(Chunk.embedding.cosine_distance(query_vec))
                .limit(min(top_k, _DENSE_LIMIT))
            )
            result = await session.execute(stmt)
            chunks = list(result.scalars().unique().all())
            return [_chunk_to_evidence(c, rank=i) for i, c in enumerate(chunks)]


def _chunk_to_evidence(chunk: Chunk, *, rank: int) -> Evidence:
    meta = chunk.meta or {}
    parent_text = meta.get("parent_text")
    doc: Document | None = chunk.document
    return Evidence(
        evidence_id=chunk.id,
        document_id=chunk.document_id,
        kb_id=chunk.kb_id,
        text=chunk.text,
        title=doc.title if doc else None,
        uri=doc.uri if doc else None,
        score=float(_DENSE_LIMIT - rank),
        parent_text=str(parent_text) if parent_text else None,
    )
