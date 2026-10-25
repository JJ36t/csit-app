"""فهرس فريد جزئي: جهاز نشط واحد لكل مستخدم (PostgreSQL وSQLite)

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-25

يثبّت قاعدة «جهاز نشط واحد لكل طالب» على مستوى قاعدة البيانات
بدل الاعتماد على طبقة الخدمة وحدها (القسم 11 من الخطة).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "uq_devices_one_active_per_user"


def upgrade() -> None:
    op.create_index(
        INDEX_NAME,
        "devices",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="devices")
