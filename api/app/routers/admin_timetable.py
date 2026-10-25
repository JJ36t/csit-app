# -*- coding: utf-8 -*-
"""إدارة الجدول: القاعات، الحصص الأسبوعية بكشف التعارضات، والتغييرات المؤرخة."""
import uuid
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_roles
from app.errors import ApiError
from app.models import (
    CourseOffering,
    Group,
    LectureSession,
    Room,
    TimetableChange,
    TimetableSlot,
    User,
)
from app.models.enums import LectureSessionStatus, SessionKind, TimetableChangeType, UserRole
from app.services.access import offering_department_id, staff_department_id
from app.services.audit import log_action
from app.services.sessions import generate_sessions_for_slot, to_utc

router = APIRouter(prefix="/admin/timetable", tags=["admin-timetable"])

MANAGER_ROLES = (UserRole.COLLEGE_ADMIN, UserRole.DEPARTMENT_HEAD)


class RoomIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    building: str | None = Field(default=None, max_length=100)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    radius_m: int | None = Field(default=None, ge=10, le=2000)


class SlotIn(BaseModel):
    offering_id: uuid.UUID
    weekday: int = Field(ge=0, le=6, description="0=الأحد … 6=السبت")
    start_time: time
    end_time: time
    room_id: uuid.UUID | None = None
    kind: SessionKind = SessionKind.THEORY


class ChangeIn(BaseModel):
    slot_id: uuid.UUID
    date: date
    type: TimetableChangeType
    new_start: time | None = None
    reason: str | None = Field(default=None, max_length=300)


def _scope_offering(db: Session, user: User, offering: CourseOffering) -> None:
    if user.role == UserRole.COLLEGE_ADMIN:
        return
    if staff_department_id(db, user) != offering_department_id(db, offering):
        raise ApiError(403, "outside_your_department", "هذه المادة خارج قسمك")


def _overlaps(a_start: time, a_end: time, b_start: time, b_end: time) -> bool:
    return a_start < b_end and b_start < a_end


def _assert_no_conflict(
    db: Session,
    *,
    offering: CourseOffering,
    weekday: int,
    start_time: time,
    end_time: time,
    room_id: uuid.UUID | None,
    exclude_slot_id: uuid.UUID | None = None,
) -> None:
    stmt = select(TimetableSlot).where(TimetableSlot.weekday == weekday)
    if exclude_slot_id is not None:
        stmt = stmt.where(TimetableSlot.id != exclude_slot_id)

    for slot in db.scalars(stmt):
        if not _overlaps(start_time, end_time, slot.start_time, slot.end_time):
            continue
        other = db.get(CourseOffering, slot.offering_id)
        if other is None:
            continue
        if room_id is not None and slot.room_id == room_id:
            raise ApiError(
                409,
                "room_conflict",
                "القاعة مشغولة في هذا الوقت بحصة أخرى",
                {"conflict_slot_id": str(slot.id)},
            )
        if (
            offering.instructor_id is not None
            and other.instructor_id == offering.instructor_id
        ):
            raise ApiError(
                409,
                "instructor_conflict",
                "التدريسي لديه حصة أخرى في هذا الوقت",
                {"conflict_slot_id": str(slot.id)},
            )
        if other.group_id == offering.group_id:
            raise ApiError(
                409,
                "group_conflict",
                "الشعبة لديها حصة أخرى في هذا الوقت",
                {"conflict_slot_id": str(slot.id)},
            )


@router.post("/rooms")
def create_room(
    body: RoomIn,
    user: User = Depends(require_roles(*MANAGER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    room = Room(
        name=body.name,
        building=body.building,
        lat=body.lat,
        lng=body.lng,
        radius_m=body.radius_m,
    )
    db.add(room)
    db.commit()
    return {"room_id": str(room.id), "name": room.name}


@router.post("/slots")
def create_slot(
    body: SlotIn,
    user: User = Depends(require_roles(*MANAGER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    if body.end_time <= body.start_time:
        raise ApiError(400, "invalid_time_range", "وقت النهاية يجب أن يكون بعد البداية")

    offering = db.get(CourseOffering, body.offering_id)
    if offering is None:
        raise ApiError(404, "offering_not_found", "المادة غير موجودة")
    _scope_offering(db, user, offering)

    if body.room_id is not None and db.get(Room, body.room_id) is None:
        raise ApiError(404, "room_not_found", "القاعة غير موجودة")

    _assert_no_conflict(
        db,
        offering=offering,
        weekday=body.weekday,
        start_time=body.start_time,
        end_time=body.end_time,
        room_id=body.room_id,
    )

    slot = TimetableSlot(
        offering_id=offering.id,
        weekday=body.weekday,
        start_time=body.start_time,
        end_time=body.end_time,
        room_id=body.room_id,
        kind=body.kind,
    )
    db.add(slot)
    db.flush()
    created = generate_sessions_for_slot(db, slot)
    log_action(
        db,
        actor=user,
        action="slot_created",
        entity="timetable_slot",
        entity_id=str(slot.id),
        after={
            "offering_id": str(offering.id),
            "weekday": body.weekday,
            "start": body.start_time.isoformat(),
            "end": body.end_time.isoformat(),
        },
    )
    db.commit()
    return {"slot_id": str(slot.id), "sessions_created": created}


@router.post("/changes")
def create_change(
    body: ChangeIn,
    user: User = Depends(require_roles(*MANAGER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    slot = db.get(TimetableSlot, body.slot_id)
    if slot is None:
        raise ApiError(404, "slot_not_found", "الحصة غير موجودة")
    offering = db.get(CourseOffering, slot.offering_id)
    if offering is None:
        raise ApiError(404, "offering_not_found", "المادة غير موجودة")
    _scope_offering(db, user, offering)

    session = db.scalar(
        select(LectureSession).where(
            LectureSession.slot_id == slot.id, LectureSession.date == body.date
        )
    )

    if body.type == TimetableChangeType.CANCEL:
        if session is None:
            raise ApiError(404, "session_not_found", "لا توجد جلسة بهذا التاريخ")
        if session.status == LectureSessionStatus.CLOSED:
            raise ApiError(409, "session_closed", "لا يمكن إلغاء جلسة مغلقة")
        session.status = LectureSessionStatus.CANCELLED

    elif body.type == TimetableChangeType.MOVE:
        if body.new_start is None:
            raise ApiError(400, "missing_new_start", "حدد وقت البداية الجديد")
        if session is None:
            raise ApiError(404, "session_not_found", "لا توجد جلسة بهذا التاريخ")
        if session.status in (
            LectureSessionStatus.CLOSED,
            LectureSessionStatus.CANCELLED,
        ):
            raise ApiError(409, "session_locked", "لا يمكن تعديل جلسة مغلقة أو ملغاة")

        duration = datetime.combine(body.date, slot.end_time) - datetime.combine(
            body.date, slot.start_time
        )
        new_end = (datetime.combine(body.date, body.new_start) + duration).time()
        _assert_no_conflict(
            db,
            offering=offering,
            weekday=slot.weekday,
            start_time=body.new_start,
            end_time=new_end,
            room_id=slot.room_id,
            exclude_slot_id=slot.id,
        )
        session.starts_at = to_utc(body.date, body.new_start)
        session.ends_at = to_utc(body.date, new_end)

    else:  # EXTRA
        if body.new_start is None:
            raise ApiError(400, "missing_new_start", "حدد وقت البداية للحصة الإضافية")
        if session is not None and session.status != LectureSessionStatus.CANCELLED:
            raise ApiError(409, "session_exists", "توجد جلسة بالفعل بهذا التاريخ")

        duration = datetime.combine(body.date, slot.end_time) - datetime.combine(
            body.date, slot.start_time
        )
        new_end = (datetime.combine(body.date, body.new_start) + duration).time()
        _assert_no_conflict(
            db,
            offering=offering,
            weekday=slot.weekday,
            start_time=body.new_start,
            end_time=new_end,
            room_id=slot.room_id,
            exclude_slot_id=slot.id,
        )
        if session is not None:
            session.starts_at = to_utc(body.date, body.new_start)
            session.ends_at = to_utc(body.date, new_end)
            session.status = LectureSessionStatus.SCHEDULED
        else:
            db.add(
                LectureSession(
                    offering_id=slot.offering_id,
                    slot_id=slot.id,
                    date=body.date,
                    starts_at=to_utc(body.date, body.new_start),
                    ends_at=to_utc(body.date, new_end),
                    status=LectureSessionStatus.SCHEDULED,
                )
            )

    change = TimetableChange(
        slot_id=slot.id,
        date=body.date,
        type=body.type,
        new_start=body.new_start,
        reason=body.reason,
        created_by=user.id,
    )
    db.add(change)
    log_action(
        db,
        actor=user,
        action="timetable_change",
        entity="timetable_slot",
        entity_id=str(slot.id),
        after={
            "date": body.date.isoformat(),
            "type": body.type.value,
            "new_start": body.new_start.isoformat() if body.new_start else None,
        },
    )
    db.commit()
    return {"change_id": str(change.id), "type": change.type.value}
