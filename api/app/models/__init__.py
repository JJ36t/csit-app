# -*- coding: utf-8 -*-
"""يجمع كل النماذج حتى ترى قاعدة البيانات (وAlembic) الجداول الـ29 كاملة."""
from app.models.academic import (
    AcademicYear,
    Course,
    CourseOffering,
    Department,
    Enrollment,
    Group,
    Term,
)
from app.models.attendance import AbsenceExcuse, AttendanceRecord
from app.models.base import Base
from app.models.comms import (
    Announcement,
    AnnouncementRead,
    AuditLog,
    Notification,
    Request,
    RequestMessage,
)
from app.models.content import Assessment, Grade, Material, StoredFile
from app.models.identity import Device, FcmToken, RefreshToken, Staff, Student, User
from app.models.timetable import (
    LectureSession,
    Room,
    TimetableChange,
    TimetableSlot,
)

__all__ = [
    "Base",
    # الهوية والأجهزة
    "User",
    "Student",
    "Staff",
    "Device",
    "RefreshToken",
    "FcmToken",
    # الأكاديمي
    "Department",
    "AcademicYear",
    "Term",
    "Group",
    "Course",
    "CourseOffering",
    "Enrollment",
    # الجدول الزمني
    "Room",
    "TimetableSlot",
    "TimetableChange",
    "LectureSession",
    # الحضور
    "AttendanceRecord",
    "AbsenceExcuse",
    # المحتوى والدرجات
    "StoredFile",
    "Material",
    "Assessment",
    "Grade",
    # التواصل والتدقيق
    "Announcement",
    "AnnouncementRead",
    "Notification",
    "Request",
    "RequestMessage",
    "AuditLog",
]
