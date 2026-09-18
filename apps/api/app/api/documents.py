from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from ingest.parse import parse_file
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import IngestQueue, Principal, get_async_session, get_current_user, get_ingest_queue
from app.db.models import Document, IndexJob, KnowledgeBase
from app.schemas.api import DocumentContentOut, DocumentOut, DocumentUploadOut

router = APIRouter(prefix="/knowledge-bases/{kb_id}/documents", tags=["documents"])


async def _get_owned_kb(kb_id: uuid.UUID, user: Principal, session: AsyncSession) -> KnowledgeBase:
    kb = await session.get(KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    if kb.created_by != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return kb


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    kb_id: uuid.UUID,
    user: Annotated[Principal, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[Document]:
    await _get_owned_kb(kb_id, user, session)
    result = await session.execute(
        select(Document).where(Document.kb_id == kb_id).order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{document_id}/content", response_model=DocumentContentOut)
async def get_document_content(
    kb_id: uuid.UUID,
    document_id: uuid.UUID,
    user: Annotated[Principal, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> DocumentContentOut:
    await _get_owned_kb(kb_id, user, session)
    document = await session.get(Document, document_id)
    if document is None or document.kb_id != kb_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if not document.raw_path:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document has no stored file",
        )

    path = Path(document.raw_path)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found")

    try:
        content = parse_file(path, document.mime_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return DocumentContentOut(
        id=document.id,
        kb_id=document.kb_id,
        title=document.title,
        mime_type=document.mime_type,
        content=content,
    )


@router.post("", response_model=DocumentUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    kb_id: uuid.UUID,
    user: Annotated[Principal, Depends(get_current_user)],
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

    checksum = hashlib.sha256(raw_bytes).hexdigest()
    existing = (
        await session.execute(
            select(Document).where(
                Document.kb_id == kb_id,
                Document.source == "upload",
                Document.external_id == checksum,
            )
        )
    ).scalar_one_or_none()

    doc_id = existing.id if existing is not None else uuid.uuid4()
    safe_name = Path(file.filename).name
    dest_dir = Path(settings.data_dir) / str(kb_id) / str(doc_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = (dest_dir / safe_name).resolve()
    dest_path.write_bytes(raw_bytes)

    mime = file.content_type or "application/octet-stream"
    uri = f"/files/{kb_id}/{doc_id}/{safe_name}"
    if existing is None:
        document = Document(
            id=doc_id,
            kb_id=kb_id,
            source="upload",
            external_id=checksum,
            title=safe_name,
            uri=uri,
            mime_type=mime,
            status="pending",
            checksum=checksum,
            raw_path=str(dest_path),
        )
        session.add(document)
    else:
        document = existing
        document.title = safe_name
        document.uri = uri
        document.mime_type = mime
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
    await session.commit()
    await session.refresh(document)
    await session.refresh(job)

    await queue.enqueue(doc_id)

    return DocumentUploadOut(document=DocumentOut.model_validate(document), job_id=job.id)
