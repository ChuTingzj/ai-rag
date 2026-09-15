"""drop users/connectors from rag db; drop kb.created_by FK.

Revision ID: 002_split_dbs
Revises: 001_m1_init
Create Date: 2026-09-15
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_split_dbs"
down_revision: Union[str, None] = "001_m1_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("knowledge_bases_created_by_fkey", "knowledge_bases", type_="foreignkey")
    op.drop_table("connectors")
    op.drop_table("users")


def downgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("roles", postgresql.ARRAY(sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "connectors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("kb_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", sa.Text(), nullable=True),
        sa.Column("config_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("cursor", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=True),
    )
    op.create_foreign_key(
        "knowledge_bases_created_by_fkey",
        "knowledge_bases",
        "users",
        ["created_by"],
        ["id"],
    )
