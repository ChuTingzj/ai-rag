from __future__ import annotations

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


def get_llm(settings: Settings | None = None) -> LLMProvider:
    cfg = settings or Settings()
    return OpenRouterLLM(
        api_key=cfg.openrouter_api_key,
        model=cfg.openrouter_model,
        base_url=cfg.openrouter_base_url,
    )


def get_embedding(settings: Settings | None = None) -> EmbeddingProvider:
    cfg = settings or Settings()
    name = cfg.embedding_provider
    if name == "hash_stub":
        return HashStubEmbedding(dim=cfg.embedding_dim)
    if name == "local_bge_m3":
        return LocalBgeM3Embedding(
            model_name=cfg.embedding_model, dim=cfg.embedding_dim
        )
    if name == "openrouter":
        return OpenRouterEmbedding(
            api_key=cfg.openrouter_api_key,
            model=cfg.embedding_model,
            dim=cfg.embedding_dim,
            base_url=cfg.openrouter_base_url,
        )
    raise ValueError(f"Unknown embedding_provider: {name}")


def get_reranker(settings: Settings | None = None) -> RerankProvider:
    cfg = settings or Settings()
    name = cfg.rerank_provider
    if name == "stub":
        return StubReranker()
    if name == "bge_reranker":
        return BgeReranker(model_name=cfg.rerank_model)
    raise ValueError(f"Unknown rerank_provider: {name}")
