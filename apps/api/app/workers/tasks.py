from __future__ import annotations

import base64
import uuid

import httpx
from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import settings
from app.db.models import IndexJob
from app.db.session import async_session_factory
from connectors.sync import ConnectorSnapshot, run_feishu_sync
from ingest.pipeline import run_ingest


async def _enqueue_ingest(document_id: str) -> None:
    pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    try:
        await pool.enqueue_job("ingest_document", document_id)
    finally:
        await pool.close()


def _connectors_headers() -> dict[str, str]:
    return {"X-Internal-Token": settings.internal_service_token}


async def _load_feishu_connector(kb_id: uuid.UUID) -> ConnectorSnapshot:
    url = f"{settings.connectors_service_url.rstrip('/')}/internal/v1/connectors/feishu/{kb_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=_connectors_headers())
        response.raise_for_status()
        payload = response.json()
    return ConnectorSnapshot(
        id=uuid.UUID(str(payload["id"])),
        config_encrypted=base64.b64decode(payload["config_encrypted_b64"]),
        cursor=payload.get("cursor"),
    )


async def _save_connector_cursor(connector_id: uuid.UUID, cursor: str | None) -> None:
    url = f"{settings.connectors_service_url.rstrip('/')}/internal/v1/connectors/{connector_id}/cursor"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.patch(
            url,
            headers={**_connectors_headers(), "content-type": "application/json"},
            json={"cursor": cursor},
        )
        response.raise_for_status()


async def ingest_document(_ctx: dict, document_id: str) -> dict:
    stats = await run_ingest(
        uuid.UUID(document_id),
        session_factory=async_session_factory,
    )
    return stats.model_dump(mode="json")


async def sync_feishu(_ctx: dict, kb_id: str, job_id: str) -> dict:
    secret = settings.connector_encryption_secret or settings.jwt_secret
    if not secret:
        raise RuntimeError("CONNECTOR_ENCRYPTION_SECRET or JWT_SECRET is required for Feishu sync")

    job_uuid = uuid.UUID(job_id)
    kb_uuid = uuid.UUID(kb_id)
    connector_id_holder: dict[str, uuid.UUID] = {}

    async def load_connector() -> ConnectorSnapshot:
        snap = await _load_feishu_connector(kb_uuid)
        connector_id_holder["id"] = snap.id
        return snap

    async def save_cursor(cursor: str | None) -> None:
        await _save_connector_cursor(connector_id_holder["id"], cursor)

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
            encryption_secret=secret,
            enqueue_ingest=lambda doc_id: _enqueue_ingest(str(doc_id)),
            load_connector=load_connector,
            save_cursor=save_cursor,
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
    # First ingest may download BAAI/bge-m3 (~2GB) before encoding.
    job_timeout = 3600
    max_tries = 3
