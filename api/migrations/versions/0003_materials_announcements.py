"""المواد والإعلانات: أصل الملف + مرحلة الإعلان

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-26

- `files.original_name`: اسم الملف الأصلي لعنوان التنزيل (Content-Disposition).
- `announcements.stage`: مرحلة داخل قسم عند scope=stage.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("files", sa.Column("original_name", sa.String(length=255), nullable=True))
    op.add_column("announcements", sa.Column("stage", sa.Integer(), nullable=True))
    op.create_index("ix_announcements_stage", "announcements", ["stage"])
    op.add_column(
        "notifications",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "notifications",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("notifications", "updated_at")
    op.drop_column("notifications", "created_at")
    op.drop_index("ix_announcements_stage", table_name="announcements")
    op.drop_column("announcements", "stage")
    op.drop_column("files", "original_name")
