"""إشعارات الدفع (طابور) + المصادقة الثنائية + مراجعة الأعذار

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-27

- `push_outbox`: طابور إرسال FCM يُكتب في معاملة الإشعار نفسها ثم يُرسَل من
  مهمة خلفية، فلا يضيع إشعار عند تعطّل الشبكة ولا يتكرر في صندوق الوارد.
- `users.totp_*`: المصادقة الثنائية (TOTP) للتدريسي والإدارة.
- `absence_excuses.reviewed_at/review_note`: قرار المراجعة وسببه يظهران للطالب.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- المصادقة الثنائية ---
    op.add_column("users", sa.Column("totp_secret", sa.String(length=64), nullable=True))
    op.add_column(
        "users",
        sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users", sa.Column("totp_confirmed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("users", sa.Column("totp_last_step", sa.Integer(), nullable=True))

    # --- مراجعة الأعذار ---
    op.add_column(
        "absence_excuses", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("absence_excuses", sa.Column("review_note", sa.String(length=500), nullable=True))

    # --- طابور إرسال الإشعارات ---
    op.create_table(
        "push_outbox",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_error", sa.String(length=300), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_push_outbox_user_id", "push_outbox", ["user_id"], unique=False)
    op.create_index("ix_push_outbox_status", "push_outbox", ["status"], unique=False)
    op.create_index(
        "ix_push_outbox_next_attempt_at", "push_outbox", ["next_attempt_at"], unique=False
    )
    op.create_index(
        "ix_push_outbox_dispatch", "push_outbox", ["status", "next_attempt_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_push_outbox_dispatch", table_name="push_outbox")
    op.drop_index("ix_push_outbox_next_attempt_at", table_name="push_outbox")
    op.drop_index("ix_push_outbox_status", table_name="push_outbox")
    op.drop_index("ix_push_outbox_user_id", table_name="push_outbox")
    op.drop_table("push_outbox")

    op.drop_column("absence_excuses", "review_note")
    op.drop_column("absence_excuses", "reviewed_at")

    op.drop_column("users", "totp_last_step")
    op.drop_column("users", "totp_confirmed_at")
    op.drop_column("users", "totp_enabled")
    op.drop_column("users", "totp_secret")
