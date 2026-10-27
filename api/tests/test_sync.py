# -*- coding: utf-8 -*-
"""اختبارات المزامنة الجزئية (updated_since) للإعلانات والإشعارات والمواد."""
from datetime import datetime, timedelta, timezone

from world import auth_headers, build_world, login


def _future() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()


def _past() -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()


def test_announcements_delta_sync(client):
    build_world()
    admin = auth_headers(login(client, "ADMIN-9", "sync-dev-01"))
    student = auth_headers(login(client, "S-100", "sync-dev-02"))

    client.post(
        "/api/v1/admin/announcements",
        json={"scope": "college", "title": "خبر", "body": "نص"},
        headers=admin,
    )

    full = client.get("/api/v1/announcements", headers=student).json()
    assert len(full["items"]) == 1
    assert full["server_time"]

    nothing = client.get(
        "/api/v1/announcements", params={"updated_since": _future()}, headers=student
    ).json()
    assert nothing["items"] == []

    delta = client.get(
        "/api/v1/announcements", params={"updated_since": _past()}, headers=student
    ).json()
    assert [item["title"] for item in delta["items"]] == ["خبر"]


def test_notifications_delta_sync(client):
    build_world()
    admin = auth_headers(login(client, "ADMIN-9", "sync-dev-03"))
    student = auth_headers(login(client, "S-100", "sync-dev-04"))

    client.post(
        "/api/v1/admin/announcements",
        json={"scope": "college", "title": "خبر", "body": "نص"},
        headers=admin,
    )

    assert client.get(
        "/api/v1/notifications", params={"updated_since": _future()}, headers=student
    ).json()["items"] == []
    delta = client.get(
        "/api/v1/notifications", params={"updated_since": _past()}, headers=student
    ).json()
    assert len(delta["items"]) == 1
    assert delta["server_time"]


def test_materials_delta_sync_and_publish_notification(client):
    world = build_world()
    teacher = auth_headers(login(client, "T-100", "sync-dev-05"))
    student = auth_headers(login(client, "S-100", "sync-dev-06"))

    created = client.post(
        f"/api/v1/offerings/{world['offering']}/materials",
        data={
            "title": "محاضرة 1",
            "kind": "link",
            "url": "https://example.com/lecture1",
            "week_no": "1",
            "is_published": "true",
        },
        headers=teacher,
    )
    assert created.status_code == 200, created.text

    full = client.get(f"/api/v1/offerings/{world['offering']}/materials", headers=student).json()
    assert len(full["items"]) == 1
    assert full["server_time"]

    nothing = client.get(
        f"/api/v1/offerings/{world['offering']}/materials",
        params={"updated_since": _future()},
        headers=student,
    ).json()
    assert nothing["items"] == []

    delta = client.get(
        f"/api/v1/offerings/{world['offering']}/materials",
        params={"updated_since": _past()},
        headers=student,
    ).json()
    assert [item["title"] for item in delta["items"]] == ["محاضرة 1"]

    # نشر مادة غير منشورة يُشعر الطلبة المسجّلين
    client.post(
        f"/api/v1/offerings/{world['offering']}/materials",
        data={
            "title": "محاضرة 2",
            "kind": "link",
            "url": "https://example.com/lecture2",
        },
        headers=teacher,
    )
    inbox_before = client.get("/api/v1/notifications", headers=student).json()["items"]
    material_id = next(
        item["material_id"]
        for item in client.get(
            f"/api/v1/offerings/{world['offering']}/materials", headers=teacher
        ).json()["items"]
        if item["title"] == "محاضرة 2"
    )
    patched = client.patch(
        f"/api/v1/materials/{material_id}", json={"is_published": True}, headers=teacher
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["is_published"] is True

    inbox_after = client.get("/api/v1/notifications", headers=student).json()["items"]
    assert len(inbox_after) > len(inbox_before)
    assert any(item["type"] == "material_published" for item in inbox_after)

    # الطالب لا يعدّل المواد
    denied = client.patch(
        f"/api/v1/materials/{material_id}", json={"title": "تغيير"}, headers=student
    )
    assert denied.status_code == 403
