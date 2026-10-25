# -*- coding: utf-8 -*-
"""اختبارات الحضور: QR متجدد، ربط جهاز، موقع، لحظي، إغلاق، وتعديل مدقَّق."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.models import AttendanceRecord, AuditLog, LectureSession
from app.models.enums import AttendanceStatus
from app.services.attendance import make_token, window_for
from world import auth_headers, build_world, login

INSIDE = {"lat": 31.9901, "lng": 44.9201, "accuracy_m": 12}
FAR = {"lat": 30.5, "lng": 44.0, "accuracy_m": 20}


def _open(client, world) -> dict:
    teacher = login(client, "T-100", "teacher-device-01")
    res = client.post(
        f"/api/v1/sessions/{world['session']}/open", headers=auth_headers(teacher)
    )
    assert res.status_code == 200, res.text
    return {"teacher": teacher, "body": res.json()}


def test_open_session_returns_rotating_qr(client):
    world = build_world()
    opened = _open(client, world)
    qr = opened["body"]["qr"]

    assert opened["body"]["status"] == "open"
    assert qr["rotation_s"] == 20
    assert 0 < qr["expires_in"] <= 20
    window, signature = qr["token"].split(".")
    assert int(window) > 0 and len(signature) == 16

    # فتح ثانٍ لا يغيّر الرمز (idempotent)
    again = client.post(
        f"/api/v1/sessions/{world['session']}/open",
        headers=auth_headers(opened["teacher"]),
    )
    assert again.status_code == 200
    assert again.json()["qr"]["token"].split(".")[0] == window


def test_scan_present_then_duplicate(client):
    world = build_world(start_offset_minutes=-3)
    opened = _open(client, world)
    student = login(client, "S-100", "student-device-01")

    payload = {
        "session_id": world["session"],
        "token": opened["body"]["qr"]["token"],
        "device_id": student["device_id"],
        "location": INSIDE,
    }
    first = client.post(
        "/api/v1/attendance/scan", json=payload, headers=auth_headers(student)
    )
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["status"] == "present"
    assert body["flagged"] is False

    duplicate = client.post(
        "/api/v1/attendance/scan", json=payload, headers=auth_headers(student)
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "already_registered"


def test_scan_rejects_invalid_and_stale_tokens(client):
    world = build_world()
    opened = _open(client, world)
    student = login(client, "S-100", "student-device-02")
    headers = auth_headers(student)

    bad = client.post(
        "/api/v1/attendance/scan",
        json={
            "session_id": world["session"],
            "token": "123.deadbeefdeadbeef",
            "device_id": student["device_id"],
            "location": INSIDE,
        },
        headers=headers,
    )
    assert bad.status_code == 400
    assert bad.json()["code"] == "invalid_token"

    with SessionLocal() as db:
        session = db.get(LectureSession, uuid.UUID(world["session"]))
        secret = session.secret
        old_window = window_for(datetime.now(timezone.utc), 20) - 2
        stale_token = make_token(secret, world["session"], old_window)

    stale = client.post(
        "/api/v1/attendance/scan",
        json={
            "session_id": world["session"],
            "token": stale_token,
            "device_id": student["device_id"],
            "location": INSIDE,
        },
        headers=headers,
    )
    assert stale.status_code == 410
    assert stale.json()["code"] == "token_expired"


def test_scan_requires_bound_device_and_enrollment(client):
    world = build_world()
    opened = _open(client, world)
    student = login(client, "S-100", "student-device-03")

    unknown_device = client.post(
        "/api/v1/attendance/scan",
        json={
            "session_id": world["session"],
            "token": opened["body"]["qr"]["token"],
            "device_id": "00000000-0000-0000-0000-000000000000",
            "location": INSIDE,
        },
        headers=auth_headers(student),
    )
    assert unknown_device.status_code == 403
    assert unknown_device.json()["code"] == "device_not_bound"

    # طالب غير مسجَّل في المادة
    other = login(client, "S-300", "student-device-04")
    not_enrolled = client.post(
        "/api/v1/attendance/scan",
        json={
            "session_id": world["session"],
            "token": opened["body"]["qr"]["token"],
            "device_id": other["device_id"],
            "location": INSIDE,
        },
        headers=auth_headers(other),
    )
    assert not_enrolled.status_code == 403
    assert not_enrolled.json()["code"] == "not_enrolled"


def test_scan_flags_outside_location(client):
    world = build_world()
    opened = _open(client, world)
    student = login(client, "S-100", "student-device-05")

    res = client.post(
        "/api/v1/attendance/scan",
        json={
            "session_id": world["session"],
            "token": opened["body"]["qr"]["token"],
            "device_id": student["device_id"],
            "location": FAR,
        },
        headers=auth_headers(student),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["flagged"] is True
    assert body["flag_reason"].startswith("outside_campus")


def test_late_after_grace(client):
    world = build_world(start_offset_minutes=-30)
    opened = _open(client, world)
    student = login(client, "S-100", "student-device-06")

    res = client.post(
        "/api/v1/attendance/scan",
        json={
            "session_id": world["session"],
            "token": opened["body"]["qr"]["token"],
            "device_id": student["device_id"],
            "location": INSIDE,
        },
        headers=auth_headers(student),
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "late"


def test_live_list_and_close_marks_absent(client):
    world = build_world()
    opened = _open(client, world)
    teacher_headers = auth_headers(opened["teacher"])
    student = login(client, "S-100", "student-device-07")

    client.post(
        "/api/v1/attendance/scan",
        json={
            "session_id": world["session"],
            "token": opened["body"]["qr"]["token"],
            "device_id": student["device_id"],
            "location": INSIDE,
        },
        headers=auth_headers(student),
    )

    live = client.get(
        f"/api/v1/sessions/{world['session']}/live", headers=teacher_headers
    )
    assert live.status_code == 200
    body = live.json()
    assert body["counts"].get("present") == 1
    statuses = {row["university_id"]: row["status"] for row in body["students"]}
    assert statuses["S-100"] == "present"
    assert statuses["S-200"] is None

    closed = client.post(
        f"/api/v1/sessions/{world['session']}/close", headers=teacher_headers
    )
    assert closed.status_code == 200
    assert closed.json()["absent_marked"] == 1
    assert closed.json()["counts"]["absent"] == 1

    report = client.get(
        f"/api/v1/offerings/{world['offering']}/attendance/report",
        headers=teacher_headers,
    )
    assert report.status_code == 200
    rows = {row["university_id"]: row for row in report.json()["students"]}
    assert rows["S-100"]["present"] == 1
    assert rows["S-100"]["percentage"] == 100.0
    assert rows["S-200"]["absent"] == 1
    assert rows["S-200"]["percentage"] == 0.0

    summary = client.get("/api/v1/attendance/summary", headers=auth_headers(student))
    assert summary.status_code == 200
    item = summary.json()["items"][0]
    assert item["present"] == 1 and item["percentage"] == 100.0


def test_manual_edit_is_audited_and_forbidden_for_student(client):
    world = build_world()
    opened = _open(client, world)
    teacher_headers = auth_headers(opened["teacher"])
    student = login(client, "S-100", "student-device-08")

    scan = client.post(
        "/api/v1/attendance/scan",
        json={
            "session_id": world["session"],
            "token": opened["body"]["qr"]["token"],
            "device_id": student["device_id"],
            "location": INSIDE,
        },
        headers=auth_headers(student),
    )
    record_id = scan.json()["attendance_id"]

    forbidden = client.patch(
        f"/api/v1/attendance/{record_id}",
        json={"status": "excused"},
        headers=auth_headers(student),
    )
    assert forbidden.status_code == 403

    edited = client.patch(
        f"/api/v1/attendance/{record_id}",
        json={"status": "excused", "reason": "عذر صحي"},
        headers=teacher_headers,
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["status"] == "excused"

    with SessionLocal() as db:
        row = db.get(AttendanceRecord, uuid.UUID(record_id))
        assert row.status == AttendanceStatus.EXCUSED
        audit = db.scalars(
            select(AuditLog).where(
                AuditLog.action == "attendance_updated",
                AuditLog.entity_id == record_id,
            )
        ).first()
        assert audit is not None
        assert audit.before["status"] == "present"
        assert audit.after["status"] == "excused"


def test_student_cannot_open_session(client):
    world = build_world()
    student = login(client, "S-100", "student-device-09")
    res = client.post(
        f"/api/v1/sessions/{world['session']}/open", headers=auth_headers(student)
    )
    assert res.status_code == 403
    assert res.json()["code"] == "not_offering_staff"
