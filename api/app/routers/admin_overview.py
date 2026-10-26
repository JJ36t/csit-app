# -*- coding: utf-8 -*-
"""لوحة الملخص — أرقام عامة للكلية أو للقسم (طلاب/حضور اليوم/الدرجات/الإعلانات).

النطاق: مدير الكلية يرى الكلية كاملة، ورئيس القسم يرى قسمه فقط:
الطلاب عبر `Student.department_id`، والجلسات/التقييمات عبر
`CourseOffering.group_id → Group.department_id`، والإعلانات الكلية + إعلانات قسمه.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_roles
from app.models import (
    Announcement,
    Assessment,
    AttendanceRecord,
    CourseOffering,
    Department,
    Group,
    LectureSession,
    Student,
    User,
)
from app.models.enums import AnnouncementScope, AttendanceStatus, UserRole
from app.services.access import staff_department_id
from app.services.sessions import baghdad_now

router = APIRouter(prefix="/admin/overview", tags=["admin-overview"])

VIEWER_ROLES = (UserRole.COLLEGE_ADMIN, UserRole.DEPARTMENT_HEAD)


def _empty() -> dict:
    """لوحة أصفار — لرئيس قسم بلا قسم مرتبط (لا نطاق له)."""
    return {
        "students": {"total": 0, "by_department": []},
        "today": {"sessions": 0, "present": 0, "late": 0, "absent": 0},
        "grades": {"published": 0, "drafts": 0},
        "announcements": {"active": 0, "scheduled": 0},
    }


def _students(db: Session, department_id) -> dict:
    """إجمالي الطلبة (مستخدمو دور الطالب غير المحذوفين) وتوزيعهم على الأقسام."""
    counted = {
        dept_id: count
        for dept_id, count in db.execute(
            select(Student.department_id, func.count())
            .join(User, User.id == Student.user_id)
            .where(
                User.role == UserRole.STUDENT,
                User.deleted_at.is_(None),
                Student.deleted_at.is_(None),
            )
            .group_by(Student.department_id)
        ).all()
    }

    total_stmt = select(func.count()).select_from(User).where(
        User.role == UserRole.STUDENT,
        User.deleted_at.is_(None),
    )
    if department_id is not None:
        total_stmt = total_stmt.where(
            User.id.in_(
                select(Student.user_id).where(
                    Student.department_id == department_id,
                    Student.deleted_at.is_(None),
                )
            )
        )
    total = db.scalar(total_stmt) or 0

    departments_stmt = (
        select(Department)
        .where(Department.deleted_at.is_(None))
        .order_by(Department.name_ar)
    )
    if department_id is not None:
        departments_stmt = departments_stmt.where(Department.id == department_id)

    return {
        "total": total,
        "by_department": [
            {
                "code": department.code,
                "name_ar": department.name_ar,
                "count": counted.get(department.id, 0),
            }
            for department in db.scalars(departments_stmt)
        ],
    }


def _today_session_ids(db: Session, department_id):
    """جلسات اليوم (بتوقيت بغداد) ضمن النطاق — تُستخدم للعدّ والعدّ الجزئي."""
    stmt = (
        select(LectureSession.id)
        .join(CourseOffering, CourseOffering.id == LectureSession.offering_id)
        .join(Group, Group.id == CourseOffering.group_id)
        .where(LectureSession.date == baghdad_now().date())
    )
    if department_id is not None:
        stmt = stmt.where(Group.department_id == department_id)
    return stmt


def _today(db: Session, department_id) -> dict:
    session_ids = _today_session_ids(db, department_id)
    sessions = db.scalar(select(func.count()).select_from(session_ids.subquery())) or 0

    counts = {
        status: count
        for status, count in db.execute(
            select(AttendanceRecord.status, func.count())
            .where(AttendanceRecord.session_id.in_(session_ids))
            .group_by(AttendanceRecord.status)
        ).all()
    }

    def of(status: AttendanceStatus) -> int:
        return int(counts.get(status, 0))

    return {
        "sessions": int(sessions),
        "present": of(AttendanceStatus.PRESENT),
        "late": of(AttendanceStatus.LATE),
        "absent": of(AttendanceStatus.ABSENT),
    }


def _grades(db: Session, department_id) -> dict:
    stmt = (
        select(Assessment.is_published, func.count())
        .join(CourseOffering, CourseOffering.id == Assessment.offering_id)
        .join(Group, Group.id == CourseOffering.group_id)
        .where(Assessment.deleted_at.is_(None))
        .group_by(Assessment.is_published)
    )
    if department_id is not None:
        stmt = stmt.where(Group.department_id == department_id)

    published = 0
    drafts = 0
    for is_published, count in db.execute(stmt).all():
        if is_published:
            published += int(count)
        else:
            drafts += int(count)
    return {"published": published, "drafts": drafts}


def _announcements(db: Session, department_id) -> dict:
    """نشطة = نُشرت ولم تنته، مجدولة = `publish_at` مستقبلي.

    مدير الكلية: الكل. رئيس القسم: إعلانات الكلية + إعلانات قسمه.
    """
    now = datetime.now(timezone.utc)
    scoped = [Announcement.deleted_at.is_(None)]
    if department_id is not None:
        scoped.append(
            or_(
                Announcement.scope == AnnouncementScope.COLLEGE,
                and_(
                    Announcement.scope == AnnouncementScope.DEPARTMENT,
                    Announcement.scope_id == department_id,
                ),
            )
        )

    def count(*extra) -> int:
        return int(
            db.scalar(select(func.count()).select_from(Announcement).where(*scoped, *extra))
            or 0
        )

    return {
        "active": count(
            or_(Announcement.publish_at.is_(None), Announcement.publish_at <= now),
            or_(Announcement.expires_at.is_(None), Announcement.expires_at > now),
        ),
        "scheduled": count(Announcement.publish_at > now),
    }


@router.get("")
def overview(
    user: User = Depends(require_roles(*VIEWER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    is_college_wide = user.role == UserRole.COLLEGE_ADMIN
    department_id = None if is_college_wide else staff_department_id(db, user)
    if not is_college_wide and department_id is None:
        return _empty()

    return {
        "students": _students(db, department_id),
        "today": _today(db, department_id),
        "grades": _grades(db, department_id),
        "announcements": _announcements(db, department_id),
    }
