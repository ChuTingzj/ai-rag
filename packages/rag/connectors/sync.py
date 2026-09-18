from __future__ import annotations

import hashlib
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from connectors.base import decrypt_connector_config
from connectors.feishu import FeishuConnector
from db.models import Document, IndexJob
from domain.models import RawDocument


class FeishuSyncStats(BaseModel):
    kb_id: uuid.UUID
    documents_synced: int = 0
    documents_queued: int = 0
    next_cursor: str | None = None
    errors: list[str] = Field(default_factory=list)


@dataclass(slots=True)
class ConnectorSnapshot:
    id: uuid.UUID
    config_encrypted: bytes
    cursor: str | None


EnqueueIngest = Callable[[uuid.UUID], Awaitable[None]]
LoadConnector = Callable[[], Awaitable[ConnectorSnapshot]]
SaveCursor = Callable[[str | None], Awaitable[None]]


async def run_feishu_sync(
    kb_id: uuid.UUID,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    data_dir: str,
    encryption_secret: str,
    enqueue_ingest: EnqueueIngest,
    load_connector: LoadConnector,
    save_cursor: SaveCursor,
    connector: FeishuConnector | None = None,
) -> FeishuSyncStats:
    stats = FeishuSyncStats(kb_id=kb_id)

    connector_row = await load_connector()
    if not connector_row.config_encrypted:
        raise ValueError("Feishu connector is not configured")

    config = decrypt_connector_config(
        connector_row.config_encrypted,
        secret=encryption_secret,
    )

    feishu = connector or FeishuConnector(
        app_id=str(config["app_id"]),
        app_secret=str(config["app_secret"]),
        space_id=str(config["space_id"]),
    )

    async with session_factory() as session:
        async with feishu:
            page = await feishu.list_changes(connector_row.cursor)
            stats.next_cursor = page.next_cursor

            for change in page.changes:
                external_id = str(change.get("external_id") or "")
                if not external_id:
                    continue
                try:
                    raw = await feishu.fetch_document(external_id)
                    if change.get("title"):
                        raw = raw.model_copy(update={"title": str(change["title"])})
                    if change.get("node_token"):
                        meta = {**raw.meta, "node_token": change["node_token"]}
                        uri = f"https://feishu.cn/wiki/{change['node_token']}"
                        raw = raw.model_copy(update={"uri": uri, "meta": meta})

                    queued = await _persist_raw_document(
                        session,
                        kb_id=kb_id,
                        raw=raw,
                        data_dir=data_dir,
                        enqueue_ingest=enqueue_ingest,
                    )
                    stats.documents_synced += 1
                    if queued:
                        stats.documents_queued += 1
                except Exception as exc:
                    stats.errors.append(f"{external_id}: {exc}")

            await session.commit()

    await save_cursor(page.next_cursor)
    return stats


async def _persist_raw_document(
    session: AsyncSession,
    *,
    kb_id: uuid.UUID,
    raw: RawDocument,
    data_dir: str,
    enqueue_ingest: EnqueueIngest,
) -> bool:
    checksum = hashlib.sha256(raw.content).hexdigest()
    result = await session.execute(
        select(Document).where(
            Document.kb_id == kb_id,
            Document.source == "feishu",
            Document.external_id == raw.external_id,
        )
    )
    existing = result.scalar_one_or_none()

    safe_name = f"{raw.external_id}.txt"
    if existing is not None and existing.checksum == checksum and existing.status == "ready":
        return False

    doc_id = existing.id if existing is not None else uuid.uuid4()
    dest_dir = Path(data_dir) / str(kb_id) / str(doc_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = (dest_dir / safe_name).resolve()
    dest_path.write_bytes(raw.content)

    if existing is None:
        document = Document(
            id=doc_id,
            kb_id=kb_id,
            source="feishu",
            external_id=raw.external_id,
            title=raw.title,
            uri=raw.uri,
            mime_type=raw.mime_type,
            status="pending",
            checksum=checksum,
            raw_path=str(dest_path),
        )
        session.add(document)
    else:
        document = existing
        document.title = raw.title
        document.uri = raw.uri
        document.mime_type = raw.mime_type
        document.checksum = checksum
        document.raw_path = str(dest_path)
        document.status = "pending"

    job = IndexJob(
        kb_id=kb_id,
        document_id=doc_id,
        job_type="ingest",
        state="pending",
    )
    session.add(job)
    await session.flush()
    await enqueue_ingest(doc_id)
    return True
