from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import IngestQueue, get_async_session, get_current_user, get_ingest_queue
from app.db.models import Document, IndexJob, KnowledgeBase, User
from app.schemas.api import DocumentOut, DocumentUploadOut

router = APIRouter(prefix="/knowledge-bases/{kb_id}/documents", tags=["documents"])


async def _get_owned_kb(kb_id: uuid.UUID, user: User, session: AsyncSession) -> KnowledgeBase:
    kb = await session.get(KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    if kb.created_by != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return kb


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    kb_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[Document]:
    await _get_owned_kb(kb_id, user, session)
    result = await session.execute(
        select(Document).where(Document.kb_id == kb_id).order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=DocumentUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    kb_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    queue: Annotated[IngestQueue, Depends(get_ingest_queue)],
    file: UploadFile = File(...),
) -> DocumentUploadOut:
    _ = user
    await _get_owned_kb(kb_id, user, session)
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    doc_id = uuid.uuid4()
    safe_name = Path(file.filename).name
    dest_dir = Path(settings.data_dir) / str(kb_id) / str(doc_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / safe_name
    dest_path.write_bytes(raw_bytes)

    checksum = hashlib.sha256(raw_bytes).hexdigest()
    mime = file.content_type or "application/octet-stream"
    document = Document(
        id=doc_id,
        kb_id=kb_id,
        source="upload",
        external_id=checksum,
        title=safe_name,
        uri=f"/files/{kb_id}/{doc_id}/{safe_name}",
        mime_type=mime,
        status="pending",
        checksum=checksum,
        raw_path=str(dest_path),
    )
    job = IndexJob(
        kb_id=kb_id,
        document_id=doc_id,
        job_type="ingest",
        state="pending",
    )
    session.add(document)
    session.add(job)
    await session.commit()
    await session.refresh(document)
    await session.refresh(job)

    await queue.enqueue(doc_id)

    return DocumentUploadOut(document=DocumentOut.model_validate(document), job_id=job.id)
