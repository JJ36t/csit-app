# -*- coding: utf-8 -*-
"""الأعذار (V2 في الخطة): رفع عذر بصورة أو PDF، مراجعة من صاحب المادة،
وتحويل سجل الغياب إلى «غياب بعذر» تلقائياً عند القبول.

قواعد العمل:
- الطالب يرفع عذراً واحداً لكل جلسة، وخلال نافذة زمنية من تاريخ المحاضرة
  (`EXCUSE_WINDOW_DAYS`، 14 يوماً افتراضياً) — بعدها لا يُقبل العذر.
- لا يُقبل عذر لجلسة لم يسجّل فيها الطالب غياباً فعلياً (حاضر/متأخر لا يُعذر).
- القبول يكتب/يحدّث سجل الحضور بحالة `excused` وطريقة `manual` مع سجل تدقيق،
  ويُشعر الطالب بالقرار وسببه.
"""
import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.errors import ApiError
from app.models import (
    AbsenceExcuse,
    AttendanceRecord,
    Course,
    CourseOffering,
    LectureSession,
    StoredFile,
    User,
)
from app.models.enums import (
    AttendanceMethod,
    AttendanceStatus,
    ExcuseStatus,
    UserRole,
)
from app.services.access import (
    require_enrollment,
    require_offering_staff,
    require_student_row,
    user_offering_ids,
)
from app.services.audit import log_action
from app.services.file_links import signed_path
from app.services.notifications import notify_users
from app.services.storage import save_upload

router = APIRouter(tags=["excuses"])

# نافذة قبول العذر بعد تاريخ المحاضرة — قابلة للتغيير من الإعدادات لاحقاً
EXCUSE_WINDOW_DAYS = 14
BAGHDAD = timezone(timedelta(hours=3))
ALLOWED_EXCUSE_MIME = ("application/pdf", "image/jpeg", "image/png", "image/webp", "image/heic")


def _today_baghdad() -> date:
    """«اليوم» بتوقيت بغداد — تاريخ الجلسات مخزَّن بهذا المعنى."""
    return datetime.now(timezone.utc).astimezone(BAGHDAD).date()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


class ReviewIn(BaseModel):
    status: ExcuseStatus
    note: str | None = Field(default=None, max_length=500)


def _excuse_payload(
    excuse: AbsenceExcuse,
    session: LectureSession,
    course: Course,
    student_name: str | None = None,
    file_row: StoredFile | None = None,
) -> dict:
    return {
        "excuse_id": str(excuse.id),
        "session_id": str(session.id),
        "session_date": session.date.isoformat(),
        "course_code": course.code,
        "course_name_ar": course.name_ar,
        "student_id": str(excuse.student_id),
        "student_name_ar": student_name,
        "reason": excuse.reason,
        "status": excuse.status.value,
        "review_note": excuse.review_note,
        "reviewed_at": excuse.reviewed_at.isoformat() if excuse.reviewed_at else None,
        "created_at": excuse.created_at.isoformat() if excuse.created_at else None,
        "attachment": (
            {
                "file_id": str(file_row.id),
                "name": file_row.original_name,
                "size": file_row.size,
                "download_url": signed_path(str(file_row.id)),
            }
            if file_row is not None
            else None
        ),
    }


def _load_excuse_context(db: Session, excuse: AbsenceExcuse):
    session = db.get(LectureSession, excuse.session_id)
    offering = db.get(CourseOffering, session.offering_id) if session else None
    course = db.get(Course, offering.course_id) if offering else None
    if session is None or offering is None or course is None:  # pragma: no cover - سلامة مرجعية
        raise ApiError(404, "excuse_context_missing", "تعذّر ربط العذر بمحاضرته")
    return session, offering, course


@router.post("/excuses")
async def submit_excuse(
    session_id: uuid.UUID = Form(),
    reason: str = Form(min_length=5, max_length=2000),
    file: UploadFile | None = File(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_student_row(db, user)
    session = db.get(LectureSession, session_id)
    if session is None:
        raise ApiError(404, "session_not_found", "المحاضرة غير موجودة")
    require_enrollment(db, user, session.offering_id)

    # نافذة القبول: لا أعذار قديمة بلا حد
    local_date = session.date
    if local_date < _today_baghdad() - timedelta(days=EXCUSE_WINDOW_DAYS):
        raise ApiError(
            400,
            "excuse_window_closed",
            f"انتهت مدة رفع العذر ({EXCUSE_WINDOW_DAYS} يوماً من تاريخ المحاضرة)",
        )

    # لا عذر بلا غياب فعلي
    record = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.session_id == session.id,
            AttendanceRecord.student_id == user.id,
        )
    )
    if record is not None and record.status in (
        AttendanceStatus.PRESENT,
        AttendanceStatus.LATE,
        AttendanceStatus.EXCUSED,
    ):
        raise ApiError(409, "not_absent", "لا يمكن رفع عذر لمحاضرة سُجّل فيها حضورك")

    existing = db.scalar(
        select(AbsenceExcuse).where(
            AbsenceExcuse.session_id == session.id,
            AbsenceExcuse.student_id == user.id,
            AbsenceExcuse.status == ExcuseStatus.PENDING,
            AbsenceExcuse.deleted_at.is_(None),
        )
    )
    if existing is not None:
        raise ApiError(409, "excuse_pending", "لديك عذر قيد المراجعة لهذه المحاضرة")

    file_row: StoredFile | None = None
    if file is not None and file.filename:
        mime = (file.content_type or "").lower()
        if mime not in ALLOWED_EXCUSE_MIME:
            raise ApiError(400, "unsupported_file_type", "المرفق يجب أن يكون صورة أو PDF")
        saved = await save_upload(file)
        file_row = StoredFile(**saved, uploader_id=user.id)
        db.add(file_row)
        db.flush()

    excuse = AbsenceExcuse(
        student_id=user.id,
        session_id=session.id,
        reason=reason.strip(),
        attachment_file_id=file_row.id if file_row else None,
        status=ExcuseStatus.PENDING,
    )
    db.add(excuse)
    db.flush()

    log_action(
        db,
        actor=user,
        action="excuse_submitted",
        entity="absence_excuse",
        entity_id=str(excuse.id),
        after={
            "session_id": str(session.id),
            "has_attachment": file_row is not None,
        },
    )
    db.commit()
    _, _, course = _load_excuse_context(db, excuse)
    return _excuse_payload(excuse, session, course, user.full_name_ar, file_row)


@router.get("/excuses")
def my_excuses(
    status: ExcuseStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_student_row(db, user)
    conditions = [
        AbsenceExcuse.student_id == user.id,
        AbsenceExcuse.deleted_at.is_(None),
    ]
    if status is not None:
        conditions.append(AbsenceExcuse.status == status)

    rows = db.execute(
        select(AbsenceExcuse, LectureSession, Course)
        .join(LectureSession, LectureSession.id == AbsenceExcuse.session_id)
        .join(CourseOffering, CourseOffering.id == LectureSession.offering_id)
        .join(Course, Course.id == CourseOffering.course_id)
        .where(*conditions)
        .order_by(AbsenceExcuse.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    files = _files_for(db, [row[0].attachment_file_id for row in rows])
    return {
        "items": [
            _excuse_payload(excuse, session, course, file_row=files.get(excuse.attachment_file_id))
            for excuse, session, course in rows
        ]
    }


def _files_for(db: Session, ids: list[uuid.UUID | None]) -> dict[uuid.UUID, StoredFile]:
    real = [value for value in ids if value is not None]
    if not real:
        return {}
    rows = db.scalars(select(StoredFile).where(StoredFile.id.in_(real)))
    return {row.id: row for row in rows}


@router.get("/admin/excuses")
def review_queue(
    status: ExcuseStatus = Query(default=ExcuseStatus.PENDING),
    offering_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """قائمة المراجعة: التدريسي يرى موادّه، رئيس القسم قسمه، والمدير الكل."""
    if user.role == UserRole.STUDENT:
        raise ApiError(403, "forbidden", "هذه القائمة للتدريسي والإدارة")

    offering_ids = user_offering_ids(db, user)
    if offering_id is not None:
        if offering_id not in offering_ids:
            raise ApiError(403, "not_offering_staff", "لا تملك صلاحية على هذه المادة")
        offering_ids = [offering_id]
    if not offering_ids:
        return {"items": [], "pending_total": 0}

    conditions = [
        AbsenceExcuse.status == status,
        AbsenceExcuse.deleted_at.is_(None),
        LectureSession.offering_id.in_(offering_ids),
    ]
    rows = db.execute(
        select(AbsenceExcuse, LectureSession, Course, User)
        .join(LectureSession, LectureSession.id == AbsenceExcuse.session_id)
        .join(CourseOffering, CourseOffering.id == LectureSession.offering_id)
        .join(Course, Course.id == CourseOffering.course_id)
        .join(User, User.id == AbsenceExcuse.student_id)
        .where(*conditions)
        .order_by(AbsenceExcuse.created_at)
        .limit(limit)
        .offset(offset)
    ).all()

    files = _files_for(db, [row[0].attachment_file_id for row in rows])
    pending_total = len(
        db.scalars(
            select(AbsenceExcuse.id)
            .join(LectureSession, LectureSession.id == AbsenceExcuse.session_id)
            .where(
                AbsenceExcuse.status == ExcuseStatus.PENDING,
                AbsenceExcuse.deleted_at.is_(None),
                LectureSession.offering_id.in_(offering_ids),
            )
        ).all()
    )
    return {
        "items": [
            _excuse_payload(
                excuse,
                session,
                course,
                student.full_name_ar,
                files.get(excuse.attachment_file_id),
            )
            for excuse, session, course, student in rows
        ],
        "pending_total": pending_total,
    }


@router.post("/admin/excuses/{excuse_id}/review")
def review_excuse(
    excuse_id: uuid.UUID,
    body: ReviewIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if body.status == ExcuseStatus.PENDING:
        raise ApiError(400, "invalid_status", "القرار يجب أن يكون قبولاً أو رفضاً")

    excuse = db.get(AbsenceExcuse, excuse_id)
    if excuse is None or excuse.deleted_at is not None:
        raise ApiError(404, "excuse_not_found", "العذر غير موجود")
    if excuse.status != ExcuseStatus.PENDING:
        raise ApiError(409, "already_reviewed", "تمت مراجعة هذا العذر سابقاً")

    session, offering, course = _load_excuse_context(db, excuse)
    require_offering_staff(db, user, offering)

    before = {"status": excuse.status.value}
    excuse.status = body.status
    excuse.reviewed_by = user.id
    excuse.reviewed_at = _utc_now()
    excuse.review_note = (body.note or "").strip() or None

    attendance_changed = False
    if body.status == ExcuseStatus.APPROVED:
        record = db.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.session_id == session.id,
                AttendanceRecord.student_id == excuse.student_id,
            )
        )
        if record is None:
            record = AttendanceRecord(
                session_id=session.id,
                student_id=excuse.student_id,
                status=AttendanceStatus.EXCUSED,
                method=AttendanceMethod.MANUAL,
                scanned_at=_utc_now(),
                marked_by=user.id,
            )
            db.add(record)
            attendance_changed = True
        elif record.status != AttendanceStatus.EXCUSED:
            record.status = AttendanceStatus.EXCUSED
            record.method = AttendanceMethod.MANUAL
            record.marked_by = user.id
            record.flag_reason = "excuse_approved"
            attendance_changed = True

    title = "قبول عذرك" if body.status == ExcuseStatus.APPROVED else "رفض عذرك"
    body_text = f"{course.name_ar} — {session.date.isoformat()}"
    if excuse.review_note:
        body_text += f"\n{excuse.review_note}"
    notify_users(
        db,
        [excuse.student_id],
        type_="excuse_reviewed",
        title=title,
        body=body_text,
        data={"excuse_id": str(excuse.id), "status": body.status.value},
    )

    log_action(
        db,
        actor=user,
        action="excuse_reviewed",
        entity="absence_excuse",
        entity_id=str(excuse.id),
        before=before,
        after={
            "status": body.status.value,
            "attendance_changed": attendance_changed,
            "note": excuse.review_note,
        },
    )
    db.commit()
    return _excuse_payload(excuse, session, course)


@router.delete("/excuses/{excuse_id}")
def cancel_excuse(
    excuse_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    excuse = db.get(AbsenceExcuse, excuse_id)
    if excuse is None or excuse.deleted_at is not None or excuse.student_id != user.id:
        raise ApiError(404, "excuse_not_found", "العذر غير موجود")
    if excuse.status != ExcuseStatus.PENDING:
        raise ApiError(409, "already_reviewed", "لا يمكن سحب عذر تمت مراجعته")

    excuse.deleted_at = _utc_now()
    log_action(
        db,
        actor=user,
        action="excuse_withdrawn",
        entity="absence_excuse",
        entity_id=str(excuse.id),
    )
    db.commit()
    return {"excuse_id": str(excuse.id), "withdrawn": True}
