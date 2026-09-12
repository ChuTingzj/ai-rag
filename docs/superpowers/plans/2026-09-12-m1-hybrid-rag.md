# M1 Hybrid RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a locally runnable M1 enterprise knowledge assistant: upload + Feishu sync, Hybrid+Rerank retrieval, OpenRouter cited answers, and a naive-vs-hybrid eval script.

**Architecture:** FastAPI + arq worker + PostgreSQL 16/pgvector + Redis; domain logic in `packages/rag` with pluggable LLM/Embedding providers; React UI per ui-ux-pro-max design system. See [`TECH_DESIGN.md`](../../../TECH_DESIGN.md).

**Tech Stack:** Python 3.12 managed by **uv**, FastAPI, SQLAlchemy 2, Alembic, **pgvector**, Redis/arq, sentence-transformers (bge-m3), bge-reranker, OpenRouter, **Next.js 16.3.5** (App Router) via **pnpm** + Phosphor + design-system tokens, Docker Compose (`pgvector/pgvector:pg16`).

## Global Constraints

- LLM calls go **only** through OpenRouter (`LLMProvider` → OpenRouter).
- Embedding is pluggable; default `local_bge_m3` (`BAAI/bge-m3`).
- **Vector store is PostgreSQL + pgvector** (no Qdrant). Lexical = `tsvector` (optional bm25s).
- M1 Wiki connector is **Feishu**; other connectors are stubs only.
- ACL Gateway exists but M1 implementation is allow-all; do not skip the hook.
- No LangChain/LlamaIndex as runtime core.
- Every query path must support citation IDs or explicit refuse.
- Config via environment variables; never commit secrets.
- Follow [`TECH_DESIGN.md`](../../../TECH_DESIGN.md) module layout under `apps/` and `packages/rag/`.
- **Frontend MUST follow** `design-system/enterprise-knowledge-assistant/MASTER.md` (+ page overrides). Icons: Phosphor only.
- **Python package management: uv only** (`uv sync`, `uv add`, `uv run`, commit `uv.lock`). Do not use pip/Poetry as the project workflow.
- **Frontend package management: pnpm only** (`pnpm install`, `pnpm add`, `pnpm build`, commit `pnpm-lock.yaml`). Do not use npm/yarn as the project workflow.
- **Frontend framework: Next.js exactly `16.3.5`** (App Router). Do not use Vite SPA. Do not replace FastAPI RAG APIs with Next Route Handlers in M1.

---

## File map (create in tasks below)

```
apps/api/app/{main,deps,core/config,core/security,api/*.py}
apps/web/{app,components,styles/tokens.css,package.json,next.config.ts}
packages/rag/{domain,providers,connectors,ingest,retrieve,generate,orchestrator,eval,acl}
migrations/versions/*.py
tests/...
evals/m1/golden.jsonl
docker-compose.yml
.env.example
pyproject.toml
uv.lock
apps/web/pnpm-lock.yaml
```

---

### Task 1: Monorepo scaffold + Compose + config

**Files:**
- Create: `pyproject.toml` (uv workspace: `apps/api`, `packages/rag`)
- Create: `uv.lock` (via `uv sync`)
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `packages/rag/pyproject.toml`
- Create: `apps/api/app/core/config.py`
- Create: `apps/api/app/main.py` (health only)
- Create: `README.md` (run instructions with `uv` / `pnpm`)
- Test: `tests/test_health.py`

**Interfaces:**
- Produces: `Settings` with `openrouter_api_key`, `openrouter_model`, `database_url`, `redis_url`, `embedding_provider`, `embedding_dim`, `jwt_secret`, `data_dir`

- [ ] **Step 1: Write failing health test**

```python
# tests/test_health.py
from fastapi.testclient import TestClient
from apps.api.app.main import app

def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
```

- [ ] **Step 2: Run test — expect fail (app missing)**

Run: `uv run pytest tests/test_health.py -v`  
Expected: FAIL import or 404

- [ ] **Step 3: Implement minimal FastAPI app + Settings + compose + `uv sync`**

`Settings` loads from env; `GET /health` returns `{"status":"ok"}`.  
`docker-compose.yml` defines `postgres` (image `pgvector/pgvector:pg16`), `redis` (api can wait until Task 2).

- [ ] **Step 4: Re-run test — expect pass**

Run: `uv run pytest tests/test_health.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock docker-compose.yml .env.example apps/api packages/rag README.md tests/test_health.py
git commit -m "chore: scaffold M1 monorepo with uv, compose, and health endpoint"
```

---

### Task 2: Domain models + Postgres schema + Alembic

**Files:**
- Create: `packages/rag/domain/models.py` (Pydantic: Evidence, QueryRequest, QueryResponse, Citation, …)
- Create: `packages/rag/domain/protocols.py`
- Create: `apps/api/app/db/base.py`, `apps/api/app/db/models.py`
- Create: `migrations/env.py`, `migrations/versions/001_m1_init.py`
- Test: `tests/test_db_models.py`

**Interfaces:**
- Produces: SQLAlchemy models `User`, `KnowledgeBase`, `Document`, `Chunk`, `IndexJob`, `Connector`, `QueryTrace` matching TECH_DESIGN §7.1
- Produces: Pydantic `Evidence(evidence_id, document_id, kb_id, text, title, uri, score, parent_text | None)`

- [ ] **Step 1: Write test that metadata tables migrate**

```python
import pytest
from sqlalchemy import inspect

@pytest.mark.asyncio
async def test_tables_exist(migrated_engine):
    tables = inspect(migrated_engine).get_table_names()
    for name in ["users", "knowledge_bases", "documents", "chunks", "index_jobs"]:
        assert name in tables
```

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement models + Alembic revision `001_m1_init`** (`CREATE EXTENSION vector`, chunks.embedding, chunks.tsv, HNSW + GIN indexes)

- [ ] **Step 4: Run migrations + test — expect pass**

Run: `uv run alembic upgrade head && uv run pytest tests/test_db_models.py -v`

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: add M1 postgres schema and domain protocols"
```

---

### Task 3: Providers — OpenRouter LLM + local bge-m3 Embedding + Reranker

**Files:**
- Create: `packages/rag/providers/openrouter_llm.py`
- Create: `packages/rag/providers/local_bge_m3.py`
- Create: `packages/rag/providers/openrouter_embedding.py`
- Create: `packages/rag/providers/bge_reranker.py`
- Create: `packages/rag/providers/registry.py`
- Test: `tests/providers/test_rrf_and_registry.py` (registry unit); `tests/providers/test_openrouter_llm.py` (mock httpx)

**Interfaces:**
- Produces: `get_llm() -> LLMProvider`, `get_embedding() -> EmbeddingProvider`, `get_reranker() -> RerankProvider`
- Consumes: `Settings`

- [ ] **Step 1: Write mock httpx test for OpenRouter chat**

```python
@pytest.mark.asyncio
async def test_openrouter_complete(httpx_mock):
    httpx_mock.add_response(json={
        "choices": [{"message": {"content": "hello [E1]"}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1}
    })
    llm = OpenRouterLLM(api_key="t", model="openai/gpt-4.1-mini", base_url="https://openrouter.ai/api/v1")
    result = await llm.complete([Message(role="user", content="hi")])
    assert "hello" in result.text
```

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement providers + registry**

Local embedding may skip model download in CI via `EMBEDDING_PROVIDER=hash_stub` test double that returns deterministic vectors.

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: add OpenRouter LLM and pluggable embedding/rerank providers"
```

---

### Task 4: Ingest — parse, parent-child chunk, index job worker

**Files:**
- Create: `packages/rag/ingest/parse.py`
- Create: `packages/rag/ingest/chunk.py`
- Create: `packages/rag/ingest/pipeline.py`
- Create: `packages/rag/ingest/pgvector_store.py`
- Create: `apps/api/app/workers/tasks.py`
- Test: `tests/ingest/test_chunker.py`, `tests/ingest/test_pipeline_integration.py`

**Interfaces:**
- Produces: `async def run_ingest(document_id: UUID) -> IndexJobStats`
- Produces: `Chunker.split(text) -> list[ChunkDraft]` with `parent_text` / `child_text`
- Consumes: `EmbeddingProvider`, asyncpg/SQLAlchemy session (pgvector upsert)

- [ ] **Step 1: Chunker unit tests (parent/child counts, non-empty)**

```python
def test_parent_child_chunker_basic():
    text = "# A\n" + ("para " * 200) + "\n# B\n" + ("para " * 200)
    chunks = ParentChildChunker().split(text)
    assert any(c.parent_text for c in chunks)
    assert all(c.child_text.strip() for c in chunks)
```

- [ ] **Step 2: Run — fail**

- [ ] **Step 3: Implement parser (md/txt/pdf/docx), chunker, pgvector+tsv upsert, arq task `ingest_document`**

- [ ] **Step 4: Integration test against compose Postgres — pass**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: implement ingest pipeline with parent-child chunking and pgvector"
```

---

### Task 5: Hybrid retrieve + RRF + rerank + ACL noop hook

**Files:**
- Create: `packages/rag/retrieve/hybrid.py`
- Create: `packages/rag/retrieve/rrf.py`
- Create: `packages/rag/retrieve/packer.py`
- Create: `packages/rag/acl/gateway.py`
- Test: `tests/retrieve/test_rrf.py`, `tests/retrieve/test_hybrid.py`

**Interfaces:**
- Produces: `HybridRetriever.retrieve(query, kb_ids, top_k) -> list[Evidence]`
- Produces: `rrf_fuse(rank_lists: list[list[str]], k: int = 60) -> list[str]`
- Produces: `AclGateway.filter(user, evidences) -> list[Evidence]` (M1: identity)
- Produces: `ContextPacker.pack(evidences, max_tokens) -> PackedContext`

- [ ] **Step 1: RRF unit test**

```python
def test_rrf_prefers_overlap():
    a = ["d1", "d2", "d3"]
    b = ["d3", "d1", "d4"]
    fused = rrf_fuse([a, b], k=60)
    assert fused[0] == "d1" or fused[0] == "d3"
    assert set(fused[:2]) == {"d1", "d3"}
```

- [ ] **Step 2: Run — fail**

- [ ] **Step 3: Implement dense pgvector search + tsv/BM25 + RRF + rerank + packer + ACL noop**

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: add hybrid retrieval with RRF, rerank, and ACL hook"
```

---

### Task 6: Generator with citation enforcement + Orchestrator single route

**Files:**
- Create: `packages/rag/generate/prompts.py`
- Create: `packages/rag/generate/citations.py`
- Create: `packages/rag/generate/generator.py`
- Create: `packages/rag/orchestrator/service.py`
- Test: `tests/generate/test_citations.py`, `tests/orchestrator/test_single_route.py`

**Interfaces:**
- Produces: `parse_citations(answer: str) -> set[int]`
- Produces: `Generator.generate(question, packed) -> GenerateResult`
- Produces: `Orchestrator.run(QueryRequest) -> QueryResponse` with `route="single"`
- Consumes: `Retriever`, `AclGateway`, `LLMProvider`

- [ ] **Step 1: Citation parser tests**

```python
def test_parse_citations():
    assert parse_citations("费用上限为 3000 元[E1]。详见[E2]") == {1, 2}

def test_ungrounded_refuses():
    validator = CitationValidator(strictness="strict")
    result = validator.validate("随便说一句无引用", evidence_count=2)
    assert result.refuse_reason == "UNGROUNDED"
```

- [ ] **Step 2: Run — fail**

- [ ] **Step 3: Implement prompts, validator, generator, orchestrator; empty evidence → `NO_EVIDENCE`**

- [ ] **Step 4: Tests pass with mocked LLM**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: cited generation and single-route orchestrator"
```

---

### Task 7: HTTP API — auth, KB, upload, jobs, query

**Files:**
- Create: `apps/api/app/api/auth.py`
- Create: `apps/api/app/api/knowledge_bases.py`
- Create: `apps/api/app/api/documents.py`
- Create: `apps/api/app/api/query.py`
- Create: `apps/api/app/api/jobs.py`
- Test: `tests/api/test_query_flow.py`

**Interfaces:**
- Produces: REST paths per TECH_DESIGN §9
- Consumes: Orchestrator, ingest enqueue

- [ ] **Step 1: API test — register, create KB, upload md, wait job, query**

Use temp files and mocked LLM/embedding stub providers via env.

- [ ] **Step 2: Run — fail**

- [ ] **Step 3: Implement routers + JWT auth + multipart upload → enqueue ingest**

- [ ] **Step 4: End-to-end API test pass**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: expose M1 REST API for auth, KB, upload, and query"
```

---

### Task 8: Feishu connector

**Files:**
- Create: `packages/rag/connectors/base.py`
- Create: `packages/rag/connectors/feishu.py`
- Create: `packages/rag/connectors/notion_stub.py`
- Create: `packages/rag/connectors/confluence_stub.py`
- Create: `apps/api/app/api/connectors.py`
- Test: `tests/connectors/test_feishu_mapping.py` (fixture JSON → RawDocument)

**Interfaces:**
- Produces: `FeishuConnector.list_changes` / `fetch_document`
- Produces: API `POST /knowledge-bases/{id}/connectors/feishu`, `POST .../sync`

- [ ] **Step 1: Fixture mapping test**

```python
def test_feishu_page_to_raw_document():
    raw = map_feishu_page(FEISHU_PAGE_FIXTURE)
    assert raw.title
    assert raw.text
    assert raw.external_id
```

- [ ] **Step 2–4: Implement connector + sync worker task + API; stubs raise `NotImplementedError` with clear message**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: add Feishu read-only connector and sync job"
```

---

### Task 9: Web UI — Next.js 16.3.5 + ui-ux-pro-max + login/KB/chat

**Files:**
- Create: `apps/web` Next.js App Router app with `"next": "16.3.5"` pinned
- Create: `apps/web/styles/tokens.css` (map MASTER CSS variables)
- Create: `apps/web/app/login/page.tsx`, `apps/web/app/page.tsx`, `apps/web/app/kbs/...`
- Create: `apps/web/next.config.ts` (`output: 'standalone'`; optional rewrite `/api` → FastAPI)
- Read first: `design-system/enterprise-knowledge-assistant/MASTER.md` + matching `pages/*.md`
- Test: `pnpm --dir apps/web build`; visual checklist against MASTER pre-delivery list

**Interfaces:**
- Consumes: FastAPI `/api/v1/*` via `NEXT_PUBLIC_API_BASE_URL` or rewrites
- UI constraints: Phosphor icons; Plus Jakarta Sans; Flat teal/orange; skeletons + aria-busy on query; citation side panel on chat

- [ ] **Step 1: Scaffold with pnpm + exact Next version**

```bash
cd apps && pnpm create next-app@16.3.5 web --typescript --eslint --app --src-dir=false --tailwind=false --import-alias="@/*"
cd web && pnpm add next@16.3.5 && pnpm add @phosphor-icons/react
```

Verify `package.json` has `"next": "16.3.5"`. Add `styles/tokens.css` from MASTER.

- [ ] **Step 2: Login page per `pages/login.md` (labels, submit feedback)**

- [ ] **Step 3: KB list/detail per `pages/knowledge-base.md` (upload, sync, job status)**

- [ ] **Step 4: Chat per `pages/chat.md` — answer + citation panel + loading skeleton**

- [ ] **Step 5: `pnpm --dir apps/web build` + commit**

```bash
git add apps/web
git commit -m "feat: add M1 Next.js 16.3.5 web UI with ui-ux-pro-max design system"
```

---

### Task 10: Eval harness + Compose smoke + M1 acceptance

**Files:**
- Create: `evals/m1/golden.jsonl`
- Create: `packages/rag/eval/run.py`
- Create: `scripts/smoke_m1.sh`
- Modify: `README.md` acceptance section
- Test: `tests/eval/test_run_naive_vs_hybrid.py`

**Interfaces:**
- Produces: CLI `uv run python -m rag.eval.run --pipeline naive|hybrid --out reports/m1.json`
- Metrics: `retrieval_hit_rate`, `citation_precision`

- [ ] **Step 1: Add ≥20 golden questions (can use synthetic docs under `evals/m1/corpus/`)**

- [ ] **Step 2: Implement naive (dense-only, no rerank) vs hybrid runners sharing ingest**

- [ ] **Step 3: Assert hybrid retrieval_hit_rate >= naive on golden (soft assert logged if flaky; hard assert citation_precision defined)**

- [ ] **Step 4: `scripts/smoke_m1.sh` brings up compose, runs migrate, indexes sample, curls `/query`**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: add M1 eval harness and smoke script"
```

---

## M2–M4

Out of scope for this plan. After M1 acceptance, write:

- `docs/superpowers/plans/2026-09-XX-m2-acl-adaptive.md`
- `docs/superpowers/plans/2026-09-XX-m3-agentic.md`
- `docs/superpowers/plans/2026-09-XX-m4-graphrag.md`

---

## Spec coverage check (M1)

| PRD FR | Task |
| --- | --- |
| FR-01 | 7, 9 |
| FR-02 | 8 |
| FR-03 | 5 |
| FR-04 | 4, 6 |
| FR-05 | 3 |
| FR-06 | 4, 7 |
| FR-07 | 10 |
| S1 local compose | 1, 10 |
| ACL hook present | 5 |
| OpenRouter only | 3, 6 |
