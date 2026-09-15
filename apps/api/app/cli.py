"""CLI entrypoints for the RAG API service (wired via [project.scripts])."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ALEMBIC_INI = _REPO_ROOT / "apps" / "api" / "alembic.ini"


def _ensure_pythonpath() -> None:
    api_root = str(_REPO_ROOT / "apps" / "api")
    rag_pkg = str(_REPO_ROOT / "packages" / "rag")
    parts = [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]
    for path in (api_root, rag_pkg):
        if path not in parts:
            parts.insert(0, path)
    os.environ["PYTHONPATH"] = os.pathsep.join(parts)


def db_upgrade() -> None:
    """Apply Alembic migrations for DB `rag`."""
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "alembic", "-c", str(_ALEMBIC_INI), "upgrade", "head"],
            cwd=_REPO_ROOT,
        )
    )


def db_revision() -> None:
    """Autogenerate an Alembic revision from SQLAlchemy models."""
    parser = argparse.ArgumentParser(description="Autogenerate RAG Alembic revision")
    parser.add_argument(
        "message",
        nargs="?",
        default="auto",
        help="Revision message (default: auto)",
    )
    args = parser.parse_args()
    raise SystemExit(
        subprocess.call(
            [
                sys.executable,
                "-m",
                "alembic",
                "-c",
                str(_ALEMBIC_INI),
                "revision",
                "--autogenerate",
                "-m",
                args.message,
            ],
            cwd=_REPO_ROOT,
        )
    )


def db_current() -> None:
    """Show current Alembic revision for DB `rag`."""
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "alembic", "-c", str(_ALEMBIC_INI), "current"],
            cwd=_REPO_ROOT,
        )
    )


def serve() -> None:
    """Run the RAG FastAPI app (reload)."""
    _ensure_pythonpath()
    raise SystemExit(
        subprocess.call(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "apps.api.app.main:app",
                "--reload",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ],
            cwd=_REPO_ROOT,
        )
    )


def worker() -> None:
    """Run the RAG arq worker."""
    _ensure_pythonpath()
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "arq", "app.workers.tasks.WorkerSettings"],
            cwd=_REPO_ROOT / "apps" / "api",
        )
    )
