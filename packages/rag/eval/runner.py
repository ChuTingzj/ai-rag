from __future__ import annotations

import json
import logging
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from acl.gateway import AclGateway
from domain.models import LLMResult, Message, QueryContext, QueryRequest
from eval.metrics import (
    aggregate_citation_precision,
    aggregate_hit_rate,
    citation_precision,
    retrieval_hit_rate,
)
from eval.models import EvalReport, GoldenCase
from eval.naive import NaiveRetriever
from generate.generator import Generator
from orchestrator.service import OrchestratorService
from providers.registry import Settings
from retrieve.hybrid import HybridRetriever
from retrieve.packer import ContextPacker

logger = logging.getLogger(__name__)


@dataclass
class StubLLM:
    content: str = "Answer grounded in evidence[E1]."

    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResult:
        _ = messages, model, temperature, max_tokens
        return LLMResult(content=self.content, model="stub")


def load_golden(path: Path) -> list[GoldenCase]:
    cases: list[GoldenCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        cases.append(GoldenCase.model_validate(json.loads(line)))
    return cases


def resolve_doc_ids(
    external_ids: list[str],
    doc_map: dict[str, UUID],
) -> list[UUID]:
    resolved: list[UUID] = []
    for key in external_ids:
        doc_id = doc_map.get(key)
        if doc_id is not None:
            resolved.append(doc_id)
    return resolved


async def run_pipeline_eval(
    pipeline: Literal["naive", "hybrid"],
    *,
    golden_path: Path,
    kb_id: UUID,
    session_factory: async_sessionmaker[AsyncSession],
    doc_map: dict[str, UUID] | None = None,
    top_k: int = 8,
    settings: Settings | None = None,
) -> EvalReport:
    cfg = settings or Settings(
        embedding_provider="hash_stub",
        embedding_dim=1024,
        rerank_provider="stub",
    )
    cases = load_golden(golden_path)
    if doc_map is None:
        from eval.corpus import ensure_m1_corpus_indexed

        _kb_id, doc_map = await ensure_m1_corpus_indexed(
            session_factory,
            corpus_dir=golden_path.parent / "corpus",
            kb_name=cases[0].kb if cases else "m1-eval",
            settings=cfg,
        )
        kb_id = _kb_id

    if pipeline == "naive":
        retriever = NaiveRetriever(session_factory, settings=cfg)
    elif pipeline == "hybrid":
        retriever = HybridRetriever(session_factory, settings=cfg)
    else:
        raise ValueError(f"Unknown pipeline: {pipeline}")

    orchestrator = OrchestratorService(
        retriever=retriever,
        acl=AclGateway(),
        packer=ContextPacker(),
        generator=Generator(StubLLM()),
        top_k=top_k,
    )

    hit_flags: list[bool] = []
    citation_scores: list[float] = []
    case_rows: list[dict] = []

    for case in cases:
        must_include = resolve_doc_ids(case.must_include_doc_ids, doc_map)
        context = QueryContext(question=case.question, kb_ids=[kb_id])
        retrieved = await retriever.retrieve(context, top_k=top_k)
        hit = retrieval_hit_rate(retrieved, must_include_doc_ids=must_include)
        hit_flags.append(hit)

        response = await orchestrator.run(
            QueryRequest(user_id=UUID(int=0), question=case.question, kb_ids=[kb_id])
        )
        retrieved_ids = {ev.evidence_id for ev in retrieved}
        cited_ids = [c.evidence_id for c in response.citations]
        cite_score = citation_precision(cited_ids, retrieved_ids)
        if response.refuse_reason is None and cited_ids:
            citation_scores.append(cite_score)

        case_rows.append(
            {
                "id": case.id,
                "retrieval_hit": hit,
                "citation_precision": cite_score,
                "refuse_reason": (
                    response.refuse_reason.value if response.refuse_reason else None
                ),
            }
        )

    metrics = {
        "retrieval_hit_rate": aggregate_hit_rate(hit_flags),
        "citation_precision": aggregate_citation_precision(citation_scores),
    }
    return EvalReport(pipeline=pipeline, metrics=metrics, cases=case_rows)


def compare_pipelines(naive: EvalReport, hybrid: EvalReport) -> dict:
    hybrid_rate = hybrid.metrics["retrieval_hit_rate"]
    naive_rate = naive.metrics["retrieval_hit_rate"]
    hybrid_ge_naive = hybrid_rate >= naive_rate
    if not hybrid_ge_naive:
        msg = (
            f"hybrid retrieval_hit_rate ({hybrid_rate:.3f}) "
            f"< naive ({naive_rate:.3f}); golden set may be flaky"
        )
        logger.warning(msg)
        warnings.warn(msg, stacklevel=2)
    return {
        "naive": naive.metrics,
        "hybrid": hybrid.metrics,
        "hybrid_ge_naive": hybrid_ge_naive,
    }
