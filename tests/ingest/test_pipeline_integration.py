from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Chunk, Document, KnowledgeBase
from ingest.pipeline import run_ingest


def _async_database_url() -> str:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://rag:rag@localhost:5432/rag",
    )
    return url


@pytest.fixture
async def async_session_factory(migrated_engine):
    url = _async_database_url()
    engine = create_async_engine(url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_run_ingest_writes_chunks_and_tsv(
    async_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash_stub")
    monkeypatch.setenv("EMBEDDING_DIM", "1024")

    kb_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    sample = "# Intro\n\nhello ingest world\n\n" + ("detail " * 120)
    raw_file = tmp_path / "sample.md"
    raw_file.write_text(sample, encoding="utf-8")

    async with async_session_factory() as session:
        session.add(KnowledgeBase(id=kb_id, name="test-kb"))
        session.add(
            Document(
                id=doc_id,
                kb_id=kb_id,
                source="upload",
                external_id="ext-1",
                title="Sample",
                mime_type="text/markdown",
                status="pending",
                version=1,
                raw_path=str(raw_file),
            )
        )
        await session.commit()

    stats = await run_ingest(doc_id, session_factory=async_session_factory)
    assert stats.chunks_written > 0
    assert stats.parent_sections >= 1

    async with async_session_factory() as session:
        doc = await session.get(Document, doc_id)
        assert doc is not None
        assert doc.status == "ready"

        count = await session.scalar(
            select(func.count()).select_from(Chunk).where(Chunk.document_id == doc_id)
        )
        assert count == stats.chunks_written

        row = await session.scalar(select(Chunk).where(Chunk.document_id == doc_id).limit(1))
        assert row is not None
        assert row.embedding is not None
        assert len(row.embedding) == 1024
        assert row.meta and row.meta.get("parent_text")

        fts = await session.execute(
            text(
                "SELECT COUNT(*) FROM chunks WHERE document_id = :doc_id "
                "AND tsv @@ plainto_tsquery('simple', 'ingest')"
            ),
            {"doc_id": doc_id},
        )
        assert int(fts.scalar_one()) >= 1
