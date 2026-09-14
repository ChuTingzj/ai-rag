import pytest

from providers.openrouter_llm import OpenRouterLLM
from providers.registry import Settings, get_embedding, get_llm, get_reranker


def test_get_llm_returns_openrouter():
    settings = Settings(openrouter_api_key="k")
    llm = get_llm(settings)
    assert isinstance(llm, OpenRouterLLM)


@pytest.mark.asyncio
async def test_hash_stub_embedding_is_deterministic():
    settings = Settings(embedding_provider="hash_stub", embedding_dim=128)
    emb = get_embedding(settings)
    assert emb.dim == 128
    v1 = await emb.embed_query("hello world")
    v2 = await emb.embed_query("hello world")
    assert v1 == v2
    assert len(v1) == 128


@pytest.mark.asyncio
async def test_hash_stub_documents_batch():
    settings = Settings(embedding_provider="hash_stub", embedding_dim=64)
    emb = get_embedding(settings)
    vectors = await emb.embed_documents(["a", "b", "a"])
    assert len(vectors) == 3
    assert vectors[0] == vectors[2]
    assert vectors[0] != vectors[1]


@pytest.mark.asyncio
async def test_stub_reranker_preserves_order():
    settings = Settings(rerank_provider="stub")
    reranker = get_reranker(settings)
    docs = ["first", "second", "third"]
    hits = await reranker.rerank("q", docs, top_n=2)
    assert len(hits) == 2
    assert hits[0].index == 0
    assert hits[1].index == 1
    assert hits[0].score >= hits[1].score
