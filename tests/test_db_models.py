import pytest
from sqlalchemy import inspect


@pytest.mark.asyncio
async def test_tables_exist(migrated_engine):
    tables = inspect(migrated_engine).get_table_names()
    for name in ["knowledge_bases", "documents", "chunks", "index_jobs", "query_traces"]:
        assert name in tables
    assert "users" not in tables
    assert "connectors" not in tables
