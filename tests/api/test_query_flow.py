from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core import deps
from app.core.config import settings
from app.main import app
from domain.models import LLMResult, Message
from ingest.pipeline import run_ingest
from providers.registry import Settings as RagSettings


def _async_database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://rag:rag@localhost:15432/rag",
    )


@dataclass
class StubLLM:
    content: str = "费用上限为 3000 元[E1]。"

    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResult:
        _ = messages, model, temperature, max_tokens
        return LLMResult(content=self.content, model="stub")


@dataclass
class SyncIngestQueue:
    factory: async_sessionmaker

    async def enqueue(self, document_id: uuid.UUID) -> None:
        rag = RagSettings(
            embedding_provider=settings.embedding_provider,
            embedding_dim=settings.embedding_dim,
            rerank_provider=settings.rerank_provider,
        )
        await run_ingest(
            document_id,
            session_factory=self.factory,
            settings=rag,
        )


@pytest.fixture
def api_client(migrated_engine, tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        settings,
        "jwt_secret",
        "test-jwt-secret-for-api-e2e-32bytes-min",
    )
    monkeypatch.setattr(settings, "embedding_provider", "hash_stub")
    monkeypatch.setattr(settings, "embedding_dim", 1024)
    monkeypatch.setattr(settings, "rerank_provider", "stub")
    monkeypatch.setattr(settings, "data_dir", str(tmp_path / "data"))

    engine = create_async_engine(_async_database_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    deps.async_session_factory = factory

    queue = SyncIngestQueue(factory=factory)
    app.dependency_overrides[deps.get_llm] = lambda: StubLLM()
    app.dependency_overrides[deps.get_ingest_queue] = lambda: queue

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_kb_upload_wait_query(api_client: TestClient, tmp_path):
    email = f"user-{uuid.uuid4()}@example.com"
    password = "secure-pass-123"

    reg = api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert reg.status_code == 201, reg.text
    user = reg.json()
    assert user["email"] == email

    login = api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = _auth_headers(token)

    me = api_client.get("/api/v1/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == email

    kb = api_client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "Policies", "description": "HR policies"},
    )
    assert kb.status_code == 201, kb.text
    kb_id = kb.json()["id"]

    md = tmp_path / "expense.md"
    md.write_text(
        "# Expense policy\n\n费用上限为 3000 元。\n\n" + ("detail " * 40),
        encoding="utf-8",
    )
    with md.open("rb") as fh:
        upload = api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents",
            headers=headers,
            files={"file": ("expense.md", fh, "text/markdown")},
        )
    assert upload.status_code == 201, upload.text
    body = upload.json()
    job_id = body["job_id"]
    assert body["document"]["status"] in ("pending", "indexing", "ready")

    deadline = time.time() + 30
    state = "pending"
    while time.time() < deadline:
        job = api_client.get(f"/api/v1/jobs/{job_id}", headers=headers)
        assert job.status_code == 200, job.text
        state = job.json()["state"]
        if state in ("succeeded", "failed"):
            break
        time.sleep(0.2)
    assert state == "succeeded", job.json()

    docs = api_client.get(f"/api/v1/knowledge-bases/{kb_id}/documents", headers=headers)
    assert docs.status_code == 200
    assert any(d["status"] == "ready" for d in docs.json())

    query = api_client.post(
        "/api/v1/query",
        headers=headers,
        json={"question": "费用上限是多少？", "kb_ids": [kb_id]},
    )
    assert query.status_code == 200, query.text
    payload = query.json()
    assert payload["route"] == "single"
    assert payload["refuse_reason"] is None
    assert "3000" in payload["answer"] or "[E1]" in payload["answer"]
    assert payload["trace_id"]
    assert payload["citations"]
    cite = payload["citations"][0]
    assert cite["evidence_id"]
    assert cite.get("title") == "expense.md" or cite.get("title")
