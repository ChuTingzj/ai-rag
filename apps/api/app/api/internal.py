from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import SyncQueue, get_async_session, get_sync_queue, require_internal_token
from app.db.models import IndexJob, KnowledgeBase

router = APIRouter(prefix="/internal/v1", tags=["internal"])


class FeishuSyncEnqueueIn(BaseModel):
    kb_id: uuid.UUID
    job_id: uuid.UUID | None = None


class KbOwnerOut(BaseModel):
    id: uuid.UUID
    created_by: uuid.UUID | None


@router.get("/knowledge-bases/{kb_id}/owner", response_model=KbOwnerOut)
async def get_kb_owner(
    kb_id: uuid.UUID,
    _: Annotated[None, Depends(require_internal_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> KbOwnerOut:
    kb = await session.get(KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    return KbOwnerOut(id=kb.id, created_by=kb.created_by)


@router.post("/enqueue/feishu-sync", status_code=202)
async def enqueue_feishu_sync(
    body: FeishuSyncEnqueueIn,
    _: Annotated[None, Depends(require_internal_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    queue: Annotated[SyncQueue, Depends(get_sync_queue)],
) -> dict[str, str]:
    kb = await session.get(KnowledgeBase, body.kb_id)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")

    if body.job_id is not None:
        job = await session.get(IndexJob, body.job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        job_id = job.id
    else:
        job = IndexJob(kb_id=body.kb_id, job_type="feishu_sync", state="pending")
        session.add(job)
        await session.commit()
        await session.refresh(job)
        job_id = job.id

    await queue.enqueue(body.kb_id, job_id=job_id)
    return {"status": "queued", "job_id": str(job_id)}
