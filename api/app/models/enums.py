# -*- coding: utf-8 -*-
"""القوائم المعرِّفة (Enums) بحسب الخطة والأدوار المحددة فيها."""
import enum

from sqlalchemy import Enum as _SAEnum


def SAEnum(enum_cls: type[enum.Enum]) -> _SAEnum:
    """Store the lowercase text values (student, qr, present, ...) as in the plan,
    not the uppercase member names (STUDENT, ...)."""
    return _SAEnum(enum_cls, values_callable=lambda e: [m.value for m in e])


class UserRole(str, enum.Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    DEPARTMENT_HEAD = "department_head"
    COLLEGE_ADMIN = "college_admin"


class UserStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"


class DeviceStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"


class StudyType(str, enum.Enum):
    """نوع الدراسة: صباحي / مسائي (قرار مستخدم رقم 5)."""

    MORNING = "morning"
    EVENING = "evening"


class StudentStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    GRADUATED = "graduated"


class EnrollmentSource(str, enum.Enum):
    AUTO = "auto"
    MANUAL = "manual"


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "active"
    DROPPED = "dropped"
    COMPLETED = "completed"


class SessionKind(str, enum.Enum):
    """نوع الحصة/المادة: نظري أو مختبر."""

    THEORY = "theory"
    LAB = "lab"


class TimetableChangeType(str, enum.Enum):
    CANCEL = "cancel"
    MOVE = "move"
    EXTRA = "extra"


class LectureSessionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class AttendanceStatus(str, enum.Enum):
    """حاضر / متأخر / غائب / غائب بعذر — قواعد التأخير تُضبط لاحقاً (قرار رقم 4)."""

    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"
    EXCUSED = "excused"


class AttendanceMethod(str, enum.Enum):
    QR = "qr"
    CODE = "code"
    ID_SCAN = "id_scan"
    MANUAL = "manual"


class ExcuseStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MaterialKind(str, enum.Enum):
    PDF = "pdf"
    VIDEO_LINK = "video_link"
    LINK = "link"


class AssessmentKind(str, enum.Enum):
    QUIZ = "quiz"
    LAB = "lab"
    MIDTERM = "midterm"
    FINAL = "final"
    OTHER = "other"


class AnnouncementScope(str, enum.Enum):
    COLLEGE = "college"
    DEPARTMENT = "department"
    STAGE = "stage"
    GROUP = "group"
    OFFERING = "offering"


class AnnouncementPriority(str, enum.Enum):
    NORMAL = "normal"
    HIGH = "high"


class RequestStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
