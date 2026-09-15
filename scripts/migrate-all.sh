#!/usr/bin/env bash
# Apply each service's own DDL migrations.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> rag (Alembic @ apps/api)"
uv run alembic -c apps/api/alembic.ini upgrade head

echo "==> auth (Prisma @ apps/auth)"
pnpm --filter @ai-rag/auth prisma:generate
pnpm --filter @ai-rag/auth db:migrate

echo "==> connectors (Prisma @ apps/connectors)"
pnpm --filter @ai-rag/connectors prisma:generate
pnpm --filter @ai-rag/connectors db:migrate

echo "All service migrations applied."
