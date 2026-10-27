# -*- coding: utf-8 -*-
"""مجموعة التواصل والتدقيق: announcements, announcement_reads, notifications, requests, request_messages, audit_logs."""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    SAEnum,
    AnnouncementPriority,
    AnnouncementScope,
    RequestStatus,
)


class Announcement(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """إعلان موجّه: كلية / قسم / مرحلة / شعبة / مادة — scope_id معرف الجهة المستهدفة."""

    __tablename__ = "announcements"

    scope: Mapped[AnnouncementScope] = mapped_column(SAEnum(AnnouncementScope), index=True)
    scope_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    # لمرحلة محددة داخل قسم (scope=stage): رقم المرحلة مع scope_id = القسم
    stage: Mapped[int | None] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    priority: Mapped[AnnouncementPriority] = mapped_column(
        SAEnum(AnnouncementPriority), default=AnnouncementPriority.NORMAL
    )
    pinned: Mapped[bool] = mapped_column(default=False)
    publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))


class AnnouncementRead(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "announcement_reads"

    announcement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("announcements.id"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("announcement_id", "user_id", name="uq_announcement_read_once"),
    )


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """إشعار داخل التطبيق مرصود في الجدول (in-box) بحسب الخطة (القسم 13)."""

    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    data: Mapped[Any] = mapped_column(JSON, nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class Request(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """طلب أو شكوى طالب موجهة لقسمه (مرحلة التوسعة V2 في الخطة)."""

    __tablename__ = "requests"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.user_id"), index=True
    )
    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id"), index=True)
    category: Mapped[str] = mapped_column(String(50))
    subject: Mapped[str] = mapped_column(String(300))
    status: Mapped[RequestStatus] = mapped_column(
        SAEnum(RequestStatus), default=RequestStatus.OPEN, index=True
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class RequestMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "request_messages"

    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("requests.id"), index=True)
    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    file_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("files.id"))


class PushOutbox(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """طابور إرسال إشعارات FCM — يُكتب في معاملة الإشعار نفسها ثم يُرسَل في الخلفية.

    الفصل بين الكتابة والإرسال يمنع ضياع الإشعار عند تعطّل الشبكة،
    ويضمن أن إعادة المحاولة لا تُنشئ إشعاراً مكرراً في صندوق الوارد.
    الحالة: pending | sent | failed | skipped (انظر app/services/push.py).
    """

    __tablename__ = "push_outbox"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    data: Mapped[Any] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_error: Mapped[str | None] = mapped_column(String(300))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        # فهرس المرسل: يبحث دائماً عن (pending, next_attempt_at <= now)
        Index("ix_push_outbox_dispatch", "status", "next_attempt_at"),
    )


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """سجل التدقيق: من فعل ماذا ومتى — قبل/بعد — إلزامي لتعديلات الحضور والدرجات."""

    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[str] = mapped_column(String(64))
    before: Mapped[Any] = mapped_column(JSON, nullable=True)
    after: Mapped[Any] = mapped_column(JSON, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45))
    # وقت الحدث — يُملأ من الخادم؛ ترتيب السجل وعرضه يعتمدان عليه
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
