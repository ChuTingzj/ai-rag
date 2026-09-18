from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    roles: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str | None = None


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class KnowledgeBaseOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: uuid.UUID
    kb_id: uuid.UUID
    source: str
    title: str | None
    uri: str | None
    mime_type: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadOut(BaseModel):
    document: DocumentOut
    job_id: uuid.UUID


class DocumentContentOut(BaseModel):
    id: uuid.UUID
    kb_id: uuid.UUID
    title: str | None
    mime_type: str | None
    content: str


class IndexJobOut(BaseModel):
    id: uuid.UUID
    kb_id: uuid.UUID | None
    document_id: uuid.UUID | None
    job_type: str | None
    state: str | None
    error: str | None
    stats: dict | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class QueryRequestIn(BaseModel):
    question: str
    kb_ids: list[uuid.UUID]
    route_hint: str | None = None


class CitationOut(BaseModel):
    evidence_id: uuid.UUID
    document_id: uuid.UUID | None = None
    kb_id: uuid.UUID | None = None
    title: str | None = None
    uri: str | None = None
    snippet: str | None = None
    score: float | None = None
    index: int | None = None


class QueryResponseOut(BaseModel):
    answer: str
    citations: list[CitationOut]
    route: str
    refuse_reason: str | None
    trace_id: uuid.UUID


class FeishuConnectorCreate(BaseModel):
    app_id: str
    app_secret: str
    space_id: str


class ConnectorOut(BaseModel):
    id: uuid.UUID
    kb_id: uuid.UUID | None
    type: str | None
    enabled: bool | None
    cursor: str | None

    model_config = {"from_attributes": True}


class SyncTriggerOut(BaseModel):
    job_id: uuid.UUID
