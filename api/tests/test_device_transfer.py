# -*- coding: utf-8 -*-
"""البصمة ليست ملكاً دائماً: بعد إلغاء الربط يمكن لحساب آخر استخدام الجهاز نفسه."""
from world import PASSWORD, auth_headers, build_world, login


def _login_attempt(client, university_id: str, fingerprint: str):
    return client.post(
        "/api/v1/auth/login",
        json={
            "university_id": university_id,
            "password": PASSWORD,
            "device": {"fingerprint": fingerprint, "model": "Shared"},
        },
    )


def test_revoked_device_can_bind_another_account(client):
    build_world()
    assert login(client, "S-100", "shared-device-001")["access_token"]

    admin = auth_headers(login(client, "ADMIN-9", "shared-admin-001"))
    reset = client.post("/api/v1/admin/users/S-100/device/reset", headers=admin)
    assert reset.status_code == 200

    # نفس الجهاز، حساب آخر — بعد إلغاء الربط
    moved = _login_attempt(client, "S-200", "shared-device-001")
    assert moved.status_code == 200, moved.text
    assert moved.json()["access_token"]

    # والحساب الأول يستطيع ربط جهاز جديد بعد إعادة الضبط (سلوك مقصود)
    rebound = _login_attempt(client, "S-100", "another-device-002")
    assert rebound.status_code == 200, rebound.text


def test_active_device_cannot_be_hijacked(client):
    build_world()
    assert login(client, "S-100", "active-device-010")["access_token"]

    hijack = _login_attempt(client, "S-200", "active-device-010")
    assert hijack.status_code == 403
    assert hijack.json()["code"] == "device_belongs_to_another_account"

    # الحساب الأصلي يستمر بالعمل من جهازه
    assert login(client, "S-100", "active-device-010")["access_token"]
