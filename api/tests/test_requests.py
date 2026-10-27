# -*- coding: utf-8 -*-
"""اختبارات الطلبات والمحادثة مع القسم: الإنشاء، الرؤية، الرد، والحالة."""
import uuid

from app.db import SessionLocal
from app.models import Staff, User
from app.models.enums import UserRole, UserStatus
from app.security import hash_password
from world import PASSWORD, auth_headers, build_world, login


def _head(world: dict) -> None:
    with SessionLocal() as db:
        head = User(
            university_id="HEAD-200",
            full_name_ar="رئيس قسم الحاسوب",
            role=UserRole.DEPARTMENT_HEAD,
            password_hash=hash_password(PASSWORD, rounds=4),
            status=UserStatus.ACTIVE,
            must_change_password=False,
        )
        db.add(head)
        db.flush()
        db.add(Staff(user_id=head.id, department_id=uuid.UUID(world["department"])))
        db.commit()


def _create(client, headers, **overrides):
    payload = {
        "category": "academic",
        "subject": "طلب تأجيل اختبار",
        "body": "أرجو تأجيل اختبار المادة بسبب ظرف عائلي.",
    }
    payload.update(overrides)
    return client.post("/api/v1/requests", json=payload, headers=headers)


def test_student_creates_request_and_head_replies(client):
    world = build_world()
    _head(world)
    student = auth_headers(login(client, "S-100", "req-dev-01"))
    head = auth_headers(login(client, "HEAD-200", "req-dev-02"))

    created = _create(client, student)
    assert created.status_code == 200, created.text
    payload = created.json()
    assert payload["status"] == "open"
    assert payload["category_label"] == "مسألة أكاديمية"
    assert len(payload["messages"]) == 1
    request_id = payload["request_id"]

    # رئيس القسم يرى طلبات قسمه
    queue = client.get("/api/v1/requests", headers=head).json()["items"]
    assert [item["request_id"] for item in queue] == [request_id]

    reply = client.post(
        f"/api/v1/requests/{request_id}/messages",
        json={"body": "تم تحويل الطلب إلى لجنة الاختبارات."},
        headers=head,
    )
    assert reply.status_code == 200
    assert reply.json()["status"] == "in_progress"
    assert len(reply.json()["messages"]) == 2

    # الطالب استلم إشعار الرد
    inbox = client.get("/api/v1/notifications", headers=student).json()["items"]
    assert any(item["type"] == "request_message" for item in inbox)

    # رد الطالب يُشعر رئيس القسم
    answer = client.post(
        f"/api/v1/requests/{request_id}/messages",
        json={"body": "شكراً، أرفقت التقرير الطبي في الأعذار."},
        headers=student,
    )
    assert answer.status_code == 200
    head_inbox = client.get("/api/v1/notifications", headers=head).json()["items"]
    assert any(item["type"] == "request_message" for item in head_inbox)


def test_request_visibility_and_assignment_flow(client):
    world = build_world()
    _head(world)
    student = auth_headers(login(client, "S-100", "req-dev-03"))
    other_student = auth_headers(login(client, "S-200", "req-dev-04"))
    head = auth_headers(login(client, "HEAD-200", "req-dev-05"))
    teacher = auth_headers(login(client, "T-100", "req-dev-06"))

    request_id = _create(client, student).json()["request_id"]

    # طالب آخر لا يرى الطلب
    assert client.get(f"/api/v1/requests/{request_id}", headers=other_student).status_code == 404

    # التدريسي غير المسنَد لا يراه
    assert client.get(f"/api/v1/requests/{request_id}", headers=teacher).status_code == 403
    assert client.get("/api/v1/requests", headers=teacher).json()["items"] == []

    # الإسناد إلى التدريسي
    assigned = client.patch(
        f"/api/v1/admin/requests/{request_id}",
        json={"assigned_to": world["instructor"], "status": "in_progress"},
        headers=head,
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["assigned_to"] == world["instructor"]

    assert client.get(f"/api/v1/requests/{request_id}", headers=teacher).status_code == 200
    teacher_queue = client.get("/api/v1/requests", headers=teacher).json()["items"]
    assert [item["request_id"] for item in teacher_queue] == [request_id]

    resolved = client.patch(
        f"/api/v1/admin/requests/{request_id}",
        json={"status": "resolved"},
        headers=teacher,
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"

    # الطلب المغلق لا يقبل رسائل جديدة
    closed = client.post(
        f"/api/v1/requests/{request_id}/messages",
        json={"body": "استفسار أخير"},
        headers=student,
    )
    assert closed.status_code == 409


def test_request_validation_and_role_limits(client):
    build_world()
    student = auth_headers(login(client, "S-100", "req-dev-07"))
    teacher = auth_headers(login(client, "T-100", "req-dev-08"))

    assert _create(client, student, category="unknown").status_code == 400
    assert _create(client, student, subject="ab").status_code == 422

    # التدريسي لا يفتح طلبات الطلبة
    denied = _create(client, teacher)
    assert denied.status_code == 403
    assert denied.json()["code"] == "not_a_student"

    # الطالب لا يغيّر حالة الطلب
    request_id = _create(client, student).json()["request_id"]
    patch = client.patch(
        f"/api/v1/admin/requests/{request_id}", json={"status": "closed"}, headers=student
    )
    assert patch.status_code == 403
