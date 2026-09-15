import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

_REPO_ROOT = Path(__file__).resolve().parents[1]
_API_ALEMBIC = _REPO_ROOT / "apps" / "api" / "alembic.ini"


def _sync_database_url() -> str:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://rag:rag@localhost:15432/rag",
    )
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return url


@pytest.fixture(scope="session")
def migrated_engine() -> Generator[Engine, None, None]:
    url = _sync_database_url()
    cfg = Config(str(_API_ALEMBIC))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    engine = create_engine(url)
    yield engine
    engine.dispose()
