# -*- coding: utf-8 -*-
"""توليد جلسات المحاضرات من الحصص الأسبوعية (نظام «قلب» الحضور)."""
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CourseOffering, LectureSession, Term, TimetableSlot
from app.models.enums import LectureSessionStatus

BAGHDAD = timezone(timedelta(hours=3))
DEFAULT_WEEKS = 16


def baghdad_now() -> datetime:
    return datetime.now(timezone.utc).astimezone(BAGHDAD)


def to_utc(day: date, clock: time) -> datetime:
    """توقيت بغداد (UTC+3 ثابت) → UTC للتخزين."""
    local = datetime.combine(day, clock).replace(tzinfo=BAGHDAD)
    return local.astimezone(timezone.utc)


def schema_weekday(day: date) -> int:
    """0=الأحد … 6=السبت كما في النموذج (Python: الاثنين=0)."""
    return (day.weekday() + 1) % 7


def generate_sessions_for_slot(
    db: Session,
    slot: TimetableSlot,
    *,
    weeks: int = DEFAULT_WEEKS,
) -> int:
    """ينشئ جلسة لكل أسبوع لنفس اليوم، متجاهلاً الموجود. يعيد عدد المُنشأ."""
    offering = db.get(CourseOffering, slot.offering_id)
    if offering is None:
        return 0

    term = db.get(Term, offering.term_id)
    start = term.start_date if term is not None and term.start_date else baghdad_now().date()
    # أول يوم يطابق weekday الحصة ابتداءً من بداية الفصل
    delta = (slot.weekday - schema_weekday(start)) % 7
    first = start + timedelta(days=delta)

    existing = {
        row
        for row in db.scalars(
            select(LectureSession.date).where(LectureSession.slot_id == slot.id)
        )
    }

    created = 0
    for index in range(weeks):
        day = first + timedelta(days=7 * index)
        if term is not None and term.end_date is not None and day > term.end_date:
            break
        if day in existing:
            continue
        db.add(
            LectureSession(
                offering_id=slot.offering_id,
                slot_id=slot.id,
                date=day,
                starts_at=to_utc(day, slot.start_time),
                ends_at=to_utc(day, slot.end_time),
                status=LectureSessionStatus.SCHEDULED,
                window_s=settings.qr_rotation_seconds,
            )
        )
        created += 1
    return created


def first_slot_date(slot: TimetableSlot, term: Term | None) -> date:
    start = term.start_date if term is not None and term.start_date else baghdad_now().date()
    return start + timedelta(days=(slot.weekday - schema_weekday(start)) % 7)
