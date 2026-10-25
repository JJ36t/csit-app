# -*- coding: utf-8 -*-
"""مجموعة الجدول الزمني: rooms, timetable_slots, timetable_changes, lecture_sessions."""
import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    SAEnum,
    LectureSessionStatus,
    SessionKind,
    TimetableChangeType,
)


class Room(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """قاعة أو مختبر بإحداثيات ونطاق للتحقق من الموقع عند الحضور."""

    __tablename__ = "rooms"

    name: Mapped[str] = mapped_column(String(100))
    building: Mapped[str | None] = mapped_column(String(100))
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    radius_m: Mapped[int | None] = mapped_column(Integer)


class TimetableSlot(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """حصة أسبوعية ثابتة — weekday: 0=الأحد … 6=السبت، والتخزين UTC والعرض بتوقيت بغداد."""

    __tablename__ = "timetable_slots"

    offering_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("course_offerings.id"), index=True
    )
    weekday: Mapped[int] = mapped_column(Integer, index=True)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    room_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("rooms.id"), index=True)
    kind: Mapped[SessionKind] = mapped_column(SAEnum(SessionKind))

    __table_args__ = (
        # فهرس الجدول كما في الخطة (القسم 8)
        Index("ix_timetable_slots_offering_weekday", "offering_id", "weekday"),
    )


class TimetableChange(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """تغيير مؤرخ ليوم واحد: إلغاء/نقل/حصة إضافية."""

    __tablename__ = "timetable_changes"

    slot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("timetable_slots.id"), index=True
    )
    date: Mapped[date] = mapped_column(Date, index=True)
    type: Mapped[TimetableChangeType] = mapped_column(SAEnum(TimetableChangeType))
    new_start: Mapped[time | None] = mapped_column(Time)
    new_room_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("rooms.id"))
    reason: Mapped[str | None] = mapped_column(String(300))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))


class LectureSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """جلسة محاضرة لكل أسبوع — قلب نظام الحضور.

    secret: سر HMAC الذي يتولد منه رمز QR المتجدد كل 20 ثانية.
    window_s: نافذة السماح بالمسح (ثوانٍ).
    """

    __tablename__ = "lecture_sessions"

    offering_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("course_offerings.id"), index=True
    )
    slot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("timetable_slots.id"), index=True
    )
    date: Mapped[date] = mapped_column(Date, index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[LectureSessionStatus] = mapped_column(
        SAEnum(LectureSessionStatus),
        default=LectureSessionStatus.SCHEDULED,
        index=True,
    )
    opened_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    secret: Mapped[str | None] = mapped_column(String(128))
    window_s: Mapped[int] = mapped_column(Integer, default=300)
