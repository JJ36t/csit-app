# -*- coding: utf-8 -*-
"""مجموعة الهوية والأجهزة: users, students, staff, devices, refresh_tokens, fcm_tokens."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    SAEnum,
    DeviceStatus,
    StudyType,
    StudentStatus,
    UserRole,
    UserStatus,
)


class User(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    university_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    full_name_ar: Mapped[str] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255))
    status: Mapped[UserStatus] = mapped_column(SAEnum(UserStatus), default=UserStatus.PENDING)
    # التغيير الإجباري لأول كلمة مرور يُضبط عند استيراد الطلاب
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Student(TimestampMixin, SoftDeleteMixin, Base):
    """طالب — علاقة 1:1 مع users (المفتاح الأساسي هو user_id نفسه)."""

    __tablename__ = "students"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id"), index=True)
    stage: Mapped[int] = mapped_column(Integer)
    study_type: Mapped[StudyType] = mapped_column(SAEnum(StudyType))
    group_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("groups.id"), index=True)
    enrollment_year: Mapped[int] = mapped_column(Integer)
    status: Mapped[StudentStatus] = mapped_column(SAEnum(StudentStatus), default=StudentStatus.ACTIVE)


class Staff(TimestampMixin, SoftDeleteMixin, Base):
    """تدريسي/رئيس قسم/إدارة — علاقة 1:1 مع users."""

    __tablename__ = "staff"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("departments.id"), index=True)
    academic_title: Mapped[str | None] = mapped_column(String(100))
    office: Mapped[str | None] = mapped_column(String(100))


class Device(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """جهاز مرتبط بمستخدم (ربط الجهاز device binding).

    ملاحظة: «جهاز نشط واحد لكل طالب» تُطبَّق حالياً في طبقة الخدمة،
    ويُضاف فهرس فريد جزئي (partial unique index) على PostgreSQL عند النشر.
    """

    __tablename__ = "devices"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    device_fingerprint: Mapped[str] = mapped_column(String(255), unique=True)
    model: Mapped[str | None] = mapped_column(String(120))
    bound_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[DeviceStatus] = mapped_column(SAEnum(DeviceStatus), default=DeviceStatus.PENDING)

    __table_args__ = (
        # جهاز نشط واحد لكل مستخدم — مفروض على مستوى قاعدة البيانات (ترحيل 0002)
        Index(
            "uq_devices_one_active_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
    )


class RefreshToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    device_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("devices.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FcmToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fcm_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    device_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("devices.id"), index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
