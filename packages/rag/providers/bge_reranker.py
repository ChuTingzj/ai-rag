from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from domain.models import RerankHit

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder


class StubReranker:
    """Preserves document order with descending scores (no model download)."""

    async def rerank(
        self, query: str, documents: list[str], top_n: int
    ) -> list[RerankHit]:
        _ = query
        limit = min(top_n, len(documents))
        return [
            RerankHit(index=i, score=float(len(documents) - i))
            for i in range(limit)
        ]


class BgeReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3") -> None:
        self._model_name = model_name
        self._model: CrossEncoder | None = None
        self._lock = asyncio.Lock()

    async def _get_model(self) -> CrossEncoder:
        if self._model is not None:
            return self._model
        async with self._lock:
            if self._model is None:
                try:
                    from sentence_transformers import CrossEncoder
                except ImportError as exc:
                    raise ImportError(
                        "bge_reranker requires optional deps: "
                        "uv sync --package rag --extra local-ml"
                    ) from exc

                self._model = await asyncio.to_thread(
                    CrossEncoder, self._model_name
                )
            return self._model

    async def rerank(
        self, query: str, documents: list[str], top_n: int
    ) -> list[RerankHit]:
        if not documents:
            return []
        model = await self._get_model()
        pairs = [[query, doc] for doc in documents]
        scores = await asyncio.to_thread(model.predict, pairs)
        ranked = sorted(
            enumerate(float(s) for s in scores),
            key=lambda item: item[1],
            reverse=True,
        )
        limit = min(top_n, len(ranked))
        return [
            RerankHit(index=idx, score=score)
            for idx, score in ranked[:limit]
        ]
