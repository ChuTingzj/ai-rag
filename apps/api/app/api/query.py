from __future__ import annotations

import time
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.deps import get_async_session, get_current_user, get_orchestrator
from app.db.models import Chunk, QueryTrace, User
from domain.models import QueryRequest
from orchestrator.service import OrchestratorService
from app.schemas.api import CitationOut, QueryRequestIn, QueryResponseOut

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponseOut)
async def query(
    body: QueryRequestIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    orchestrator: Annotated[OrchestratorService, Depends(get_orchestrator)],
) -> QueryResponseOut:
    started = time.perf_counter()
    request = QueryRequest(
        user_id=user.id,
        question=body.question,
        kb_ids=body.kb_ids,
    )
    result = await orchestrator.run(request)
    latency_ms = int((time.perf_counter() - started) * 1000)

    trace = QueryTrace(
        user_id=user.id,
        kb_ids=body.kb_ids,
        question=body.question,
        route=result.route,
        answer=result.answer or None,
        evidence_ids=[c.evidence_id for c in result.citations],
        model=None,
        steps={"route_hint": body.route_hint},
        latency_ms=latency_ms,
    )
    session.add(trace)
    await session.commit()
    await session.refresh(trace)

    citations = await _enrich_citations(session, result.citations)

    return QueryResponseOut(
        answer=result.answer,
        citations=citations,
        route=result.route,
        refuse_reason=result.refuse_reason.value if result.refuse_reason else None,
        trace_id=trace.id,
    )


async def _enrich_citations(session: AsyncSession, citations) -> list[CitationOut]:
    if not citations:
        return []

    ids = [c.evidence_id for c in citations]
    rows = await session.execute(
        select(Chunk).options(joinedload(Chunk.document)).where(Chunk.id.in_(ids))
    )
    chunks = {row.id: row for row in rows.scalars().unique().all()}

    out: list[CitationOut] = []
    for cite in citations:
        chunk = chunks.get(cite.evidence_id)
        doc = chunk.document if chunk else None
        out.append(
            CitationOut(
                evidence_id=cite.evidence_id,
                document_id=chunk.document_id if chunk else None,
                title=cite.title or (doc.title if doc else None),
                uri=cite.uri or (doc.uri if doc else None),
                snippet=chunk.text[:500] if chunk else None,
                index=cite.index,
            )
        )
    return out
