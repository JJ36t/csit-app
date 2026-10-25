# -*- coding: utf-8 -*-
"""الحضور: فتح/إغلاق الجلسة، رمز QR المتجدد، المسح، اللحظي، والتعديل اليدوي.

بحسب القسم 6 و9 من الخطة: الدوران كل 20 ثانية، ربط الجهاز، تحقق الموقع،
وتعليم الحضور «المشكوك» للمراجعة بدل الرفض.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_current_user
from app.errors import ApiError
from app.models import (
    AttendanceRecord,
    Course,
    CourseOffering,
    Device,
    Enrollment,
    LectureSession,
    Student,
    TimetableSlot,
    User,
)
from app.models.enums import (
    AttendanceMethod,
    AttendanceStatus,
    DeviceStatus,
    EnrollmentStatus,
    LectureSessionStatus,
)
from app.security import as_utc
from app.services.access import require_enrollment, require_offering_staff, require_student_row
from app.services.attendance import (
    distance_m,
    make_token,
    new_secret,
    token_status,
    window_for,
)
from app.services.audit import log_action
from app.services.rate_limit import guard, record

router = APIRouter(tags=["attendance"])

SCAN_PER_MINUTE = 8


# ----------------------------- نماذج الطلب -----------------------------

class LocationIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    accuracy_m: float | None = Field(default=None, ge=0, le=5000)


class ScanIn(BaseModel):
    session_id: uuid.UUID
    token: str = Field(min_length=4, max_length=80)
    device_id: uuid.UUID
    location: LocationIn | None = None


class AttendancePatchIn(BaseModel):
    status: AttendanceStatus
    reason: str | None = Field(default=None, max_length=200)


# ----------------------------- أدوات -----------------------------

def _qr_payload(session: LectureSession, now: datetime) -> dict:
    rotation = session.window_s or settings.qr_rotation_seconds
    window = window_for(now, rotation)
    token = make_token(session.secret or "", str(session.id), window)
    next_boundary = (window + 1) * rotation
    return {
        "token": token,
        "window": window,
        "rotation_s": rotation,
        "expires_in": max(1, int(next_boundary - now.timestamp())),
    }


def _load_session(db: Session, session_id: uuid.UUID) -> LectureSession:
    session = db.get(LectureSession, session_id)
    if session is None:
        raise ApiError(404, "session_not_found", "الجلسة غير موجودة")
    return session


def _status_counts(db: Session, session_id) -> dict[str, int]:
    rows = db.execute(
        select(AttendanceRecord.status, func.count())
        .where(AttendanceRecord.session_id == session_id)
        .group_by(AttendanceRecord.status)
    ).all()
    return {status.value: count for status, count in rows}


def _percentage(records: dict[str, int], total_sessions: int) -> float:
    counted = (
        records.get("present", 0) + records.get("late", 0) + records.get("excused", 0)
    )
    if total_sessions <= 0:
        return 0.0
    return round(100.0 * counted / total_sessions, 1)


# ----------------------------- جلسات التدريسي -----------------------------

@router.post("/sessions/{session_id}/open")
def open_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    now = datetime.now(timezone.utc)
    session = _load_session(db, session_id)
    offering = db.get(CourseOffering, session.offering_id)
    require_offering_staff(db, user, offering)

    if session.status == LectureSessionStatus.CANCELLED:
        raise ApiError(409, "session_cancelled", "هذه الجلسة ملغاة")
    if session.status == LectureSessionStatus.CLOSED:
        raise ApiError(409, "session_closed", "هذه الجلسة أُغلقت")

    start, end = as_utc(session.starts_at), as_utc(session.ends_at)
    if now < start - timedelta(minutes=settings.attendance_window_before_min):
        raise ApiError(409, "session_not_started", "لم يحن وقت هذه الجلسة بعد")
    if now > end + timedelta(minutes=settings.attendance_window_after_min):
        raise ApiError(409, "session_expired", "انتهى وقت هذه الجلسة")

    if session.status != LectureSessionStatus.OPEN or not session.secret:
        session.secret = new_secret()
        session.status = LectureSessionStatus.OPEN
        session.opened_by = user.id
        session.window_s = settings.qr_rotation_seconds
        db.commit()
        db.refresh(session)

    return {
        "session_id": str(session.id),
        "status": session.status.value,
        "qr": _qr_payload(session, now),
    }


@router.post("/sessions/{session_id}/close")
def close_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    session = _load_session(db, session_id)
    offering = db.get(CourseOffering, session.offering_id)
    require_offering_staff(db, user, offering)

    enrolled = list(
        db.scalars(
            select(Enrollment.student_id).where(
                Enrollment.offering_id == session.offering_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
    )
    recorded = set(
        db.scalars(
            select(AttendanceRecord.student_id).where(
                AttendanceRecord.session_id == session.id
            )
        )
    )
    marked_absent = 0
    for student_id in enrolled:
        if student_id in recorded:
            continue
        db.add(
            AttendanceRecord(
                session_id=session.id,
                student_id=student_id,
                status=AttendanceStatus.ABSENT,
                method=AttendanceMethod.MANUAL,
                marked_by=user.id,
            )
        )
        marked_absent += 1

    session.status = LectureSessionStatus.CLOSED
    db.commit()

    counts = _status_counts(db, session.id)
    return {
        "session_id": str(session.id),
        "status": session.status.value,
        "absent_marked": marked_absent,
        "counts": counts,
    }


@router.get("/sessions/{session_id}/live")
def live_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    now = datetime.now(timezone.utc)
    session = _load_session(db, session_id)
    offering = db.get(CourseOffering, session.offering_id)
    require_offering_staff(db, user, offering)

    rows = {
        record.student_id: record
        for record in db.scalars(
            select(AttendanceRecord).where(AttendanceRecord.session_id == session.id)
        )
    }
    enrolled = db.execute(
        select(User.university_id, User.full_name_ar, User.id)
        .join(Enrollment, Enrollment.student_id == User.id)
        .where(
            Enrollment.offering_id == session.offering_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        .order_by(User.full_name_ar)
    ).all()

    students = []
    for university_id, full_name, student_id in enrolled:
        record = rows.get(student_id)
        students.append(
            {
                "university_id": university_id,
                "full_name_ar": full_name,
                "status": record.status.value if record else None,
                "flagged": bool(record.flagged) if record else False,
            }
        )

    return {
        "session_id": str(session.id),
        "status": session.status.value,
        "starts_at": as_utc(session.starts_at).isoformat(),
        "ends_at": as_utc(session.ends_at).isoformat(),
        "qr": _qr_payload(session, now)
        if session.status == LectureSessionStatus.OPEN and session.secret
        else None,
        "counts": _status_counts(db, session.id),
        "students": students,
    }


@router.patch("/attendance/{record_id}")
def mark_attendance(
    record_id: uuid.UUID,
    body: AttendancePatchIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    record_row = db.get(AttendanceRecord, record_id)
    if record_row is None:
        raise ApiError(404, "record_not_found", "سجل الحضور غير موجود")
    session = db.get(LectureSession, record_row.session_id)
    offering = db.get(CourseOffering, session.offering_id)
    require_offering_staff(db, user, offering)

    before = {
        "status": record_row.status.value,
        "flag_reason": record_row.flag_reason,
    }
    record_row.status = body.status
    record_row.marked_by = user.id
    if body.reason:
        record_row.flag_reason = body.reason

    log_action(
        db,
        actor=user,
        action="attendance_updated",
        entity="attendance",
        entity_id=str(record_row.id),
        before=before,
        after={
            "status": record_row.status.value,
            "flag_reason": record_row.flag_reason,
            "reason": body.reason,
        },
    )
    db.commit()
    return {
        "attendance_id": str(record_row.id),
        "status": record_row.status.value,
        "flag_reason": record_row.flag_reason,
    }


# ----------------------------- مسح الطالب -----------------------------

@router.post("/attendance/scan")
def scan_attendance(
    body: ScanIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    now = datetime.now(timezone.utc)
    limit_key = f"scan:{user.id}"
    if not guard(limit_key, limit=SCAN_PER_MINUTE):
        raise ApiError(
            429, "too_many_scans", "محاولات مسح كثيرة خلال دقيقة؛ انتظر قليلاً"
        )

    session = _load_session(db, body.session_id)
    if session.status != LectureSessionStatus.OPEN or not session.secret:
        raise ApiError(409, "session_not_open", "الجلسة غير مفتوحة للحضور")

    verdict = token_status(
        secret=session.secret,
        session_id=str(session.id),
        token=body.token,
        rotation_s=session.window_s or settings.qr_rotation_seconds,
        tolerance=settings.qr_tolerance_windows,
        now=now,
    )
    if verdict == "invalid":
        record(limit_key)
        raise ApiError(
            400, "invalid_token", "رمز الحضور غير صالح؛ أعد مسح الرمز المعروض الآن"
        )
    if verdict == "stale":
        record(limit_key)
        raise ApiError(410, "token_expired", "انتهت صلاحية رمز الحضور؛ امسح الرمز الجديد")

    require_student_row(db, user)
    require_enrollment(db, user, session.offering_id)

    device = db.get(Device, body.device_id)
    if (
        device is None
        or device.user_id != user.id
        or device.status != DeviceStatus.ACTIVE
    ):
        raise ApiError(
            403, "device_not_bound", "هذا الجهاز غير مربوط بحسابك؛ راجع قسمك"
        )

    existing = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.session_id == session.id,
            AttendanceRecord.student_id == user.id,
        )
    )
    if existing is not None:
        raise ApiError(409, "already_registered", "سُجّل حضورك لهذه الجلسة مسبقاً")

    late_after = as_utc(session.starts_at) + timedelta(
        minutes=settings.attendance_grace_minutes
    )
    status = AttendanceStatus.PRESENT if now <= late_after else AttendanceStatus.LATE

    flagged = False
    flag_reason: str | None = None
    coords = _reference_point(db, session)
    if body.location is not None and coords is not None:
        ref_lat, ref_lng, radius = coords
        distance = distance_m(body.location.lat, body.location.lng, ref_lat, ref_lng)
        if distance > radius:
            flagged = True
            flag_reason = f"outside_campus:{int(distance)}m"
    elif body.location is None:
        flagged = True
        flag_reason = "no_location"

    record_row = AttendanceRecord(
        session_id=session.id,
        student_id=user.id,
        status=status,
        method=AttendanceMethod.QR,
        device_id=device.id,
        lat=body.location.lat if body.location else None,
        lng=body.location.lng if body.location else None,
        accuracy=body.location.accuracy_m if body.location else None,
        flagged=flagged,
        flag_reason=flag_reason,
        marked_by=None,
    )
    db.add(record_row)
    db.commit()
    record(limit_key)

    return {
        "attendance_id": str(record_row.id),
        "status": record_row.status.value,
        "flagged": record_row.flagged,
        "flag_reason": record_row.flag_reason,
        "message_ar": "تم تسجيل حضورك"
        + (" (قيد المراجعة لخروج الموقع عن النطاق)" if flagged else ""),
    }


def _reference_point(db: Session, session: LectureSession):
    """نقطة التحقق: إحداثيات القاعة إن وُجدت، وإلا نطاق الحرم من الإعدادات."""
    from app.models import Room  # استيراد محلي لتجنّب التكرار في الأعلى

    if session.slot_id is not None:
        slot = db.get(TimetableSlot, session.slot_id)
        if slot is not None and slot.room_id is not None:
            room = db.get(Room, slot.room_id)
            if room is not None and room.lat is not None and room.lng is not None:
                return (
                    room.lat,
                    room.lng,
                    float(room.radius_m or settings.campus_radius_m),
                )

    if settings.campus_lat is not None and settings.campus_lng is not None:
        return settings.campus_lat, settings.campus_lng, float(settings.campus_radius_m)
    return None


# ----------------------------- التقارير -----------------------------

@router.get("/attendance/summary")
def attendance_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_student_row(db, user)
    enrollments = list(
        db.scalars(
            select(Enrollment).where(
                Enrollment.student_id == user.id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
    )

    items = []
    for enrollment in enrollments:
        offering = db.get(CourseOffering, enrollment.offering_id)
        course = db.get(Course, offering.course_id)
        total_sessions = (
            db.scalar(
                select(func.count())
                .select_from(LectureSession)
                .where(
                    LectureSession.offering_id == offering.id,
                    LectureSession.status != LectureSessionStatus.CANCELLED,
                )
            )
            or 0
        )
        counts = dict(
            db.execute(
                select(AttendanceRecord.status, func.count())
                .join(LectureSession, LectureSession.id == AttendanceRecord.session_id)
                .where(
                    LectureSession.offering_id == offering.id,
                    AttendanceRecord.student_id == user.id,
                )
                .group_by(AttendanceRecord.status)
            ).all()
        )
        normalized = {status.value: count for status, count in counts.items()}
        items.append(
            {
                "offering_id": str(offering.id),
                "course_code": course.code,
                "course_name_ar": course.name_ar,
                "sessions_total": total_sessions,
                "present": normalized.get("present", 0),
                "late": normalized.get("late", 0),
                "absent": normalized.get("absent", 0),
                "excused": normalized.get("excused", 0),
                "percentage": _percentage(normalized, total_sessions),
            }
        )

    return {"items": items}


@router.get("/offerings/{offering_id}/attendance")
def my_offering_attendance(
    offering_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    offering = db.get(CourseOffering, offering_id)
    if offering is None:
        raise ApiError(404, "offering_not_found", "المادة غير موجودة")
    require_enrollment(db, user, offering.id)

    rows = db.execute(
        select(LectureSession.date, LectureSession.status, AttendanceRecord.status,
               AttendanceRecord.flagged, AttendanceRecord.flag_reason)
        .join(AttendanceRecord, AttendanceRecord.session_id == LectureSession.id)
        .where(
            LectureSession.offering_id == offering.id,
            AttendanceRecord.student_id == user.id,
        )
        .order_by(LectureSession.date)
    ).all()

    return {
        "offering_id": str(offering.id),
        "records": [
            {
                "date": day.isoformat(),
                "session_status": session_status.value,
                "status": status.value,
                "flagged": flagged,
                "flag_reason": reason,
            }
            for day, session_status, status, flagged, reason in rows
        ],
    }


@router.get("/offerings/{offering_id}/attendance/report")
def offering_report(
    offering_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    offering = db.get(CourseOffering, offering_id)
    if offering is None:
        raise ApiError(404, "offering_not_found", "المادة غير موجودة")
    require_offering_staff(db, user, offering)

    total_sessions = (
        db.scalar(
            select(func.count())
            .select_from(LectureSession)
            .where(
                LectureSession.offering_id == offering.id,
                LectureSession.status != LectureSessionStatus.CANCELLED,
            )
        )
        or 0
    )

    students = db.execute(
        select(User.id, User.university_id, User.full_name_ar)
        .join(Enrollment, Enrollment.student_id == User.id)
        .where(
            Enrollment.offering_id == offering.id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        .order_by(User.full_name_ar)
    ).all()

    counts_by_student: dict[uuid.UUID, dict[str, int]] = {}
    for student_id, status, count in db.execute(
        select(AttendanceRecord.student_id, AttendanceRecord.status, func.count())
        .join(LectureSession, LectureSession.id == AttendanceRecord.session_id)
        .where(LectureSession.offering_id == offering.id)
        .group_by(AttendanceRecord.student_id, AttendanceRecord.status)
    ).all():
        counts_by_student.setdefault(student_id, {})[status.value] = count

    items = []
    for student_id, university_id, full_name in students:
        counts = counts_by_student.get(student_id, {})
        items.append(
            {
                "university_id": university_id,
                "full_name_ar": full_name,
                "present": counts.get("present", 0),
                "late": counts.get("late", 0),
                "absent": counts.get("absent", 0),
                "excused": counts.get("excused", 0),
                "percentage": _percentage(counts, total_sessions),
            }
        )

    return {
        "offering_id": str(offering.id),
        "sessions_total": total_sessions,
        "students": items,
    }
