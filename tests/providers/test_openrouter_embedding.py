from __future__ import annotations

import json

import pytest

from providers.openrouter_embedding import OpenRouterEmbedding


@pytest.mark.asyncio
async def test_openrouter_embedding_sends_dimensions(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://openrouter.ai/api/v1/embeddings",
        json={
            "data": [
                {"index": 0, "embedding": [0.1] * 1024},
                {"index": 1, "embedding": [0.2] * 1024},
            ]
        },
    )
    emb = OpenRouterEmbedding(
        api_key="test-key",
        model="openai/text-embedding-3-large",
        dim=1024,
    )
    vectors = await emb.embed_documents(["a", "b"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 1024

    request = httpx_mock.get_request()
    assert request is not None
    payload = json.loads(request.content.decode())
    assert payload["model"] == "openai/text-embedding-3-large"
    assert payload["input"] == ["a", "b"]
    assert payload["dimensions"] == 1024
    assert request.headers["Authorization"] == "Bearer test-key"


@pytest.mark.asyncio
async def test_openrouter_embedding_rejects_dim_mismatch(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://openrouter.ai/api/v1/embeddings",
        json={"data": [{"index": 0, "embedding": [0.1] * 3072}]},
    )
    emb = OpenRouterEmbedding(
        api_key="test-key",
        model="openai/text-embedding-3-large",
        dim=1024,
    )
    with pytest.raises(ValueError, match="Embedding dim mismatch"):
        await emb.embed_documents(["a"])
