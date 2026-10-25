# -*- coding: utf-8 -*-
"""أساسيات النماذج: مفتاح UUID، طوابع زمنية (UTC)، وحذف ناعم — كما في الخطة (القسم 8)."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """حذف ناعم: لا تُحذف السجلات نهائياً بل تُعلَّم بـ deleted_at.

    السجلات التبادلية (الحضور، الدرجات، سجل التدقيق…) لا تُمزج بهذا الخليط
    لأنها append-only بحسب التصميم.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
