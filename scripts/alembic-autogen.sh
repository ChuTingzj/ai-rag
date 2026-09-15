#!/usr/bin/env bash
# Thin wrapper — prefer: uv run rag-db-revision -- "<msg>"
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
exec uv run rag-db-revision -- "${1:-auto}"
