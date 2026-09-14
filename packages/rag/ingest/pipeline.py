from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import Document, IndexJob
from domain.protocols import EmbeddingProvider
from ingest.chunk import ParentChildChunker
from ingest.parse import parse_file
from ingest.pgvector_store import delete_document_chunks, insert_chunk_rows, tokenize_for_tsv
from providers.registry import Settings, get_embedding


class IndexJobStats(BaseModel):
    document_id: uuid.UUID
    chunks_written: int = 0
    parent_sections: int = 0
    bytes_read: int = 0
    duration_ms: int = 0
    errors: list[str] = Field(default_factory=list)


async def run_ingest(
    document_id: uuid.UUID,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    embedding: EmbeddingProvider | None = None,
    settings: Settings | None = None,
) -> IndexJobStats:
    started = datetime.now(UTC)
    cfg = settings or Settings()
    embedder = embedding or get_embedding(cfg)
    stats = IndexJobStats(document_id=document_id)

    async with session_factory() as session:
        document = await session.get(Document, document_id)
        if document is None:
            raise ValueError(f"Document not found: {document_id}")

        job = await _ensure_index_job(session, document)
        job.state = "running"
        job.started_at = started
        document.status = "indexing"
        await session.commit()

        try:
            stats = await _ingest_document_body(
                session,
                document=document,
                embedder=embedder,
                started=started,
            )
            document.status = "ready"
            job.state = "succeeded"
            job.stats = stats.model_dump(mode="json")
            job.error = None
        except Exception as exc:
            document.status = "failed"
            job.state = "failed"
            job.error = str(exc)
            stats.errors.append(str(exc))
            raise
        finally:
            job.finished_at = datetime.now(UTC)
            if stats.duration_ms == 0:
                stats.duration_ms = int(
                    (job.finished_at - started).total_seconds() * 1000
                )
            await session.commit()

    return stats


async def _ingest_document_body(
    session: AsyncSession,
    *,
    document: Document,
    embedder: EmbeddingProvider,
    started: datetime,
) -> IndexJobStats:
    if not document.raw_path:
        raise ValueError("Document has no raw_path")

    path = Path(document.raw_path)
    if not path.is_file():
        raise FileNotFoundError(f"Raw file missing: {path}")

    raw_bytes = path.read_bytes()
    text = parse_file(path, document.mime_type)
    drafts = ParentChildChunker().split(text)
    if not drafts:
        raise ValueError("No chunks produced from document")

    parent_sections = len({d.parent_text for d in drafts})
    await delete_document_chunks(session, document.id)

    child_texts = [d.child_text for d in drafts]
    vectors = await embedder.embed_documents(child_texts)

    rows: list[dict] = []
    parent_ids: dict[str, uuid.UUID] = {}
    for draft, vector in zip(drafts, vectors, strict=True):
        parent_id = parent_ids.setdefault(draft.parent_text, uuid.uuid4())
        context_prefix = draft.heading
        rows.append(
            {
                "id": uuid.uuid4(),
                "document_id": document.id,
                "kb_id": document.kb_id,
                "parent_chunk_id": parent_id,
                "ordinal": draft.ordinal,
                "text": draft.child_text,
                "context_prefix": context_prefix,
                "token_count": len(draft.child_text.split()),
                "embedding": vector,
                "meta": {"parent_text": draft.parent_text},
                "tsv_input": tokenize_for_tsv(draft.child_text),
            }
        )

    written = await insert_chunk_rows(
        session,
        document_id=document.id,
        kb_id=document.kb_id,
        rows=rows,
    )

    finished = datetime.now(UTC)
    return IndexJobStats(
        document_id=document.id,
        chunks_written=written,
        parent_sections=parent_sections,
        bytes_read=len(raw_bytes),
        duration_ms=int((finished - started).total_seconds() * 1000),
    )


async def _ensure_index_job(session: AsyncSession, document: Document) -> IndexJob:
    result = await session.execute(
        select(IndexJob)
        .where(IndexJob.document_id == document.id)
        .order_by(IndexJob.created_at.desc())
        .limit(1)
    )
    job = result.scalar_one_or_none()
    if job is not None:
        return job

    job = IndexJob(
        id=uuid.uuid4(),
        kb_id=document.kb_id,
        document_id=document.id,
        job_type="ingest",
        state="pending",
    )
    session.add(job)
    await session.flush()
    return job
