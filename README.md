# AI RAG — M1 Hybrid RAG Platform

Enterprise knowledge assistant: FastAPI backend, PostgreSQL (pgvector), Redis, and a Next.js UI (added in later milestones). See [TECH_DESIGN.md](./TECH_DESIGN.md) and [PRD.md](./PRD.md).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python 3.12+)
- [Docker](https://www.docker.com/) (Compose v2)
- [pnpm](https://pnpm.io/) (for the web app in Task 9+)

## Quick start

### 1. Infrastructure

```bash
cp .env.example .env
# Edit .env with secrets (OPENROUTER_API_KEY, JWT_SECRET, etc.)

docker compose up -d postgres redis
```

### 2. Python (uv workspace)

Install dependencies and run tests:

```bash
uv sync --all-groups
uv run pytest tests/ -v
```

Start the API:

```bash
uv run uvicorn apps.api.app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: `GET http://localhost:8000/health` → `{"status":"ok"}`.

### 3. Frontend (later tasks)

From `apps/web` (once scaffolded):

```bash
pnpm install
pnpm dev
```

## Repository layout

- `apps/api` — FastAPI application
- `packages/rag` — domain library (ingest, retrieve, generate)
- `tests/` — integration and unit tests
- `docker-compose.yml` — Postgres (pgvector) + Redis

Python packages are managed **only** with `uv` (`uv sync`, `uv add`, `uv run`). Commit `uv.lock`.
