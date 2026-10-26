"""سجل التدقيق: طابع زمني للحدث

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-26

- `audit_logs.created_at`: وقت الحدث لعرضه في شاشة سجل التدقيق وترتيبه به.

ملاحظة SQLite: لا يسمح بإضافة عمود `NOT NULL` بقيمة افتراضية غير ثابتة
(`CURRENT_TIMESTAMP`) إلى جدول فيه صفوف، لذلك نستخدم وضع batch (إعادة بناء الجدول)
على SQLite فقط، ونُبقي ALTER المباشر على PostgreSQL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_sqlite() -> bool:
    return op.get_bind().dialect.name == "sqlite"


def upgrade() -> None:
    column = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    if _is_sqlite():
        # إعادة بناء الجدول تتيح القيمة الافتراضية حتى مع وجود صفوف سابقة
        with op.batch_alter_table("audit_logs", recreate="always") as batch:
            batch.add_column(column)
    else:
        op.add_column("audit_logs", column)


def downgrade() -> None:
    if _is_sqlite():
        with op.batch_alter_table("audit_logs", recreate="always") as batch:
            batch.drop_column("created_at")
    else:
        op.drop_column("audit_logs", "created_at")
