"""سجل التدقيق: طابع زمني للحدث

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-26

- `audit_logs.created_at`: وقت الحدث لعرضه في شاشة سجل التدقيق وترتيبه به.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("audit_logs", "created_at")
