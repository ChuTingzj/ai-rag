from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import SyncQueue, get_async_session, get_current_user, get_sync_queue
from app.db.models import Connector, IndexJob, KnowledgeBase, User
from app.schemas.api import ConnectorOut, FeishuConnectorCreate, SyncTriggerOut
from connectors.base import encrypt_connector_config

router = APIRouter(prefix="/knowledge-bases/{kb_id}", tags=["connectors"])


async def _get_owned_kb(kb_id: uuid.UUID, user: User, session: AsyncSession) -> KnowledgeBase:
    kb = await session.get(KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    if kb.created_by != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return kb


def _require_encryption_secret() -> str:
    if not settings.jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT_SECRET is required to store connector credentials",
        )
    return settings.jwt_secret


@router.post("/connectors/feishu", response_model=ConnectorOut, status_code=status.HTTP_201_CREATED)
async def bind_feishu_connector(
    kb_id: uuid.UUID,
    body: FeishuConnectorCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Connector:
    _ = user
    await _get_owned_kb(kb_id, user, session)
    secret = _require_encryption_secret()

    encrypted = encrypt_connector_config(
        {
            "app_id": body.app_id,
            "app_secret": body.app_secret,
            "space_id": body.space_id,
        },
        secret=secret,
    )

    result = await session.execute(
        select(Connector).where(Connector.kb_id == kb_id, Connector.type == "feishu").limit(1)
    )
    connector = result.scalar_one_or_none()
    if connector is None:
        connector = Connector(
            kb_id=kb_id,
            type="feishu",
            config_encrypted=encrypted,
            enabled=True,
        )
        session.add(connector)
    else:
        connector.config_encrypted = encrypted
        connector.enabled = True

    await session.commit()
    await session.refresh(connector)
    return connector


@router.post("/sync", response_model=SyncTriggerOut, status_code=status.HTTP_202_ACCEPTED)
async def trigger_sync(
    kb_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    queue: Annotated[SyncQueue, Depends(get_sync_queue)],
) -> SyncTriggerOut:
    _ = user
    await _get_owned_kb(kb_id, user, session)

    result = await session.execute(
        select(Connector).where(
            Connector.kb_id == kb_id,
            Connector.type == "feishu",
            Connector.enabled.is_(True),
        )
    )
    connector = result.scalar_one_or_none()
    if connector is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bind a Feishu connector before syncing",
        )

    job = IndexJob(kb_id=kb_id, job_type="feishu_sync", state="pending")
    session.add(job)
    await session.commit()
    await session.refresh(job)

    await queue.enqueue(kb_id, job_id=job.id)
    return SyncTriggerOut(job_id=job.id)
