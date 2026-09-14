from __future__ import annotations

import uuid

from domain.models import Evidence


def retrieval_hit_rate(
    evidences: list[Evidence],
    *,
    must_include_doc_ids: list[uuid.UUID],
) -> bool:
    if not must_include_doc_ids:
        return True
    retrieved_docs = {ev.document_id for ev in evidences}
    return any(doc_id in retrieved_docs for doc_id in must_include_doc_ids)


def citation_precision(
    cited_evidence_ids: list[uuid.UUID],
    retrieved_evidence_ids: set[uuid.UUID],
) -> float:
    if not cited_evidence_ids:
        return 1.0
    hits = sum(1 for eid in cited_evidence_ids if eid in retrieved_evidence_ids)
    return hits / len(cited_evidence_ids)


def aggregate_hit_rate(hits: list[bool]) -> float:
    if not hits:
        return 0.0
    return sum(1 for h in hits if h) / len(hits)


def aggregate_citation_precision(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
