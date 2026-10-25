# -*- coding: utf-8 -*-
"""اختبارات الإعلانات (N3): النطاق والصلاحيات والجدولة وعلامة القراءة."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Announcement, Staff, User
from app.models.enums import UserRole, UserStatus
from app.security import hash_password
from world import PASSWORD, auth_headers, build_world, login


def _create(client, headers, **overrides):
    payload = {
        "scope": "college",
        "title": "إعلان تجريبي",
        "body": "نص الإعلان التجريبي",
    }
    payload.update(overrides)
    return client.post("/api/v1/admin/announcements", json=payload, headers=headers)


def test_college_announcement_visible_to_students_and_restricted_to_admin(client):
    build_world()
    admin = auth_headers(login(client, "ADMIN-9", "ann-dev-01"))
    teacher = auth_headers(login(client, "T-100", "ann-dev-02"))
    student = auth_headers(login(client, "S-100", "ann-dev-03"))

    forbidden = _create(client, teacher)
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "not_allowed_scope"

    created = _create(client, admin, title="عطلة رسمية", body="تتوقف المحاضرات يوم الخميس")
    assert created.status_code == 200, created.text
    assert created.json()["notified"] >= 1

    feed = client.get("/api/v1/announcements", headers=student)
    assert feed.status_code == 200
    items = feed.json()["items"]
    assert [item["title"] for item in items] == ["عطلة رسمية"]
    assert items[0]["is_read"] is False


def test_scheduled_announcement_hidden_until_publish_time(client):
    build_world()
    admin = auth_headers(login(client, "ADMIN-9", "ann-dev-04"))
    student = auth_headers(login(client, "S-100", "ann-dev-05"))

    future = datetime.now(timezone.utc) + timedelta(hours=2)
    created = _create(client, admin, title="إعلان مجدول", publish_at=future.isoformat())
    assert created.status_code == 200
    announcement_id = created.json()["announcement_id"]

    assert client.get("/api/v1/announcements", headers=student).json()["items"] == []

    # تحريك وقت النشر إلى الماضي (كأن الجدولة حان وقتها)
    with SessionLocal() as db:
        row = db.get(Announcement, __import__("uuid").UUID(announcement_id))
        row.publish_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()

    titles = [
        item["title"]
        for item in client.get("/api/v1/announcements", headers=student).json()["items"]
    ]
    assert "إعلان مجدول" in titles


def test_department_head_can_post_and_group_scope_is_filtered(client):
    world = build_world()

    # رئيس قسم على قسم علوم الحاسوب
    with SessionLocal() as db:
        head = User(
            university_id="HEAD-100",
            full_name_ar="رئيس القسم",
            role=UserRole.DEPARTMENT_HEAD,
            password_hash=hash_password(PASSWORD, rounds=4),
            status=UserStatus.ACTIVE,
            must_change_password=False,
        )
        db.add(head)
        db.flush()
        db.add(Staff(user_id=head.id, department_id=__import__("uuid").UUID(world["department"])))
        db.commit()

    head_headers = auth_headers(login(client, "HEAD-100", "ann-dev-06"))
    student = auth_headers(login(client, "S-100", "ann-dev-07"))
    teacher = auth_headers(login(client, "T-100", "ann-dev-08"))

    forbidden = _create(
        client, teacher, scope="department", scope_id=world["department"], title="قسمي"
    )
    assert forbidden.status_code == 403

    created = _create(
        client,
        head_headers,
        scope="department",
        scope_id=world["department"],
        title="إعلان القسم",
    )
    assert created.status_code == 200, created.text

    # إعلان شعبة أخرى (لا تضم الطالب) لا يظهر له
    with SessionLocal() as db:
        from app.models import Group
        from app.models.enums import StudyType

        other_group = Group(
            department_id=__import__("uuid").UUID(world["department"]),
            stage=2,
            name="B",
            study_type=StudyType.MORNING,
            term_id=__import__("uuid").UUID(world["term"]),
        )
        db.add(other_group)
        db.commit()
        other_group_id = str(other_group.id)

    other = _create(
        client,
        head_headers,
        scope="group",
        scope_id=other_group_id,
        title="إعلان شعبة أخرى",
    )
    assert other.status_code == 200

    titles = [
        item["title"]
        for item in client.get("/api/v1/announcements", headers=student).json()["items"]
    ]
    assert "إعلان القسم" in titles
    assert "إعلان شعبة أخرى" not in titles


def test_reading_an_announcement_is_idempotent(client):
    build_world()
    admin = auth_headers(login(client, "ADMIN-9", "ann-dev-09"))
    student = auth_headers(login(client, "S-100", "ann-dev-10"))

    created = _create(client, admin, title="إعلان للقراءة").json()
    announcement_id = created["announcement_id"]

    first = client.post(f"/api/v1/announcements/{announcement_id}/read", headers=student)
    assert first.status_code == 200
    second = client.post(f"/api/v1/announcements/{announcement_id}/read", headers=student)
    assert second.status_code == 200

    item = client.get("/api/v1/announcements", headers=student).json()["items"][0]
    assert item["is_read"] is True
