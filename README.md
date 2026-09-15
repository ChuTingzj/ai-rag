# AI RAG — M1 Hybrid RAG Platform

Enterprise knowledge assistant: NestJS gateway + Auth/Connectors microservices, FastAPI RAG API, PostgreSQL (pgvector), Redis, and Next.js UI. See [TECH_DESIGN.md](./TECH_DESIGN.md) and [PRD.md](./PRD.md).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python 3.12+)
- [Docker](https://www.docker.com/) (Compose v2)
- [pnpm](https://pnpm.io/) 9.x (Nest gateway/services + web)

## Quick start

### 1. Infrastructure + migrations

```bash
cp .env.example .env
# Edit .env with secrets (OPENROUTER_API_KEY, JWT_SECRET, INTERNAL_SERVICE_TOKEN, etc.)
./scripts/link-env.sh   # apps/*/.env → ../../.env (idempotent)

docker compose up -d postgres redis
# Logical DBs auth/connectors are created by docker/postgres/init-databases.sql on first volume init

pnpm install
pnpm db:migrate   # Turborepo: prisma generate → migrate deploy (auth + connectors)
uv run alembic -c apps/api/alembic.ini upgrade head
```

| Service | Generate | Apply | Location |
| --- | --- | --- | --- |
| `apps/api` (rag) | `alembic revision --autogenerate` | `alembic upgrade head` | [`apps/api/migrations/`](apps/api/migrations/) |
| `apps/auth` | `prisma migrate diff` | `turbo run db:migrate --filter=@ai-rag/auth` | [`apps/auth/prisma/`](apps/auth/prisma/) |
| `apps/connectors` | `prisma migrate diff` | `turbo run db:migrate --filter=@ai-rag/connectors` | [`apps/connectors/prisma/`](apps/connectors/prisma/) |

### 2. Python (uv workspace)

```bash
uv sync --all-groups
uv run alembic -c apps/api/alembic.ini upgrade head
uv run pytest tests/ -v
```

Start the RAG API (behind the gateway in production):

```bash
uv run uvicorn apps.api.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. NestJS gateway + microservices (Turborepo)

```bash
pnpm install
pnpm build:nest   # builds nest-common + gateway + auth + connectors (auth/connectors migrate first)
```

Dev (`start:dev` depends on `db:migrate` via Turbo; env from root `.env` via symlink):

```bash
pnpm dev:auth
pnpm dev:connectors
pnpm dev:gateway
```

Public entry: `http://localhost:8080` (`GET /health`, `/api/v1/*`).

### 4. Frontend

```bash
cd apps/web && pnpm install && pnpm dev
```

Next rewrites `/api/v1/*` to the gateway (`API_PROXY_TARGET`, default `http://127.0.0.1:8080`).

## Repository layout

- `apps/gateway` — NestJS API gateway (CORS, JWT, reverse proxy) — no DB
- `apps/auth` — NestJS auth + Prisma migrations → DB `auth`
- `apps/connectors` — NestJS connectors + Prisma migrations → DB `connectors`
- `apps/api` — FastAPI RAG + Alembic migrations → DB `rag`
- `apps/web` — Next.js UI
- `packages/rag` — Python domain library
- `packages/nest-common` — shared Nest JWT/header helpers

## M1 acceptance checklist

- [ ] `docker compose up -d postgres redis`, then `pnpm db:migrate` and `uv run alembic -c apps/api/alembic.ini upgrade head`
- [ ] `uv run pytest tests/ -v` passes (Postgres on `localhost:15432`)
- [ ] `uv run python -m rag.eval.run --pipeline hybrid --compare --out reports/m1.json` — metrics include `retrieval_hit_rate` and `citation_precision`; hybrid hit rate should meet or beat naive (warning only if not)
- [ ] `./scripts/smoke_m1.sh` indexes `evals/m1/corpus` and writes `reports/smoke-m1.json`
- [ ] Gateway `GET /health` returns ok/degraded with upstreams; optional authenticated `POST /api/v1/query` via gateway with `SMOKE_JWT`
- [ ] Ingest + hybrid retrieval + cited answers via API (see `tests/api/test_query_flow.py`)
