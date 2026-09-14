from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import joinedload

from db.models import Chunk, Document
from domain.models import Evidence, QueryContext, RerankHit
from domain.protocols import EmbeddingProvider, RerankProvider
from ingest.pgvector_store import tokenize_for_tsv
from providers.registry import Settings, get_embedding, get_reranker
from retrieve.rrf import rrf_fuse

_DENSE_LIMIT = 50
_LEXICAL_LIMIT = 50
_RRF_K = 60
_RRF_POOL = 100


class HybridRetriever:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        embedding: EmbeddingProvider | None = None,
        reranker: RerankProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        cfg = settings or Settings()
        self._session_factory = session_factory
        self._embedding = embedding or get_embedding(cfg)
        self._reranker = reranker or get_reranker(cfg)

    async def retrieve(
        self,
        context: QueryContext,
        *,
        top_k: int = 8,
    ) -> list[Evidence]:
        return await self._retrieve_impl(context.question, context.kb_ids, top_k=top_k)

    async def _retrieve_impl(
        self,
        query: str,
        kb_ids: list[uuid.UUID],
        *,
        top_k: int = 8,
    ) -> list[Evidence]:
        if not kb_ids or not query.strip():
            return []

        query_vec = await self._embedding.embed_query(query)
        async with self._session_factory() as session:
            dense_ids = await self._dense_search(session, query_vec, kb_ids)
            lexical_ids = await self._lexical_search(session, query, kb_ids)
            fused_ids = rrf_fuse([dense_ids, lexical_ids], k=_RRF_K)[:_RRF_POOL]
            if not fused_ids:
                return []

            chunks = await self._load_chunks(session, fused_ids)
            chunk_by_id = {str(c.id): c for c in chunks}
            ordered_chunks = [
                chunk_by_id[cid] for cid in fused_ids if cid in chunk_by_id
            ]
            if not ordered_chunks:
                return []

            doc_texts = [c.text for c in ordered_chunks]
            hits = await self._reranker.rerank(query, doc_texts, top_n=top_k)
            return self._to_evidences(ordered_chunks, hits)

    async def _dense_search(
        self,
        session: AsyncSession,
        query_vec: list[float],
        kb_ids: list[uuid.UUID],
    ) -> list[str]:
        distance = Chunk.embedding.cosine_distance(query_vec)
        stmt: Select[Any] = (
            select(Chunk.id)
            .where(Chunk.kb_id.in_(kb_ids))
            .order_by(distance)
            .limit(_DENSE_LIMIT)
        )
        result = await session.execute(stmt)
        return [str(row[0]) for row in result.all()]

    async def _lexical_search(
        self,
        session: AsyncSession,
        query: str,
        kb_ids: list[uuid.UUID],
    ) -> list[str]:
        tokens = tokenize_for_tsv(query)
        if not tokens.strip():
            return []

        tsquery = func.plainto_tsquery("simple", tokens)
        rank = func.ts_rank_cd(Chunk.tsv, tsquery)
        stmt: Select[Any] = (
            select(Chunk.id)
            .where(Chunk.kb_id.in_(kb_ids), Chunk.tsv.op("@@")(tsquery))
            .order_by(rank.desc())
            .limit(_LEXICAL_LIMIT)
        )
        result = await session.execute(stmt)
        return [str(row[0]) for row in result.all()]

    async def _load_chunks(
        self, session: AsyncSession, chunk_ids: list[str]
    ) -> list[Chunk]:
        uuids = [uuid.UUID(cid) for cid in chunk_ids]
        stmt = (
            select(Chunk)
            .options(joinedload(Chunk.document))
            .where(Chunk.id.in_(uuids))
        )
        result = await session.execute(stmt)
        return list(result.scalars().unique().all())

    def _to_evidences(
        self,
        ordered_chunks: list[Chunk],
        hits: list[RerankHit],
    ) -> list[Evidence]:
        evidences: list[Evidence] = []
        for hit in hits:
            chunk = ordered_chunks[hit.index]
            meta = chunk.meta or {}
            parent_text = meta.get("parent_text")
            doc = chunk.document
            evidences.append(
                Evidence(
                    evidence_id=chunk.id,
                    document_id=chunk.document_id,
                    kb_id=chunk.kb_id,
                    text=chunk.text,
                    title=doc.title if doc else None,
                    uri=doc.uri if doc else None,
                    score=float(hit.score),
                    parent_text=str(parent_text) if parent_text else None,
                )
            )
        return evidences
