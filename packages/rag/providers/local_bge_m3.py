from __future__ import annotations

import asyncio
import hashlib
import struct
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class HashStubEmbedding:
    """Deterministic vectors for CI without downloading models."""

    def __init__(self, dim: int = 1024) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed_query(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        return _hash_to_vector(text, self._dim)


class LocalBgeM3Embedding:
    def __init__(self, model_name: str = "BAAI/bge-m3", *, dim: int = 1024) -> None:
        self._model_name = model_name
        self._dim = dim
        self._model: SentenceTransformer | None = None
        self._lock = asyncio.Lock()

    @property
    def dim(self) -> int:
        return self._dim

    async def _get_model(self) -> SentenceTransformer:
        if self._model is not None:
            return self._model
        async with self._lock:
            if self._model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError as exc:
                    raise ImportError(
                        "local_bge_m3 requires optional deps: "
                        "uv sync --all-groups --extra local-ml"
                    ) from exc

                self._model = await asyncio.to_thread(
                    SentenceTransformer, self._model_name
                )
            return self._model

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        model = await self._get_model()
        vectors = await asyncio.to_thread(
            model.encode,
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vectors]

    async def embed_query(self, text: str) -> list[float]:
        rows = await self.embed_documents([text])
        return rows[0]


def _hash_to_vector(text: str, dim: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    seed = digest
    while len(values) < dim:
        for i in range(0, len(seed) - 3, 4):
            (n,) = struct.unpack(">I", seed[i : i + 4])
            values.append((n / 2**32) * 2.0 - 1.0)
            if len(values) >= dim:
                break
        seed = hashlib.sha256(seed).digest()
    return values[:dim]
