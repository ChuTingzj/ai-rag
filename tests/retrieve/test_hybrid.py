from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from acl.gateway import AclGateway
from db.models import Document, KnowledgeBase
from domain.models import Evidence, QueryContext
from ingest.pipeline import run_ingest
from providers.registry import Settings
from retrieve.hybrid import HybridRetriever
from retrieve.packer import ContextPacker


def _async_database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://rag:rag@localhost:15432/rag",
    )


@pytest.fixture
async def async_session_factory(migrated_engine):
    engine = create_async_engine(_async_database_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


def test_acl_gateway_is_identity():
    gateway = AclGateway()
    user_id = uuid.uuid4()
    evidences = [
        Evidence(
            evidence_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            kb_id=uuid.uuid4(),
            text="child",
            score=1.0,
            parent_text="parent section",
        )
    ]
    assert gateway.filter(user_id, evidences) == evidences


def test_context_packer_prefers_parent_text_and_dedupes():
    doc_id = uuid.uuid4()
    kb_id = uuid.uuid4()
    parent = "Shared parent section with enough context."
    e1 = Evidence(
        evidence_id=uuid.uuid4(),
        document_id=doc_id,
        kb_id=kb_id,
        text="child one",
        score=0.9,
        parent_text=parent,
        title="Doc",
    )
    e2 = Evidence(
        evidence_id=uuid.uuid4(),
        document_id=doc_id,
        kb_id=kb_id,
        text="child two",
        score=0.8,
        parent_text=parent,
        title="Doc",
    )
    packed = ContextPacker().pack([e1, e2], max_tokens=500)
    assert len(packed.evidence_ids) == 1
    assert parent in packed.text
    assert "[E1]" in packed.text


@pytest.mark.asyncio
async def test_hybrid_retriever_reranks_and_returns_parent_text(
    async_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash_stub")
    monkeypatch.setenv("EMBEDDING_DIM", "1024")
    monkeypatch.setenv("RERANK_PROVIDER", "stub")

    kb_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    sample = "# Policy\n\nexpense limit hybrid retrieve test\n\n" + ("padding " * 80)
    raw_file = tmp_path / "policy.md"
    raw_file.write_text(sample, encoding="utf-8")

    async with async_session_factory() as session:
        session.add(KnowledgeBase(id=kb_id, name="retrieve-kb"))
        session.add(
            Document(
                id=doc_id,
                kb_id=kb_id,
                source="upload",
                external_id="hybrid-1",
                title="Policy",
                mime_type="text/markdown",
                status="pending",
                version=1,
                raw_path=str(raw_file),
            )
        )
        await session.commit()

    await run_ingest(doc_id, session_factory=async_session_factory)

    settings = Settings(
        embedding_provider="hash_stub",
        embedding_dim=1024,
        rerank_provider="stub",
    )
    retriever = HybridRetriever(async_session_factory, settings=settings)
    hits = await retriever.retrieve(
        QueryContext(
            question="expense limit hybrid retrieve",
            kb_ids=[kb_id],
        ),
        top_k=3,
    )
    assert hits
    assert all(isinstance(h, Evidence) for h in hits)
    assert any(h.parent_text for h in hits)
    assert hits[0].score >= hits[-1].score
