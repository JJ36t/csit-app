# -*- coding: utf-8 -*-
"""مجموعة المحتوى والدرجات: files, materials, assessments, grades.

الدرجات وأعمال السنة ضمن الإطلاق الأول (قرار مستخدم رقم 3).
"""
import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import SAEnum, AssessmentKind, MaterialKind


class StoredFile(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """ملف مُخزَّن (PDF محاضرات، مرفقات أعذار…)."""

    __tablename__ = "files"

    storage_key: Mapped[str] = mapped_column(String(255), unique=True)
    original_name: Mapped[str | None] = mapped_column(String(255))
    mime: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str | None] = mapped_column(String(64))
    uploader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)


class Material(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """محتوى مادة: PDF أو رابط فيديو أو رابط — مرتبط بأسبوع دراسي."""

    __tablename__ = "materials"

    offering_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("course_offerings.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    kind: Mapped[MaterialKind] = mapped_column(SAEnum(MaterialKind))
    file_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("files.id"))
    url: Mapped[str | None] = mapped_column(String(500))
    week_no: Mapped[int | None] = mapped_column(Integer)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    # التحقق من أن (file_id أو url) موجوداً يُطبَّق في طبقة الخدمة


class Assessment(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """تقييم: كوز / مختبر / نصفي / نهائي — بوزن ودرجة عظمى."""

    __tablename__ = "assessments"

    offering_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("course_offerings.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[AssessmentKind] = mapped_column(SAEnum(AssessmentKind))
    max_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("100"))
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    # النشر موافقة الكلية بعد إدخال التدريسي — كما في مصفوفة الصلاحيات
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)


class Grade(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """درجة طالب في تقييم — قيد فريد (تقييم، طالب) كما في الخطة."""

    __tablename__ = "grades"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id"), index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.user_id"), index=True
    )
    score: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    entered_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    __table_args__ = (
        UniqueConstraint("assessment_id", "student_id", name="uq_grade_once"),
    )
