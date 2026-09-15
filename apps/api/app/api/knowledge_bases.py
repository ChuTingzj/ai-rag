from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import Principal, get_async_session, get_current_user
from app.db.models import KnowledgeBase
from app.schemas.api import KnowledgeBaseCreate, KnowledgeBaseOut, KnowledgeBaseUpdate

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.get("", response_model=list[KnowledgeBaseOut])
async def list_knowledge_bases(
    user: Annotated[Principal, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[KnowledgeBase]:
    result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.created_by == user.id).order_by(KnowledgeBase.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=KnowledgeBaseOut, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    body: KnowledgeBaseCreate,
    user: Annotated[Principal, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> KnowledgeBase:
    kb = KnowledgeBase(
        name=body.name,
        description=body.description,
        created_by=user.id,
    )
    session.add(kb)
    await session.commit()
    await session.refresh(kb)
    return kb


async def _get_owned_kb(
    kb_id: uuid.UUID,
    user: Principal,
    session: AsyncSession,
) -> KnowledgeBase:
    kb = await session.get(KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    if kb.created_by != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return kb


@router.get("/{kb_id}", response_model=KnowledgeBaseOut)
async def get_knowledge_base(
    kb_id: uuid.UUID,
    user: Annotated[Principal, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> KnowledgeBase:
    return await _get_owned_kb(kb_id, user, session)


@router.patch("/{kb_id}", response_model=KnowledgeBaseOut)
async def update_knowledge_base(
    kb_id: uuid.UUID,
    body: KnowledgeBaseUpdate,
    user: Annotated[Principal, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> KnowledgeBase:
    kb = await _get_owned_kb(kb_id, user, session)
    if body.name is not None:
        kb.name = body.name
    if body.description is not None:
        kb.description = body.description
    await session.commit()
    await session.refresh(kb)
    return kb


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: uuid.UUID,
    user: Annotated[Principal, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    kb = await _get_owned_kb(kb_id, user, session)
    await session.delete(kb)
    await session.commit()
