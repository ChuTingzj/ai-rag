from __future__ import annotations

import uuid
from typing import Any

import jieba
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chunk


def tokenize_for_tsv(text: str) -> str:
    """Tokenize for Postgres simple text search (jieba for CJK)."""
    tokens = jieba.cut_for_search(text)
    return " ".join(t.strip() for t in tokens if t.strip())


async def delete_document_chunks(session: AsyncSession, document_id: uuid.UUID) -> int:
    result = await session.execute(delete(Chunk).where(Chunk.document_id == document_id))
    return result.rowcount or 0


async def insert_chunk_rows(
    session: AsyncSession,
    *,
    document_id: uuid.UUID,
    kb_id: uuid.UUID,
    rows: list[dict[str, Any]],
) -> int:
    if not rows:
        return 0
    for row in rows:
        tsv_input = row.pop("tsv_input")
        chunk = Chunk(**row)
        chunk.tsv = func.to_tsvector("simple", tsv_input)
        session.add(chunk)
    await session.flush()
    return len(rows)


async def count_document_chunks(session: AsyncSession, document_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.count()).select_from(Chunk).where(Chunk.document_id == document_id)
    )
    return int(result.scalar_one())
