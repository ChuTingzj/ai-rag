from __future__ import annotations

import io
import os
import time
import uuid
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core import deps
from app.core.config import settings
from app.main import app
from domain.models import LLMResult, Message
from ingest.pipeline import run_ingest
from providers.registry import Settings as RagSettings

_TEST_INTERNAL_TOKEN = "test-internal-service-token"


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
    monkeypatch.setattr(settings, "internal_service_token", _TEST_INTERNAL_TOKEN)
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


def _gateway_headers(user_id: uuid.UUID) -> dict[str, str]:
    return {
        "X-User-Id": str(user_id),
        "X-Internal-Token": _TEST_INTERNAL_TOKEN,
    }


def test_register_kb_upload_wait_query(api_client: TestClient, tmp_path):
    user_id = uuid.uuid4()
    headers = _gateway_headers(user_id)

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
    assert cite.get("document_id")
    assert cite.get("kb_id") == kb_id


def test_document_content_preview(api_client: TestClient, tmp_path):
    user_id = uuid.uuid4()
    headers = _gateway_headers(user_id)

    kb = api_client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "Preview KB", "description": None},
    )
    assert kb.status_code == 201, kb.text
    kb_id = kb.json()["id"]

    payload = "# Preview doc\n\n费用上限为 3000 元。\n".encode("utf-8")
    upload = api_client.post(
        f"/api/v1/knowledge-bases/{kb_id}/documents",
        headers=headers,
        files={"file": ("preview.md", io.BytesIO(payload), "text/markdown")},
    )
    assert upload.status_code == 201, upload.text
    doc_id = upload.json()["document"]["id"]

    content = api_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/content",
        headers=headers,
    )
    assert content.status_code == 200, content.text
    body = content.json()
    assert body["id"] == doc_id
    assert body["kb_id"] == kb_id
    assert body["title"] == "preview.md"
    assert body["mime_type"] == "text/markdown"
    assert "费用上限为 3000 元" in body["content"]

    missing = api_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{uuid.uuid4()}/content",
        headers=headers,
    )
    assert missing.status_code == 404, missing.text

    foreign = api_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/content",
        headers=_gateway_headers(uuid.uuid4()),
    )
    assert foreign.status_code == 403, foreign.text


def test_reupload_same_content_reuses_document(api_client: TestClient) -> None:
    user_id = uuid.uuid4()
    headers = _gateway_headers(user_id)

    kb = api_client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "Dup upload", "description": None},
    )
    assert kb.status_code == 201, kb.text
    kb_id = kb.json()["id"]

    payload = b"# Same file\n\ncontent for checksum dedupe.\n"
    first = api_client.post(
        f"/api/v1/knowledge-bases/{kb_id}/documents",
        headers=headers,
        files={"file": ("research.md", io.BytesIO(payload), "text/markdown")},
    )
    assert first.status_code == 201, first.text
    first_body = first.json()
    doc_id = first_body["document"]["id"]

    second = api_client.post(
        f"/api/v1/knowledge-bases/{kb_id}/documents",
        headers=headers,
        files={"file": ("research.md", io.BytesIO(payload), "text/markdown")},
    )
    assert second.status_code == 201, second.text
    second_body = second.json()
    assert second_body["document"]["id"] == doc_id
    assert second_body["job_id"] != first_body["job_id"]
    assert second_body["document"]["status"] in {"pending", "indexing", "ready"}


def test_query_rejects_foreign_kb_id(api_client: TestClient):
    owner_headers = _gateway_headers(uuid.uuid4())
    kb = api_client.post(
        "/api/v1/knowledge-bases",
        headers=owner_headers,
        json={"name": "Private KB", "description": "owner only"},
    )
    assert kb.status_code == 201, kb.text
    foreign_kb_id = kb.json()["id"]

    attacker_headers = _gateway_headers(uuid.uuid4())
    denied = api_client.post(
        "/api/v1/query",
        headers=attacker_headers,
        json={"question": "费用上限是多少？", "kb_ids": [foreign_kb_id]},
    )
    assert denied.status_code == 403, denied.text


def test_query_empty_kb_ids_scopes_to_owned_only(api_client: TestClient, tmp_path):
    owner_headers = _gateway_headers(uuid.uuid4())
    kb = api_client.post(
        "/api/v1/knowledge-bases",
        headers=owner_headers,
        json={"name": "Owner KB", "description": "secret"},
    )
    assert kb.status_code == 201, kb.text
    kb_id = kb.json()["id"]

    md = tmp_path / "secret.md"
    md.write_text(
        "# Secret\n\n费用上限为 3000 元。\n\n" + ("detail " * 40),
        encoding="utf-8",
    )
    with md.open("rb") as fh:
        upload = api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents",
            headers=owner_headers,
            files={"file": ("secret.md", fh, "text/markdown")},
        )
    assert upload.status_code == 201, upload.text
    job_id = upload.json()["job_id"]
    deadline = time.time() + 30
    state = "pending"
    while time.time() < deadline:
        job = api_client.get(f"/api/v1/jobs/{job_id}", headers=owner_headers)
        state = job.json()["state"]
        if state in ("succeeded", "failed"):
            break
        time.sleep(0.2)
    assert state == "succeeded", job.json()

    owned_empty = api_client.post(
        "/api/v1/query",
        headers=owner_headers,
        json={"question": "费用上限是多少？", "kb_ids": []},
    )
    assert owned_empty.status_code == 200, owned_empty.text
    assert "3000" in owned_empty.json()["answer"] or owned_empty.json()["citations"]

    other_headers = _gateway_headers(uuid.uuid4())
    no_kb = api_client.post(
        "/api/v1/query",
        headers=other_headers,
        json={"question": "费用上限是多少？", "kb_ids": []},
    )
    assert no_kb.status_code == 400, no_kb.text

    other_kb = api_client.post(
        "/api/v1/knowledge-bases",
        headers=other_headers,
        json={"name": "Other empty KB", "description": "no docs"},
    )
    assert other_kb.status_code == 201, other_kb.text

    scoped = api_client.post(
        "/api/v1/query",
        headers=other_headers,
        json={"question": "费用上限是多少？", "kb_ids": []},
    )
    assert scoped.status_code == 200, scoped.text
    payload = scoped.json()
    assert "3000" not in payload["answer"]
    assert payload["refuse_reason"] is not None or not payload["citations"]
