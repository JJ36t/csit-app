# -*- coding: utf-8 -*-
"""اختبارات مواد المستخدم: نطاق الرؤية حسب الدور، الحقول، وربط الجدول بالعرض."""
from world import auth_headers, build_world, login


def _items(client, headers) -> list:
    res = client.get("/api/v1/offerings", headers=headers)
    assert res.status_code == 200, res.text
    return res.json()["items"]


def test_student_sees_only_enrolled_offering(client):
    world = build_world()
    student = login(client, "S-100", "student-device-of01")

    items = _items(client, auth_headers(student))
    assert [item["offering_id"] for item in items] == [world["offering"]]
    assert items[0]["course_code"] == "CS101"

    # طالب غير مسجَّل في أي مادة: قائمة فارغة
    outsider = login(client, "S-300", "student-device-of02")
    assert _items(client, auth_headers(outsider)) == []


def test_instructor_sees_same_offering_with_fields(client):
    world = build_world()
    teacher = login(client, "T-100", "teacher-device-of01")

    items = _items(client, auth_headers(teacher))
    assert len(items) == 1
    item = items[0]
    assert item["offering_id"] == world["offering"]
    assert item["course_code"] == "CS101"
    assert item["course_name_ar"] == "مقدمة في علوم الحاسوب"
    assert item["kind"] == "theory"
    assert item["stage"] == 1
    assert item["group_name"] == "A"
    assert item["study_type"] == "morning"
    assert item["instructor_name_ar"] == "د. أحمد التدريسي"

    # الطالب يرى المادة نفسها فقط، بلا تكرار
    student = login(client, "S-100", "student-device-of03")
    student_items = _items(client, auth_headers(student))
    assert [row["offering_id"] for row in student_items] == [item["offering_id"]]


def test_timetable_items_carry_offering_id_and_endpoint_requires_auth(client):
    world = build_world()
    student = login(client, "S-100", "student-device-of04")

    res = client.get("/api/v1/timetable", headers=auth_headers(student))
    assert res.status_code == 200, res.text
    items = res.json()["items"]
    assert items
    assert all(item["offering_id"] == world["offering"] for item in items)

    # بلا رمز: 401 برسالة عربية
    anonymous = client.get("/api/v1/offerings")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "not_authenticated"
