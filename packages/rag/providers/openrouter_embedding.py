from __future__ import annotations

import httpx

_DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


class OpenRouterEmbedding:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        dim: int,
        base_url: str = "https://openrouter.ai/api/v1",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._dim = dim
        self._base_url = base_url.rstrip("/")
        self._client = client

    @property
    def dim(self) -> int:
        return self._dim

    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        payload = {"model": self._model, "input": texts}
        url = f"{self._base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if self._client is not None:
            response = await self._client.post(url, json=payload, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
                response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        items = sorted(data["data"], key=lambda row: row["index"])
        return [row["embedding"] for row in items]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await self._embed_batch(texts)

    async def embed_query(self, text: str) -> list[float]:
        rows = await self._embed_batch([text])
        return rows[0]
