# -*- coding: utf-8 -*-
"""الجدول الزمني للقراءة: جلسات المستخدم وتغييراتها (القسم 9 من الخطة)."""
import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.errors import ApiError
from app.models import (
    Course,
    CourseOffering,
    Enrollment,
    Group,
    LectureSession,
    Room,
    Staff,
    TimetableChange,
    TimetableSlot,
    User,
)
from app.models.enums import EnrollmentStatus, UserRole
from app.security import as_utc
from app.services.sessions import BAGHDAD

router = APIRouter(tags=["timetable"])


def _user_offering_ids(db: Session, user: User) -> list[uuid.UUID]:
    if user.role == UserRole.STUDENT:
        return list(
            db.scalars(
                select(Enrollment.offering_id).where(
                    Enrollment.student_id == user.id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
            )
        )
    if user.role == UserRole.INSTRUCTOR:
        return list(
            db.scalars(
                select(CourseOffering.id).where(CourseOffering.instructor_id == user.id)
            )
        )
    if user.role == UserRole.DEPARTMENT_HEAD:
        staff = db.get(Staff, user.id)
        if staff is None or staff.department_id is None:
            return []
        return list(
            db.scalars(
                select(CourseOffering.id)
                .join(Group, Group.id == CourseOffering.group_id)
                .where(Group.department_id == staff.department_id)
            )
        )
    if user.role == UserRole.COLLEGE_ADMIN:
        return list(db.scalars(select(CourseOffering.id)))
    return []


@router.get("/timetable")
def get_timetable(
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    today = datetime.now(timezone.utc).astimezone(BAGHDAD).date()
    start = date_from or today
    end = date_to or (start + timedelta(days=13))
    if end < start:
        raise ApiError(400, "invalid_range", "نطاق التاريخ غير صحيح")
    if (end - start).days > 120:
        raise ApiError(400, "range_too_wide", "النطاق الأقصى 120 يوماً")

    offering_ids = _user_offering_ids(db, user)
    if not offering_ids:
        return {"items": []}

    rows = db.execute(
        select(LectureSession, CourseOffering, Course, TimetableSlot, Room)
        .join(CourseOffering, CourseOffering.id == LectureSession.offering_id)
        .join(Course, Course.id == CourseOffering.course_id)
        .outerjoin(TimetableSlot, TimetableSlot.id == LectureSession.slot_id)
        .outerjoin(Room, Room.id == TimetableSlot.room_id)
        .where(
            LectureSession.offering_id.in_(offering_ids),
            LectureSession.date >= start,
            LectureSession.date <= end,
        )
        .order_by(LectureSession.starts_at)
    ).all()

    return {
        "items": [
            {
                "session_id": str(session.id),
                "date": session.date.isoformat(),
                "starts_at": as_utc(session.starts_at).isoformat(),
                "ends_at": as_utc(session.ends_at).isoformat(),
                "course_code": course.code,
                "course_name_ar": course.name_ar,
                "kind": offering.session_kind.value,
                "room": room.name if room is not None else None,
                "status": session.status.value,
            }
            for session, offering, course, _slot, room in rows
        ]
    }


@router.get("/timetable/changes")
def get_timetable_changes(
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    today = datetime.now(timezone.utc).astimezone(BAGHDAD).date()
    start = date_from or today
    end = date_to or (start + timedelta(days=13))

    offering_ids = _user_offering_ids(db, user)
    if not offering_ids:
        return {"items": []}

    rows = db.execute(
        select(TimetableChange, TimetableSlot, CourseOffering, Course)
        .join(TimetableSlot, TimetableSlot.id == TimetableChange.slot_id)
        .join(CourseOffering, CourseOffering.id == TimetableSlot.offering_id)
        .join(Course, Course.id == CourseOffering.course_id)
        .where(
            TimetableSlot.offering_id.in_(offering_ids),
            TimetableChange.date >= start,
            TimetableChange.date <= end,
        )
        .order_by(TimetableChange.date)
    ).all()

    return {
        "items": [
            {
                "change_id": str(change.id),
                "date": change.date.isoformat(),
                "type": change.type.value,
                "course_name_ar": course.name_ar,
                "new_start": change.new_start.isoformat() if change.new_start else None,
                "reason": change.reason,
            }
            for change, _slot, _offering, course in rows
        ]
    }
