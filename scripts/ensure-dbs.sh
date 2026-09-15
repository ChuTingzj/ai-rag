#!/usr/bin/env bash
# Create auth/connectors databases on an already-initialized Postgres volume.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

create_db_if_missing() {
  local name="$1"
  exists="$(docker compose exec -T postgres psql -U rag -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname='${name}'" | tr -d '[:space:]')"
  if [[ "${exists}" == "1" ]]; then
    echo "database ${name} already exists"
  else
    docker compose exec -T postgres psql -U rag -d postgres -c "CREATE DATABASE ${name}"
    echo "created database ${name}"
  fi
}

create_db_if_missing auth
create_db_if_missing connectors
echo "Databases ready: rag (default), auth, connectors"
