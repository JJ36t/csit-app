# -*- coding: utf-8 -*-
"""اختبارات صندوق الإشعارات ورمز FCM (N3)."""
import uuid

from sqlalchemy import select

from app.db import SessionLocal
from app.models import FcmToken
from world import auth_headers, build_world, login


def test_inbox_gets_announcement_notifications_and_read_all_clears(client):
    build_world()
    admin = auth_headers(login(client, "ADMIN-9", "notif-dev-01"))
    student_login = login(client, "S-100", "notif-dev-02")
    student = auth_headers(student_login)

    empty = client.get("/api/v1/notifications", headers=student).json()
    assert empty["items"] == []
    assert empty["unread_count"] == 0

    client.post(
        "/api/v1/admin/announcements",
        json={"scope": "college", "title": "إشعار", "body": "محتوى"},
        headers=admin,
    )

    inbox = client.get("/api/v1/notifications", headers=student).json()
    assert inbox["unread_count"] == 1
    assert inbox["items"][0]["type"] == "announcement"

    marked = client.post("/api/v1/notifications/read-all", headers=student).json()
    assert marked["unread_count"] == 0

    assert client.get("/api/v1/notifications?unread_only=true", headers=student).json()[
        "items"
    ] == []


def test_single_notification_read_and_ownership(client):
    build_world()
    admin = auth_headers(login(client, "ADMIN-9", "notif-dev-03"))
    student = auth_headers(login(client, "S-100", "notif-dev-04"))
    other = auth_headers(login(client, "S-200", "notif-dev-05"))

    client.post(
        "/api/v1/admin/announcements",
        json={"scope": "college", "title": "إشعار", "body": "محتوى"},
        headers=admin,
    )
    notification_id = client.get("/api/v1/notifications", headers=student).json()["items"][0][
        "notification_id"
    ]

    assert (
        client.post(f"/api/v1/notifications/{notification_id}/read", headers=other).status_code
        == 404
    )

    read = client.post(f"/api/v1/notifications/{notification_id}/read", headers=student)
    assert read.status_code == 200
    assert client.get("/api/v1/notifications", headers=student).json()["unread_count"] == 0


def test_fcm_token_registration_requires_own_active_device(client):
    build_world()
    student_login = login(client, "S-100", "notif-dev-06")
    student = auth_headers(student_login)

    ok = client.put(
        "/api/v1/devices/fcm-token",
        json={"token": "fcm-token-abcdef-123456", "device_id": student_login["device_id"]},
        headers=student,
    )
    assert ok.status_code == 200, ok.text

    with SessionLocal() as db:
        tokens = list(db.scalars(select(FcmToken)))
    assert len(tokens) == 1
    assert tokens[0].token == "fcm-token-abcdef-123456"

    wrong_device = client.put(
        "/api/v1/devices/fcm-token",
        json={"token": "fcm-token-other-999999", "device_id": str(uuid.uuid4())},
        headers=student,
    )
    assert wrong_device.status_code == 403
    assert wrong_device.json()["code"] == "device_not_bound"
