from __future__ import annotations

import uuid

from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import settings
from app.db.models import IndexJob
from app.db.session import async_session_factory
from connectors.sync import run_feishu_sync
from ingest.pipeline import run_ingest


async def _enqueue_ingest(document_id: str) -> None:
    pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    try:
        await pool.enqueue_job("ingest_document", document_id)
    finally:
        await pool.close()


async def ingest_document(_ctx: dict, document_id: str) -> dict:
    stats = await run_ingest(
        uuid.UUID(document_id),
        session_factory=async_session_factory,
    )
    return stats.model_dump(mode="json")


async def sync_feishu(_ctx: dict, kb_id: str, job_id: str) -> dict:
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is required for Feishu sync")

    job_uuid = uuid.UUID(job_id)
    kb_uuid = uuid.UUID(kb_id)

    async with async_session_factory() as session:
        job = await session.get(IndexJob, job_uuid)
        if job is not None:
            job.state = "running"
            await session.commit()

    try:
        stats = await run_feishu_sync(
            kb_uuid,
            session_factory=async_session_factory,
            data_dir=settings.data_dir,
            encryption_secret=settings.jwt_secret,
            enqueue_ingest=lambda doc_id: _enqueue_ingest(str(doc_id)),
        )
        payload = stats.model_dump(mode="json")
    except Exception as exc:
        async with async_session_factory() as session:
            job = await session.get(IndexJob, job_uuid)
            if job is not None:
                job.state = "failed"
                job.error = str(exc)
                await session.commit()
        raise

    async with async_session_factory() as session:
        job = await session.get(IndexJob, job_uuid)
        if job is not None:
            job.state = "failed" if stats.errors else "succeeded"
            job.error = "; ".join(stats.errors) if stats.errors else None
            job.stats = payload
            await session.commit()

    return payload


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    functions = [ingest_document, sync_feishu]
