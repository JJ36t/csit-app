# -*- coding: utf-8 -*-
"""مجموعة الحضور والأعذار: attendance_records, absence_excuses."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    SAEnum,
    AttendanceMethod,
    AttendanceStatus,
    ExcuseStatus,
)


class AttendanceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """سجل حضور طالب في جلسة — قيد فريد يمنع تسجيل الحضور مرتين (كما في الخطة)."""

    __tablename__ = "attendance_records"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lecture_sessions.id"), index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.user_id"), index=True
    )
    status: Mapped[AttendanceStatus] = mapped_column(SAEnum(AttendanceStatus))
    method: Mapped[AttendanceMethod] = mapped_column(SAEnum(AttendanceMethod))
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    device_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("devices.id"))
    # الموقع يُرسل لحظة المسح فقط ولا يُخزَّن دائماً (الخصوصية)
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    accuracy: Mapped[float | None] = mapped_column(Float)
    # الحضور «المريب» يُعلَّم للمراجعة بدل الرفض الفوري
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_reason: Mapped[str | None] = mapped_column(String(200))
    marked_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_attendance_once"),
    )


class AbsenceExcuse(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """عذر غياب مرفوع لجلسة، يراجعه التدريسي أو القسم."""

    __tablename__ = "absence_excuses"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.user_id"), index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lecture_sessions.id"), index=True
    )
    reason: Mapped[str] = mapped_column(Text)
    attachment_file_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("files.id"))
    status: Mapped[ExcuseStatus] = mapped_column(
        SAEnum(ExcuseStatus), default=ExcuseStatus.PENDING
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
