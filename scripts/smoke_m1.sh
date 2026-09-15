#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://rag:rag@localhost:15432/rag}"
export EMBEDDING_PROVIDER="${EMBEDDING_PROVIDER:-hash_stub}"
export EMBEDDING_DIM="${EMBEDDING_DIM:-1024}"
export RERANK_PROVIDER="${RERANK_PROVIDER:-stub}"

echo "==> Starting postgres + redis"
docker compose up -d postgres redis

echo "==> Waiting for postgres"
for _ in $(seq 1 30); do
  if docker compose exec -T postgres pg_isready -U rag -d rag >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "==> Running migrations"
uv run alembic upgrade head

echo "==> Indexing M1 eval corpus"
uv run python -m rag.eval.run --pipeline hybrid --compare --out reports/smoke-m1.json

echo "==> Health check (gateway preferred on :8080; RAG API on :8000)"
if curl -sf "http://localhost:8080/health" >/dev/null; then
  echo "Gateway health OK"
  if [[ -n "${SMOKE_JWT:-}" ]]; then
    curl -sf -X POST "http://localhost:8080/api/v1/query" \
      -H "Authorization: Bearer ${SMOKE_JWT}" \
      -H "Content-Type: application/json" \
      -d '{"question":"What is TOKEN_EXPENSE_3000?","kb_ids":[]}' \
      | head -c 200 || true
    echo
  else
    echo "Set SMOKE_JWT to exercise /api/v1/query via gateway"
  fi
elif curl -sf "http://localhost:8000/health" >/dev/null; then
  echo "RAG API health OK (direct; prefer gateway in normal setups)"
else
  echo "Skip query smoke (start gateway + services, or: uv run uvicorn apps.api.app.main:app --port 8000)"
fi

echo "==> Smoke complete"
