import pytest
from sqlalchemy import inspect


@pytest.mark.asyncio
async def test_tables_exist(migrated_engine):
    tables = inspect(migrated_engine).get_table_names()
    for name in ["users", "knowledge_bases", "documents", "chunks", "index_jobs"]:
        assert name in tables
