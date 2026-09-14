from __future__ import annotations


def rrf_fuse(rank_lists: list[list[str]], k: int = 60) -> list[str]:
    """Reciprocal rank fusion over multiple ordered document-id lists."""
    scores: dict[str, float] = {}
    for ranked in rank_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda doc_id: scores[doc_id], reverse=True)
