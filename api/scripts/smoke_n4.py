# -*- coding: utf-8 -*-
"""فحص شامل لدورة N4 (لوحة التحكم) عبر HTTP حقيقي — بعد تشغيل الخدمة على 8000.

    python scripts/smoke_n4.py

يفترض بيانات العرض من `scripts/demo_seed.py` وحساب المدير من `create_admin.py`.
يغطي المسارات التي تستدعيها شاشات اللوحة الثلاث:
الطلاب (قائمة + قالب) · الجدول (قاعات/حصص + تعارض + تغيير مؤرّخ) ·
الدرجات (تقييم + إدخال + نشر + منع التعديل بعد النشر + تصدير Excel).
قابل للتكرار: يعيد استخدام ما أنشأه في تشغيل سابق بدل تكراره.
"""
import os
import sys
from datetime import datetime, timedelta, timezone

import httpx

BASE = os.environ.get("SMOKE_BASE", "http://127.0.0.1:8000/api/v1")
ADMIN = ("ADMIN-001", "Admin#2026", "smoke-n4-admin")
TEACHER = ("T-100", "Test#12345", "smoke-n4-teacher")
STUDENT = ("S-100", "Test#12345", "smoke-n4-student")
BAGHDAD = timezone(timedelta(hours=3))


def login(client: httpx.Client, credentials: tuple[str, str, str]) -> dict:
    university_id, password, device = credentials
    res = client.post(
        f"{BASE}/auth/login",
        json={
            "university_id": university_id,
            "password": password,
            "device": {"fingerprint": device, "model": "Smoke N4"},
        },
    )
    res.raise_for_status()
    return res.json()


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def expect(res: httpx.Response, status: int, label: str) -> dict:
    assert res.status_code == status, f"{label}: {res.status_code} {res.text}"
    return res.json() if res.content else {}


def pick_offering(client: httpx.Client, token: str) -> dict:
    res = client.get(f"{BASE}/offerings", headers=headers(token))
    expect(res, 200, "offerings")
    items = res.json()["items"]
    assert items, "لا مواد — شغّل scripts/demo_seed.py"
    return next((item for item in items if item["course_code"] == "CS101"), items[0])


def ensure_assessment(client: httpx.Client, token: str, offering_id: str) -> dict:
    matrix = expect(
        client.get(f"{BASE}/offerings/{offering_id}/grades", headers=headers(token)),
        200,
        "grades matrix",
    )
    for row in matrix["assessments"]:
        if row["name"] == "سموك N4":
            return row
    created = expect(
        client.post(
            f"{BASE}/assessments",
            json={
                "offering_id": offering_id,
                "name": "سموك N4",
                "kind": "quiz",
                "max_score": 20,
                "weight": 5,
            },
            headers=headers(token),
        ),
        200,
        "create assessment",
    )
    return created


def ensure_room(client: httpx.Client, token: str) -> dict:
    rooms = expect(
        client.get(f"{BASE}/admin/timetable/rooms", headers=headers(token)),
        200,
        "rooms",
    )["items"]
    assert any(room["name"] == "قاعة 108" for room in rooms), rooms
    existing = next((room for room in rooms if room["name"] == "قاعة سموك N4"), None)
    if existing is not None:
        return existing
    return expect(
        client.post(
            f"{BASE}/admin/timetable/rooms",
            json={"name": "قاعة سموك N4", "building": "مبنى الفحص", "radius_m": 80},
            headers=headers(token),
        ),
        200,
        "create room",
    )


def ensure_slot(client: httpx.Client, token: str, offering_id: str, room_id: str) -> dict:
    slots = expect(
        client.get(f"{BASE}/admin/timetable/slots", headers=headers(token)),
        200,
        "slots",
    )["items"]
    for slot in slots:
        if slot["room_id"] == room_id and slot["offering_id"] == offering_id:
            return slot
    created = expect(
        client.post(
            f"{BASE}/admin/timetable/slots",
            json={
                "offering_id": offering_id,
                "weekday": 2,
                "start_time": "08:00:00",
                "end_time": "09:30:00",
                "room_id": room_id,
                "kind": "theory",
            },
            headers=headers(token),
        ),
        200,
        "create slot",
    )
    return {**created, "weekday": 2, "start_time": "08:00:00"}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    with httpx.Client(timeout=60) as client:
        admin_token = login(client, ADMIN)["access_token"]
        teacher_token = login(client, TEACHER)["access_token"]
        student_token = login(client, STUDENT)["access_token"]
        print("logins ok")

        # 1) الطلاب: قائمة + قالب Excel
        students = expect(
            client.get(
                f"{BASE}/admin/students",
                params={"limit": 5, "study_type": "morning", "stage": 1},
                headers=headers(admin_token),
            ),
            200,
            "students list",
        )
        assert students["items"], "قائمة الطلاب فارغة"
        template = client.get(f"{BASE}/admin/students/template", headers=headers(admin_token))
        assert template.status_code == 200 and template.content[:2] == b"PK", template.status_code
        print("students:", students["total"], "| template bytes:", len(template.content))

        # 2) الجدول: قاعة، تعارض، حصة، تغيير مؤرّخ
        room = ensure_room(client, admin_token)
        room_id = room.get("room_id", room.get("id"))
        offering = pick_offering(client, admin_token)
        slot = ensure_slot(client, admin_token, offering["offering_id"], room_id)

        conflict = client.post(
            f"{BASE}/admin/timetable/slots",
            json={
                "offering_id": offering["offering_id"],
                "weekday": 2,
                "start_time": "08:30:00",
                "end_time": "09:00:00",
                "room_id": room_id,
                "kind": "theory",
            },
            headers=headers(admin_token),
        )
        conflict_body = expect(conflict, 409, "room conflict")
        assert conflict_body["code"] == "room_conflict", conflict_body
        print("conflict detected:", conflict_body["message_ar"])

        today = datetime.now(BAGHDAD).date()
        sessions = expect(
            client.get(
                f"{BASE}/timetable",
                params={"from": today.isoformat(), "to": (today + timedelta(days=13)).isoformat()},
                headers=headers(admin_token),
            ),
            200,
            "timetable",
        )["items"]
        target = next(item for item in sessions if item["slot_id"] == slot["slot_id"])
        changes = expect(
            client.get(f"{BASE}/timetable/changes", headers=headers(admin_token)),
            200,
            "changes",
        )["items"]
        if not any(row["date"] == target["date"] and row["type"] == "cancel" for row in changes):
            change = expect(
                client.post(
                    f"{BASE}/admin/timetable/changes",
                    json={
                        "slot_id": slot["slot_id"],
                        "date": target["date"],
                        "type": "cancel",
                        "reason": "سموك N4",
                    },
                    headers=headers(admin_token),
                ),
                200,
                "create change",
            )
            print("change recorded:", change["type"], "on", target["date"])
        else:
            print("change already recorded on", target["date"])

        # 3) الدرجات: إدخال ← نشر ← منع التعديل ← تصدير
        assessment = ensure_assessment(client, admin_token, offering["offering_id"])
        matrix = expect(
            client.get(
                f"{BASE}/offerings/{offering['offering_id']}/grades",
                headers=headers(admin_token),
            ),
            200,
            "matrix reload",
        )
        rows = [
            {"student_id": student["student_id"], "score": 18}
            for student in matrix["students"]
        ]
        if not assessment["is_published"]:
            saved = expect(
                client.post(
                    f"{BASE}/assessments/{assessment['assessment_id']}/grades",
                    json={"rows": rows},
                    headers=headers(admin_token),
                ),
                200,
                "save grades",
            )
            print("grades saved:", saved)

            forbidden = client.post(
                f"{BASE}/assessments/{assessment['assessment_id']}/publish",
                headers=headers(teacher_token),
            )
            forbidden_body = expect(forbidden, 403, "publish by instructor")
            assert forbidden_body["code"] == "not_college_admin", forbidden_body

            published = expect(
                client.post(
                    f"{BASE}/assessments/{assessment['assessment_id']}/publish",
                    headers=headers(admin_token),
                ),
                200,
                "publish",
            )
            print("published | notified:", published["notified"])

        locked = client.post(
            f"{BASE}/assessments/{assessment['assessment_id']}/grades",
            json={"rows": rows},
            headers=headers(admin_token),
        )
        locked_body = expect(locked, 409, "edit after publish")
        assert locked_body["code"] == "assessment_published", locked_body
        print("edit blocked after publish:", locked_body["message_ar"])

        export = client.get(
            f"{BASE}/offerings/{offering['offering_id']}/grades/export",
            headers=headers(admin_token),
        )
        assert export.status_code == 200 and export.content[:2] == b"PK", export.status_code
        assert "spreadsheetml" in export.headers["content-type"], export.headers
        print("export bytes:", len(export.content))

        # 4) الطالب يرى المنشور فقط
        student_grades = expect(
            client.get(f"{BASE}/grades", headers=headers(student_token)),
            200,
            "student grades",
        )["items"]
        seen = [
            row
            for course in student_grades
            for row in course["assessments"]
            if row["assessment_id"] == assessment["assessment_id"]
        ]
        assert seen and seen[0]["score"] == 18.0, seen
        print("student sees score:", seen[0]["score"])

        print("\nN4 smoke: كل الخطوات نجحت")


if __name__ == "__main__":
    main()
