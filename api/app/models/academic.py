# -*- coding: utf-8 -*-
"""المجموعة الأكاديمية: departments, academic_years, terms, groups, courses, course_offerings, enrollments."""
import uuid
from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    SAEnum,
    EnrollmentSource,
    EnrollmentStatus,
    SessionKind,
    StudyType,
)


class Department(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """الأقسام الأربعة: علوم الحاسوب، نظم المعلومات، الأنظمة الطبية، الأمن السيبراني."""

    __tablename__ = "departments"

    code: Mapped[str] = mapped_column(String(10), unique=True)
    name_ar: Mapped[str] = mapped_column(String(200))
    name_en: Mapped[str] = mapped_column(String(200))


class AcademicYear(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "academic_years"

    label: Mapped[str] = mapped_column(String(20), unique=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)


class Term(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "terms"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(50))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)


class Group(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """شعبة دراسية (صباحية/مسائية) ضمن قسم ومرحلة وفصل."""

    __tablename__ = "groups"

    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id"), index=True)
    stage: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(50))
    study_type: Mapped[StudyType] = mapped_column(SAEnum(StudyType))
    term_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("terms.id"), index=True)

    __table_args__ = (
        UniqueConstraint(
            "department_id", "stage", "name", "study_type", "term_id",
            name="uq_group_identity",
        ),
    )


class Course(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """مادة مجردة تُدرَّس في قسم لمرحلة ما."""

    __tablename__ = "courses"

    code: Mapped[str] = mapped_column(String(20), unique=True)
    name_ar: Mapped[str] = mapped_column(String(200))
    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id"), index=True)
    stage: Mapped[int] = mapped_column(Integer)
    units: Mapped[int] = mapped_column(Integer)
    kind: Mapped[SessionKind] = mapped_column(SAEnum(SessionKind))


class CourseOffering(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """المحور: ربط المادة بالشعبة والتدريسي والفصل (course offering)."""

    __tablename__ = "course_offerings"

    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"), index=True)
    term_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("terms.id"), index=True)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("groups.id"), index=True)
    instructor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("staff.user_id"), index=True
    )
    session_kind: Mapped[SessionKind] = mapped_column(SAEnum(SessionKind))

    __table_args__ = (
        UniqueConstraint(
            "course_id", "term_id", "group_id", "session_kind",
            name="uq_offering_identity",
        ),
    )


class Enrollment(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """تسجيل طالب في offering — منه تُحلّ حالة الطالب في كل شاشة."""

    __tablename__ = "enrollments"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.user_id"), index=True
    )
    offering_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("course_offerings.id"), index=True)
    source: Mapped[EnrollmentSource] = mapped_column(
        SAEnum(EnrollmentSource), default=EnrollmentSource.AUTO
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        SAEnum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE
    )

    __table_args__ = (
        UniqueConstraint("student_id", "offering_id", name="uq_enrollment_once"),
    )
