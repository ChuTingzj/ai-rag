from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RefuseReason(StrEnum):
    NO_EVIDENCE = "NO_EVIDENCE"
    UNGROUNDED = "UNGROUNDED"
    NO_PERMISSION = "NO_PERMISSION"


class Message(BaseModel):
    role: str
    content: str


class LLMResult(BaseModel):
    content: str
    model: str
    usage: dict[str, int] = Field(default_factory=dict)

    @property
    def text(self) -> str:
        return self.content


class RerankHit(BaseModel):
    index: int
    score: float


class Evidence(BaseModel):
    evidence_id: UUID
    document_id: UUID
    kb_id: UUID
    text: str
    title: str | None = None
    uri: str | None = None
    score: float
    parent_text: str | None = None


class Citation(BaseModel):
    evidence_id: UUID
    index: int
    title: str | None = None
    uri: str | None = None


class QueryRequest(BaseModel):
    user_id: UUID
    question: str
    kb_ids: list[UUID]


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    route: str = "single"
    trace_id: UUID | None = None
    refuse_reason: RefuseReason | None = None


class QueryContext(BaseModel):
    question: str
    kb_ids: list[UUID]
    user_id: UUID | None = None


class RawDocument(BaseModel):
    external_id: str
    title: str
    uri: str | None = None
    mime_type: str
    content: bytes
    meta: dict[str, Any] = Field(default_factory=dict)

    @property
    def text(self) -> str:
        return self.content.decode("utf-8")


class ChangePage(BaseModel):
    changes: list[dict[str, Any]] = Field(default_factory=list)
    next_cursor: str | None = None
