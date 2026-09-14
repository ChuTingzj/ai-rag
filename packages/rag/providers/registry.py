from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from domain.protocols import EmbeddingProvider, LLMProvider, RerankProvider
from providers.bge_reranker import BgeReranker, StubReranker
from providers.local_bge_m3 import HashStubEmbedding, LocalBgeM3Embedding
from providers.openrouter_embedding import OpenRouterEmbedding
from providers.openrouter_llm import OpenRouterLLM


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4.1-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    embedding_provider: str = "local_bge_m3"
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024
    rerank_provider: str = "bge_reranker"
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    data_dir: str = "./data"


@lru_cache(maxsize=8)
def _llm_for_key(openrouter_api_key: str, openrouter_model: str, openrouter_base_url: str) -> LLMProvider:
    return OpenRouterLLM(
        api_key=openrouter_api_key,
        model=openrouter_model,
        base_url=openrouter_base_url,
    )


def get_llm(settings: Settings | None = None) -> LLMProvider:
    cfg = settings or Settings()
    return _llm_for_key(
        cfg.openrouter_api_key,
        cfg.openrouter_model,
        cfg.openrouter_base_url,
    )


@lru_cache(maxsize=16)
def _embedding_for_key(
    embedding_provider: str,
    embedding_model: str,
    embedding_dim: int,
    openrouter_api_key: str,
    openrouter_base_url: str,
) -> EmbeddingProvider:
    if embedding_provider == "hash_stub":
        return HashStubEmbedding(dim=embedding_dim)
    if embedding_provider == "local_bge_m3":
        return LocalBgeM3Embedding(model_name=embedding_model, dim=embedding_dim)
    if embedding_provider == "openrouter":
        return OpenRouterEmbedding(
            api_key=openrouter_api_key,
            model=embedding_model,
            dim=embedding_dim,
            base_url=openrouter_base_url,
        )
    raise ValueError(f"Unknown embedding_provider: {embedding_provider}")


def get_embedding(settings: Settings | None = None) -> EmbeddingProvider:
    cfg = settings or Settings()
    return _embedding_for_key(
        cfg.embedding_provider,
        cfg.embedding_model,
        cfg.embedding_dim,
        cfg.openrouter_api_key,
        cfg.openrouter_base_url,
    )


@lru_cache(maxsize=16)
def _reranker_for_key(rerank_provider: str, rerank_model: str) -> RerankProvider:
    if rerank_provider == "stub":
        return StubReranker()
    if rerank_provider == "bge_reranker":
        return BgeReranker(model_name=rerank_model)
    raise ValueError(f"Unknown rerank_provider: {rerank_provider}")


def get_reranker(settings: Settings | None = None) -> RerankProvider:
    cfg = settings or Settings()
    return _reranker_for_key(cfg.rerank_provider, cfg.rerank_model)
