# -*- coding: utf-8 -*-
"""اختبارات الجدول: توليد الجلسات، كشف التعارضات، القراءة، والتغييرات المؤرخة."""
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Course, CourseOffering, Group, LectureSession, Room, TimetableSlot
from app.models.enums import SessionKind, StudyType
from world import auth_headers, build_world, login

BAGHDAD = timezone(timedelta(hours=3))


def _add_second_offering(world, *, group_name: str = "B", code: str = "CS102", instructor=None, group_id=None):
    """مادة/شعبة ثانية لاختبار التعارضات (قاعة/شعبة/تدريسي)."""
    with SessionLocal() as db:
        term_id = uuid.UUID(world["term"])
        dept_id = uuid.UUID(world["department"])
        if group_id is not None:
            group = db.get(Group, uuid.UUID(group_id))
        else:
            group = Group(
                department_id=dept_id,
                stage=1,
                name=group_name,
                study_type=StudyType.MORNING,
                term_id=term_id,
            )
            db.add(group)
            db.flush()
        course = Course(
            code=code,
            name_ar="مادة ثانية",
            department_id=dept_id,
            stage=1,
            units=2,
            kind=SessionKind.THEORY,
        )
        db.add(course)
        db.flush()
        offering = CourseOffering(
            course_id=course.id,
            term_id=term_id,
            group_id=group.id,
            instructor_id=instructor,
            session_kind=SessionKind.THEORY,
        )
        db.add(offering)
        db.commit()
        return str(offering.id), str(group.id)


def _admin_headers(client) -> dict:
    return auth_headers(login(client, "ADMIN-9", "admin-device-01"))


def _today_weekday() -> int:
    return (datetime.now(BAGHDAD).weekday() + 1) % 7


def test_create_slot_generates_sessions(client):
    world = build_world()
    headers = _admin_headers(client)

    weekday = (_today_weekday() + 2) % 7
    res = client.post(
        "/api/v1/admin/timetable/slots",
        json={
            "offering_id": world["offering"],
            "weekday": weekday,
            "start_time": "08:00:00",
            "end_time": "09:30:00",
            "room_id": world["room"],
            "kind": "theory",
        },
        headers=headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["sessions_created"] >= 15

    with SessionLocal() as db:
        count = db.scalar(
            select(LectureSession).where(
                LectureSession.slot_id == uuid.UUID(body["slot_id"])
            )
        )
        assert count is not None


def test_room_conflict_detected(client):
    world = build_world()
    headers = _admin_headers(client)
    second_offering, _ = _add_second_offering(world, group_name="B", code="CS102")

    res = client.post(
        "/api/v1/admin/timetable/slots",
        json={
            "offering_id": second_offering,
            "weekday": _today_weekday(),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "room_id": world["room"],
            "kind": "theory",
        },
        headers=headers,
    )
    # الجلسة الأصلية في العالم لها نفس اليوم والوقت الحالي؛ نقارن بالتداخل الفعلي
    if res.status_code == 200:
        # لا تداخل زمني مع وقت الجلسة الأصلية → ننشئ تداخلاً مؤكداً
        with SessionLocal() as db:
            slot = db.get(TimetableSlot, uuid.UUID(world["slot"]))
            start = slot.start_time
            end = slot.end_time
        res = client.post(
            "/api/v1/admin/timetable/slots",
            json={
                "offering_id": second_offering,
                "weekday": _today_weekday(),
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "room_id": world["room"],
                "kind": "theory",
            },
            headers=headers,
        )
    assert res.status_code == 409, res.text
    assert res.json()["code"] == "room_conflict"


def test_group_conflict_detected(client):
    world = build_world()
    headers = _admin_headers(client)
    # نفس الشعبة، قاعة أخرى، بلا تدريسي → يبقى تعارض الشعبة
    second_offering, _ = _add_second_offering(
        world, group_id=world["group"], code="CS103"
    )

    with SessionLocal() as db:
        slot = db.get(TimetableSlot, uuid.UUID(world["slot"]))
        start, end = slot.start_time, slot.end_time
        room2 = Room(name="قاعة 202", building="مبنى ب")
        db.add(room2)
        db.commit()
        room2_id = str(room2.id)

    res = client.post(
        "/api/v1/admin/timetable/slots",
        json={
            "offering_id": second_offering,
            "weekday": _today_weekday(),
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "room_id": room2_id,
            "kind": "theory",
        },
        headers=headers,
    )
    assert res.status_code == 409, res.text
    assert res.json()["code"] == "group_conflict"


def test_timetable_read_for_student(client):
    world = build_world()
    student = login(client, "S-100", "student-device-tt")
    today = datetime.now(BAGHDAD).date()

    res = client.get(
        "/api/v1/timetable",
        params={"from": today.isoformat(), "to": (today + timedelta(days=7)).isoformat()},
        headers=auth_headers(student),
    )
    assert res.status_code == 200, res.text
    items = res.json()["items"]
    assert any(item["course_code"] == "CS101" for item in items)
    assert items[0]["status"] == "scheduled"


def test_change_cancel_and_listing(client):
    world = build_world()
    headers = _admin_headers(client)
    today = datetime.now(BAGHDAD).date()

    cancel = client.post(
        "/api/v1/admin/timetable/changes",
        json={
            "slot_id": world["slot"],
            "date": today.isoformat(),
            "type": "cancel",
            "reason": "عطلة رسمية",
        },
        headers=headers,
    )
    assert cancel.status_code == 200, cancel.text

    with SessionLocal() as db:
        session = db.get(LectureSession, uuid.UUID(world["session"]))
        assert session.status.value == "cancelled"

    student = login(client, "S-100", "student-device-tt2")
    changes = client.get(
        "/api/v1/timetable/changes",
        params={"from": today.isoformat(), "to": today.isoformat()},
        headers=auth_headers(student),
    )
    assert changes.status_code == 200
    assert changes.json()["items"][0]["type"] == "cancel"


def test_change_move_requires_new_start(client):
    world = build_world()
    headers = _admin_headers(client)
    today = datetime.now(BAGHDAD).date()

    res = client.post(
        "/api/v1/admin/timetable/changes",
        json={"slot_id": world["slot"], "date": today.isoformat(), "type": "move"},
        headers=headers,
    )
    assert res.status_code == 400
    assert res.json()["code"] == "missing_new_start"


def test_admin_rooms_listing(client):
    world = build_world()
    headers = _admin_headers(client)

    res = client.get("/api/v1/admin/timetable/rooms", headers=headers)
    assert res.status_code == 200, res.text
    items = res.json()["items"]
    names = {item["name"] for item in items}
    assert "قاعة 101" in names
    room = next(item for item in items if item["name"] == "قاعة 101")
    assert room["room_id"] == world["room"]
    assert room["radius_m"] == 100


def test_admin_slots_listing_with_offering_filter(client):
    world = build_world()
    headers = _admin_headers(client)

    res = client.get("/api/v1/admin/timetable/slots", headers=headers)
    assert res.status_code == 200, res.text
    items = res.json()["items"]
    assert len(items) == 1
    slot = items[0]
    assert slot["slot_id"] == world["slot"]
    assert slot["offering_id"] == world["offering"]
    assert slot["course_code"] == "CS101"
    assert slot["group_name"] == "A"
    assert slot["room_name"] == "قاعة 101"
    assert slot["instructor_name_ar"] == "د. أحمد التدريسي"
    assert slot["start_time"].startswith("10:00")

    filtered = client.get(
        "/api/v1/admin/timetable/slots",
        params={"offering_id": world["offering"]},
        headers=headers,
    )
    assert filtered.status_code == 200
    assert len(filtered.json()["items"]) == 1

    other = client.get(
        "/api/v1/admin/timetable/slots",
        params={"offering_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert other.status_code == 200
    assert other.json()["items"] == []


def test_timetable_items_expose_slot_id(client):
    world = build_world()
    student = login(client, "S-100", "student-device-tt4")
    today = datetime.now(BAGHDAD).date()

    res = client.get(
        "/api/v1/timetable",
        params={"from": today.isoformat(), "to": today.isoformat()},
        headers=auth_headers(student),
    )
    assert res.status_code == 200, res.text
    items = res.json()["items"]
    assert items and items[0]["slot_id"] == world["slot"]


def test_timetable_admin_read_requires_manager_role(client):
    build_world()
    student = login(client, "S-100", "student-device-tt5")
    headers = auth_headers(student)

    assert client.get("/api/v1/admin/timetable/rooms", headers=headers).status_code == 403
    assert client.get("/api/v1/admin/timetable/slots", headers=headers).status_code == 403
