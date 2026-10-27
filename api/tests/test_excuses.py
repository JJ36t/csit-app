# -*- coding: utf-8 -*-
"""اختبارات الأعذار: الرفع، النافذة الزمنية، المراجعة، وأثر القبول على الحضور."""
import io
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.models import AttendanceRecord, LectureSession, Staff, User
from app.models.enums import (
    AttendanceMethod,
    AttendanceStatus,
    LectureSessionStatus,
    UserRole,
    UserStatus,
)
from app.security import hash_password
from world import PASSWORD, auth_headers, build_world, login

BAGHDAD = timezone(timedelta(hours=3))


def _add_session(world: dict, *, days_ago: int = 0, status=LectureSessionStatus.CLOSED) -> str:
    """جلسة إضافية لنفس المادة بتاريخ مختلف — لاختبار النافذة والغياب."""
    with SessionLocal() as db:
        starts = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=1)
        session = LectureSession(
            offering_id=uuid.UUID(world["offering"]),
            date=starts.astimezone(BAGHDAD).date(),
            starts_at=starts,
            ends_at=starts + timedelta(minutes=90),
            status=status,
            window_s=20,
        )
        db.add(session)
        db.commit()
        return str(session.id)


def _submit(client, headers, session_id: str, reason: str = "مراجعة طبية في المستشفى"):
    return client.post(
        "/api/v1/excuses",
        data={"session_id": session_id, "reason": reason},
        headers=headers,
    )


def test_student_submits_and_instructor_approves_marks_attendance(client):
    world = build_world()
    student_headers = auth_headers(login(client, "S-100", "exc-dev-01"))
    teacher_headers = auth_headers(login(client, "T-100", "exc-dev-02"))

    submitted = _submit(client, student_headers, world["session"])
    assert submitted.status_code == 200, submitted.text
    payload = submitted.json()
    assert payload["status"] == "pending"
    assert payload["course_code"] == "CS101"
    assert payload["attachment"] is None
    assert payload["student_name_ar"] == "علي حسن محمد"

    queue = client.get("/api/v1/admin/excuses", headers=teacher_headers)
    assert queue.status_code == 200
    assert queue.json()["pending_total"] == 1
    excuse_id = queue.json()["items"][0]["excuse_id"]

    reviewed = client.post(
        f"/api/v1/admin/excuses/{excuse_id}/review",
        json={"status": "approved", "note": "عذر مقبول"},
        headers=teacher_headers,
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["status"] == "approved"
    assert reviewed.json()["review_note"] == "عذر مقبول"

    # سجل الحضور تحوّل إلى «بعذر» بطريقة يدوية
    with SessionLocal() as db:
        record = db.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.session_id == uuid.UUID(world["session"]),
                AttendanceRecord.student_id == uuid.UUID(world["student"]),
            )
        )
        assert record is not None
        assert record.status == AttendanceStatus.EXCUSED
        assert record.method == AttendanceMethod.MANUAL
        assert record.marked_by == uuid.UUID(world["instructor"])

    # الطالب يرى القرار ووصلته إشعارات
    mine = client.get("/api/v1/excuses", headers=student_headers).json()["items"]
    assert mine[0]["status"] == "approved"
    assert mine[0]["review_note"] == "عذر مقبول"
    inbox = client.get("/api/v1/notifications", headers=student_headers).json()
    assert any(item["type"] == "excuse_reviewed" for item in inbox["items"])


def test_review_rejects_with_reason_and_no_attendance_change(client):
    world = build_world()
    student_headers = auth_headers(login(client, "S-200", "exc-dev-03"))
    teacher_headers = auth_headers(login(client, "T-100", "exc-dev-04"))
    session_id = _add_session(world, days_ago=1)

    created = _submit(client, student_headers, session_id)
    assert created.status_code == 200, created.text
    excuse_id = created.json()["excuse_id"]

    rejected = client.post(
        f"/api/v1/admin/excuses/{excuse_id}/review",
        json={"status": "rejected", "note": "التقرير غير واضح"},
        headers=teacher_headers,
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"

    with SessionLocal() as db:
        record = db.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.session_id == uuid.UUID(session_id),
                AttendanceRecord.student_id == uuid.UUID(world["other"]),
            )
        )
        assert record is None

    # لا تُقبل مراجعة ثانية
    again = client.post(
        f"/api/v1/admin/excuses/{excuse_id}/review",
        json={"status": "approved"},
        headers=teacher_headers,
    )
    assert again.status_code == 409


def test_excuse_window_and_duplicate_and_present_guard(client):
    world = build_world()
    student_headers = auth_headers(login(client, "S-100", "exc-dev-05"))

    old_session = _add_session(world, days_ago=30)
    late = _submit(client, student_headers, old_session)
    assert late.status_code == 400
    assert late.json()["code"] == "excuse_window_closed"

    first = _submit(client, student_headers, world["session"])
    assert first.status_code == 200
    duplicate = _submit(client, student_headers, world["session"])
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "excuse_pending"

    # طالب حاضر لا يستطيع رفع عذر
    present_session = _add_session(world, days_ago=2)
    with SessionLocal() as db:
        db.add(
            AttendanceRecord(
                session_id=uuid.UUID(present_session),
                student_id=uuid.UUID(world["student"]),
                status=AttendanceStatus.PRESENT,
                method=AttendanceMethod.QR,
            )
        )
        db.commit()
    blocked = _submit(client, student_headers, present_session)
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "not_absent"


def test_attachment_must_be_image_or_pdf(client):
    world = build_world()
    student_headers = auth_headers(login(client, "S-100", "exc-dev-06"))

    bad = client.post(
        "/api/v1/excuses",
        data={"session_id": world["session"], "reason": "عذر بمرفق غير مدعوم"},
        files={"file": ("note.txt", io.BytesIO(b"hello"), "text/plain")},
        headers=student_headers,
    )
    assert bad.status_code == 400
    assert bad.json()["code"] == "unsupported_file_type"

    ok = client.post(
        "/api/v1/excuses",
        data={"session_id": world["session"], "reason": "صورة تقرير طبي"},
        files={"file": ("report.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
        headers=student_headers,
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["attachment"]["name"] == "report.png"
    assert ok.json()["attachment"]["download_url"]


def test_students_and_outsider_staff_cannot_review(client):
    world = build_world()
    student_headers = auth_headers(login(client, "S-100", "exc-dev-07"))
    created = _submit(client, student_headers, world["session"])
    excuse_id = created.json()["excuse_id"]

    assert client.get("/api/v1/admin/excuses", headers=student_headers).status_code == 403

    # تدريسي آخر في القسم نفسه ليس صاحب المادة
    with SessionLocal() as db:
        other_teacher = User(
            university_id="T-200",
            full_name_ar="د. سارة الأخرى",
            role=UserRole.INSTRUCTOR,
            password_hash=hash_password(PASSWORD, rounds=4),
            status=UserStatus.ACTIVE,
            must_change_password=False,
        )
        db.add(other_teacher)
        db.flush()
        db.add(Staff(user_id=other_teacher.id, department_id=uuid.UUID(world["department"])))
        db.commit()

    outsider = auth_headers(login(client, "T-200", "exc-dev-08"))
    review = client.post(
        f"/api/v1/admin/excuses/{excuse_id}/review",
        json={"status": "approved"},
        headers=outsider,
    )
    assert review.status_code == 403
    assert review.json()["code"] == "not_offering_staff"


def test_student_can_withdraw_pending_excuse(client):
    world = build_world()
    headers = auth_headers(login(client, "S-100", "exc-dev-09"))
    excuse_id = _submit(client, headers, world["session"]).json()["excuse_id"]

    withdrawn = client.delete(f"/api/v1/excuses/{excuse_id}", headers=headers)
    assert withdrawn.status_code == 200
    assert client.get("/api/v1/excuses", headers=headers).json()["items"] == []
