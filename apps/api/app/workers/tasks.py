from __future__ import annotations

import uuid

from arq.connections import RedisSettings

from app.core.config import settings
from app.db.session import async_session_factory
from ingest.pipeline import run_ingest


async def ingest_document(_ctx: dict, document_id: str) -> dict:
    stats = await run_ingest(
        uuid.UUID(document_id),
        session_factory=async_session_factory,
    )
    return stats.model_dump(mode="json")


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    functions = [ingest_document]
