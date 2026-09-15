#!/usr/bin/env bash
# Recreate .env symlinks from the monorepo root into Nest/Next/Python packages.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env — copy from example first:"
  echo "  cp .env.example .env"
  exit 1
fi

link_one() {
  local target="$1"
  mkdir -p "$(dirname "$target")"
  ln -sfn ../../.env "$target"
  echo "linked $target -> ../../.env"
}

# apps/* are two levels deep
link_one apps/api/.env
link_one apps/auth/.env
link_one apps/connectors/.env
link_one apps/gateway/.env
link_one apps/web/.env
link_one packages/rag/.env

echo "Done. Root of truth: $ROOT/.env"
