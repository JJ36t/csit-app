# -*- coding: utf-8 -*-
"""الإشعارات: جمهور الإعلانات والمواد، وإنشاء إشعارات صندوق الوارد دفعة واحدة."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Announcement,
    CourseOffering,
    Enrollment,
    Notification,
    Staff,
    Student,
    User,
)
from app.models.enums import (
    AnnouncementScope,
    EnrollmentStatus,
    UserRole,
    UserStatus,
)


def offering_student_ids(db: Session, offering_id: uuid.UUID) -> list[uuid.UUID]:
    return list(
        db.scalars(
            select(Enrollment.student_id).where(
                Enrollment.offering_id == offering_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
    )


def _active_user_ids(db: Session, condition) -> list[uuid.UUID]:
    return list(
        db.scalars(
            select(User.id).where(User.status == UserStatus.ACTIVE, condition)
        )
    )


def announcement_audience(db: Session, announcement: Announcement) -> list[uuid.UUID]:
    """معرّفات المستخدمين المستهدفين بالإعلان (بلا المُنشئ)."""
    scope = announcement.scope
    scope_id = announcement.scope_id

    if scope == AnnouncementScope.COLLEGE:
        ids = _active_user_ids(db, User.deleted_at.is_(None))
    elif scope == AnnouncementScope.DEPARTMENT:
        students = _active_user_ids(
            db, User.id.in_(select(Student.user_id).where(Student.department_id == scope_id))
        )
        staff_dept = _active_user_ids(
            db, User.id.in_(select(Staff.user_id).where(Staff.department_id == scope_id))
        )
        ids = students + staff_dept
    elif scope == AnnouncementScope.STAGE:
        ids = _active_user_ids(
            db,
            User.id.in_(
                select(Student.user_id).where(
                    Student.department_id == scope_id,
                    Student.stage == announcement.stage,
                )
            ),
        )
    elif scope == AnnouncementScope.GROUP:
        ids = _active_user_ids(
            db, User.id.in_(select(Student.user_id).where(Student.group_id == scope_id))
        )
    elif scope == AnnouncementScope.OFFERING:
        ids = offering_student_ids(db, scope_id) if scope_id else []
        offering = db.get(CourseOffering, scope_id) if scope_id else None
        if offering is not None and offering.instructor_id is not None:
            ids.append(offering.instructor_id)
    else:  # pragma: no cover - enum مغطى كاملاً
        ids = []

    return [user_id for user_id in dict.fromkeys(ids) if user_id != announcement.created_by]


def notify_users(
    db: Session,
    user_ids: list[uuid.UUID],
    *,
    type_: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> int:
    """يضيف إشعارات صندوق الوارد لكل مستخدم ويعيد العدد."""
    created = 0
    for user_id in user_ids:
        db.add(
            Notification(
                user_id=user_id,
                type=type_,
                title=title,
                body=body,
                data=data,
            )
        )
        created += 1
    return created


def notify_offering_students(
    db: Session,
    offering_id: uuid.UUID,
    *,
    type_: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> int:
    return notify_users(
        db,
        offering_student_ids(db, offering_id),
        type_=type_,
        title=title,
        body=body,
        data=data,
    )


def staff_offering_ids(db: Session, user: User) -> list[uuid.UUID]:
    """عروض المادة التي يدرّسها المستخدم (للتدريسي)."""
    if user.role != UserRole.INSTRUCTOR:
        return []
    return list(
        db.scalars(select(CourseOffering.id).where(CourseOffering.instructor_id == user.id))
    )
