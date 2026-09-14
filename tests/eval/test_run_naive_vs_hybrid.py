from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from eval.metrics import citation_precision, retrieval_hit_rate
from eval.runner import compare_pipelines, run_pipeline_eval
from eval.corpus import ensure_m1_corpus_indexed


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


def test_retrieval_hit_rate_and_citation_precision_units():
    doc_a = uuid.uuid4()
    doc_b = uuid.uuid4()
    ev_a = _evidence(doc_a)
    ev_b = _evidence(doc_b)

    assert retrieval_hit_rate([ev_a, ev_b], must_include_doc_ids=[doc_a]) is True
    assert retrieval_hit_rate([ev_b], must_include_doc_ids=[doc_a]) is False

    retrieved = {ev_a.evidence_id, ev_b.evidence_id}
    assert citation_precision([ev_a.evidence_id], retrieved) == 1.0
    assert citation_precision([uuid.uuid4()], retrieved) == 0.0


@pytest.mark.asyncio
async def test_run_naive_vs_hybrid_on_golden(
    async_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash_stub")
    monkeypatch.setenv("EMBEDDING_DIM", "1024")
    monkeypatch.setenv("RERANK_PROVIDER", "stub")

    repo_root = Path(__file__).resolve().parents[2]
    golden_path = repo_root / "evals" / "m1" / "golden.jsonl"
    corpus_dir = repo_root / "evals" / "m1" / "corpus"
    assert golden_path.is_file()
    assert corpus_dir.is_dir()
    lines = [ln for ln in golden_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 20

    kb_id, _doc_map = await ensure_m1_corpus_indexed(
        async_session_factory,
        corpus_dir=corpus_dir,
        kb_name="m1-eval",
    )

    naive_report = await run_pipeline_eval(
        "naive",
        golden_path=golden_path,
        kb_id=kb_id,
        session_factory=async_session_factory,
    )
    hybrid_report = await run_pipeline_eval(
        "hybrid",
        golden_path=golden_path,
        kb_id=kb_id,
        session_factory=async_session_factory,
    )

    assert naive_report.metrics["citation_precision"] is not None
    assert hybrid_report.metrics["citation_precision"] is not None
    assert 0.0 <= naive_report.metrics["citation_precision"] <= 1.0
    assert 0.0 <= hybrid_report.metrics["citation_precision"] <= 1.0

    comparison = compare_pipelines(naive_report, hybrid_report)
    assert comparison["naive"]["retrieval_hit_rate"] is not None
    assert comparison["hybrid"]["retrieval_hit_rate"] is not None
    assert "hybrid_ge_naive" in comparison


def _evidence(document_id: uuid.UUID):
    from domain.models import Evidence

    return Evidence(
        evidence_id=uuid.uuid4(),
        document_id=document_id,
        kb_id=uuid.uuid4(),
        text="snippet",
        score=1.0,
    )
