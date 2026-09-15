from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Annotated, Protocol

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from acl.gateway import AclGateway
from app.core.config import settings
from app.db.session import async_session_factory
from domain.protocols import LLMProvider
from generate.generator import Generator
from orchestrator.service import OrchestratorService
from providers.registry import Settings as RagSettings
from providers.registry import get_embedding, get_llm as build_llm, get_reranker
from retrieve.hybrid import HybridRetriever
from retrieve.packer import ContextPacker


@dataclass(frozen=True, slots=True)
class Principal:
    """Gateway-authenticated identity (auth DB is separate; no local user row)."""

    id: uuid.UUID
    roles: list[str] = field(default_factory=list)


class IngestQueue(Protocol):
    async def enqueue(self, document_id: uuid.UUID) -> None: ...


class SyncQueue(Protocol):
    async def enqueue(self, kb_id: uuid.UUID, *, job_id: uuid.UUID) -> None: ...


class ArqIngestQueue:
    async def enqueue(self, document_id: uuid.UUID) -> None:
        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        try:
            await pool.enqueue_job("ingest_document", str(document_id))
        finally:
            await pool.close()


class ArqSyncQueue:
    async def enqueue(self, kb_id: uuid.UUID, *, job_id: uuid.UUID) -> None:
        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        try:
            await pool.enqueue_job("sync_feishu", str(kb_id), str(job_id))
        finally:
            await pool.close()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


def get_rag_settings() -> RagSettings:
    return RagSettings(
        openrouter_api_key=settings.openrouter_api_key,
        openrouter_model=settings.openrouter_model,
        openrouter_base_url=settings.openrouter_base_url,
        embedding_provider=settings.embedding_provider,
        embedding_model=settings.embedding_model,
        embedding_dim=settings.embedding_dim,
        rerank_provider=settings.rerank_provider,
        rerank_model=settings.rerank_model,
        data_dir=settings.data_dir,
    )


def get_llm(rag_settings: Annotated[RagSettings, Depends(get_rag_settings)]) -> LLMProvider:
    return build_llm(rag_settings)


def require_internal_token(
    x_internal_token: Annotated[str | None, Header()] = None,
) -> None:
    expected = settings.internal_service_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="INTERNAL_SERVICE_TOKEN is not configured",
        )
    if not x_internal_token or x_internal_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token",
        )


async def get_current_user(
    _: Annotated[None, Depends(require_internal_token)],
    x_user_id: Annotated[str | None, Header()] = None,
    x_user_roles: Annotated[str | None, Header()] = None,
) -> Principal:
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        user_id = uuid.UUID(x_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user id",
        ) from exc
    roles = [r for r in (x_user_roles or "").split(",") if r]
    return Principal(id=user_id, roles=roles)


def get_ingest_queue() -> IngestQueue:
    return ArqIngestQueue()


def get_sync_queue() -> SyncQueue:
    return ArqSyncQueue()


def _rag_settings_cache_key(cfg: RagSettings) -> tuple:
    return (
        cfg.openrouter_api_key,
        cfg.openrouter_model,
        cfg.openrouter_base_url,
        cfg.embedding_provider,
        cfg.embedding_model,
        cfg.embedding_dim,
        cfg.rerank_provider,
        cfg.rerank_model,
        cfg.data_dir,
    )


@lru_cache(maxsize=8)
def _cached_hybrid_retriever(settings_key: tuple, session_factory_id: int) -> HybridRetriever:
    cfg = RagSettings(
        openrouter_api_key=settings_key[0],
        openrouter_model=settings_key[1],
        openrouter_base_url=settings_key[2],
        embedding_provider=settings_key[3],
        embedding_model=settings_key[4],
        embedding_dim=settings_key[5],
        rerank_provider=settings_key[6],
        rerank_model=settings_key[7],
        data_dir=settings_key[8],
    )
    return HybridRetriever(
        async_session_factory,
        embedding=get_embedding(cfg),
        reranker=get_reranker(cfg),
        settings=cfg,
    )


def get_orchestrator(
    rag_settings: Annotated[RagSettings, Depends(get_rag_settings)],
    llm: Annotated[LLMProvider, Depends(get_llm)],
) -> OrchestratorService:
    retriever = _cached_hybrid_retriever(
        _rag_settings_cache_key(rag_settings),
        id(async_session_factory),
    )
    return OrchestratorService(
        retriever=retriever,
        acl=AclGateway(),
        packer=ContextPacker(),
        generator=Generator(llm, model=rag_settings.openrouter_model),
    )
