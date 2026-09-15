from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.deps import SyncQueue, get_sync_queue, require_internal_token

router = APIRouter(prefix="/internal/v1", tags=["internal"])


class FeishuSyncEnqueueIn(BaseModel):
    kb_id: uuid.UUID
    job_id: uuid.UUID = Field(...)


@router.post("/enqueue/feishu-sync", status_code=202)
async def enqueue_feishu_sync(
    body: FeishuSyncEnqueueIn,
    _: Annotated[None, Depends(require_internal_token)],
    queue: Annotated[SyncQueue, Depends(get_sync_queue)],
) -> dict[str, str]:
    await queue.enqueue(body.kb_id, job_id=body.job_id)
    return {"status": "queued"}
