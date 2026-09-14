from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from db.models import Document, KnowledgeBase
from ingest.pipeline import run_ingest
from providers.registry import Settings


async def ensure_m1_corpus_indexed(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    corpus_dir: Path,
    kb_name: str = "m1-eval",
    settings: Settings | None = None,
) -> tuple[uuid.UUID, dict[str, uuid.UUID]]:
    """Index markdown corpus; returns kb_id and external_id -> document_id."""
    cfg = settings or Settings()
    async with session_factory() as session:
        kb = await session.scalar(select(KnowledgeBase).where(KnowledgeBase.name == kb_name))
        if kb is None:
            kb = KnowledgeBase(id=uuid.uuid4(), name=kb_name, description="M1 eval corpus")
            session.add(kb)
            await session.commit()
            await session.refresh(kb)
        kb_id = kb.id

    doc_map: dict[str, uuid.UUID] = {}
    for path in sorted(corpus_dir.glob("*.md")):
        external_id = path.stem
        async with session_factory() as session:
            existing = await session.scalar(
                select(Document).where(
                    Document.kb_id == kb_id,
                    Document.external_id == external_id,
                )
            )
            if existing is not None and existing.status == "ready":
                doc_map[external_id] = existing.id
                continue

            doc_id = existing.id if existing is not None else uuid.uuid4()
            if existing is None:
                session.add(
                    Document(
                        id=doc_id,
                        kb_id=kb_id,
                        source="eval",
                        external_id=external_id,
                        title=path.name,
                        mime_type="text/markdown",
                        status="pending",
                        version=1,
                        raw_path=str(path.resolve()),
                    )
                )
                await session.commit()
            else:
                existing.raw_path = str(path.resolve())
                existing.status = "pending"
                await session.commit()

        await run_ingest(doc_id, session_factory=session_factory, settings=cfg)
        doc_map[external_id] = doc_id

    return kb_id, doc_map
