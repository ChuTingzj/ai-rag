# AI RAG — M1 Hybrid RAG Platform

Enterprise knowledge assistant: NestJS gateway + Auth/Connectors microservices, FastAPI RAG API, PostgreSQL (pgvector), Redis, and Next.js UI. See [TECH_DESIGN.md](./TECH_DESIGN.md) and [PRD.md](./PRD.md).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python 3.12+)
- [Docker](https://www.docker.com/) (Compose v2)
- [pnpm](https://pnpm.io/) 9.x (Nest gateway/services + web)

## Quick start

### 1. Infrastructure

```bash
cp .env.example .env
# Edit .env with secrets (OPENROUTER_API_KEY, JWT_SECRET, INTERNAL_SERVICE_TOKEN, etc.)
./scripts/link-env.sh   # apps/*/.env → ../../.env (idempotent)

docker compose up -d postgres redis
# If the Postgres volume already existed before multi-DB support:
./scripts/ensure-dbs.sh

uv run alembic upgrade head
# Auth / connectors schemas (Prisma owns those DBs):
pnpm --filter @ai-rag/auth prisma:generate && pnpm --filter @ai-rag/auth prisma:push
pnpm --filter @ai-rag/connectors prisma:generate && pnpm --filter @ai-rag/connectors prisma:push
```

### 2. Python (uv workspace)

```bash
uv sync --all-groups
uv run alembic upgrade head
uv run pytest tests/ -v
```

Start the RAG API (behind the gateway in production):

```bash
export INTERNAL_SERVICE_TOKEN=dev-internal-token-change-me
uv run uvicorn apps.api.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. NestJS gateway + microservices (managed with nest-cli)

From the repo root (pnpm workspace: `apps/gateway`, `apps/auth`, `apps/connectors`, `packages/nest-common`):

```bash
pnpm install
pnpm --filter @ai-rag/nest-common build
pnpm --filter @ai-rag/auth prisma:generate
pnpm --filter @ai-rag/connectors prisma:generate
```

Dev (each uses `nest start --watch`; env from root `.env` via symlink):

```bash
pnpm --filter @ai-rag/auth start:dev
pnpm --filter @ai-rag/connectors start:dev
pnpm --filter @ai-rag/gateway start:dev
```

Public entry: `http://localhost:8080` (`GET /health`, `/api/v1/*`).

### 4. Frontend

```bash
cd apps/web && pnpm install && pnpm dev
```

Next rewrites `/api/v1/*` to the gateway (`API_PROXY_TARGET`, default `http://127.0.0.1:8080`).

## Repository layout

- `apps/gateway` — NestJS API gateway (CORS, JWT, reverse proxy)
- `apps/auth` — NestJS auth microservice (register/login/me) → DB `auth`
- `apps/connectors` — NestJS connectors microservice (Feishu bind/sync) → DB `connectors`
- `apps/api` — FastAPI RAG API (KB/docs/jobs/query + internal enqueue) → DB `rag`
- `apps/web` — Next.js UI
- `packages/rag` — Python domain library
- `packages/nest-common` — shared Nest JWT/header helpers

Databases (one Postgres, three logical DBs): `rag` (Alembic), `auth` / `connectors` (Prisma `db push`).

## M1 acceptance checklist

- [ ] `docker compose up -d postgres redis` and `uv run alembic upgrade head`
- [ ] `uv run pytest tests/ -v` passes (Postgres on `localhost:15432`)
- [ ] `uv run python -m rag.eval.run --pipeline hybrid --compare --out reports/m1.json` — metrics include `retrieval_hit_rate` and `citation_precision`; hybrid hit rate should meet or beat naive (warning only if not)
- [ ] `./scripts/smoke_m1.sh` indexes `evals/m1/corpus` and writes `reports/smoke-m1.json`
- [ ] Gateway `GET /health` returns ok/degraded with upstreams; optional authenticated `POST /api/v1/query` via gateway with `SMOKE_JWT`
- [ ] Ingest + hybrid retrieval + cited answers via API (see `tests/api/test_query_flow.py`)
