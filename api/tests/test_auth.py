# -*- coding: utf-8 -*-
"""اختبارات المصادقة: دخول، ربط جهاز، تجديد مع كشف إعادة الاستخدام، تغيير كلمة المرور."""
from app.db import SessionLocal
from app.models import User
from app.models.enums import UserRole, UserStatus
from app.security import hash_password

DEVICE_A = {"fingerprint": "device-aaaa-0001", "model": "Pixel"}
DEVICE_B = {"fingerprint": "device-bbbb-0002", "model": "iPhone"}

STUDENT_ID = "20240001"
STUDENT_PASSWORD = "Student@123"


def _make_student(university_id: str = STUDENT_ID, password: str = STUDENT_PASSWORD) -> None:
    with SessionLocal() as db:
        db.add(
            User(
                university_id=university_id,
                full_name_ar="طالب اختبار",
                role=UserRole.STUDENT,
                password_hash=hash_password(password),
                status=UserStatus.ACTIVE,
                must_change_password=True,
            )
        )
        db.commit()


def _login(client, university_id=STUDENT_ID, password=STUDENT_PASSWORD, device=DEVICE_A):
    return client.post(
        "/api/v1/auth/login",
        json={"university_id": university_id, "password": password, "device": device},
    )


def test_login_success_and_me(client):
    _make_student()
    res = _login(client)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 15 * 60
    assert data["refresh_token"]
    assert data["user"]["university_id"] == STUDENT_ID
    assert data["user"]["must_change_password"] is True

    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["role"] == "student"


def test_login_wrong_password_returns_arabic_error(client):
    _make_student()
    res = _login(client, password="wrong-password")
    assert res.status_code == 401
    body = res.json()
    assert body["code"] == "invalid_credentials"
    assert body["message_ar"]


def test_me_requires_token(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["code"] == "not_authenticated"


def test_device_binding_blocks_second_device(client):
    _make_student()
    assert _login(client).status_code == 200

    second = _login(client, device=DEVICE_B)
    assert second.status_code == 403
    assert second.json()["code"] == "device_change_requires_approval"

    # الجهاز الأصلي ما زال يعمل
    assert _login(client).status_code == 200


def test_refresh_rotation_and_reuse_detection(client):
    _make_student()
    first = _login(client).json()
    refresh1 = first["refresh_token"]

    second = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh1})
    assert second.status_code == 200, second.text
    refresh2 = second.json()["refresh_token"]
    assert refresh2 != refresh1

    # إعادة استخدام رمز ملغى → رفض + إنهاء كل الجلسات
    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh1})
    assert reuse.status_code == 401
    assert reuse.json()["code"] == "refresh_token_reused"

    # حتى الرمز الأحدث أُلغي بسبب الإنهاء الشامل
    after = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh2})
    assert after.status_code == 401


def test_change_password_flow(client):
    _make_student()
    login = _login(client).json()
    access = login["access_token"]

    res = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {access}"},
        json={"current_password": STUDENT_PASSWORD, "new_password": "NewPass@2026"},
    )
    assert res.status_code == 200
    assert res.json()["reauth_required"] is True

    # القديمة لم تعد تعمل، والجديدة تعمل
    assert _login(client).status_code == 401
    ok = _login(client, password="NewPass@2026")
    assert ok.status_code == 200
    assert ok.json()["user"]["must_change_password"] is False


def test_weak_new_password_rejected(client):
    _make_student()
    access = _login(client).json()["access_token"]
    res = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {access}"},
        json={"current_password": STUDENT_PASSWORD, "new_password": STUDENT_ID},
    )
    assert res.status_code == 400
    assert res.json()["code"] == "weak_password"


def test_import_forbidden_for_student(client):
    _make_student()
    token = _login(client).json()["access_token"]
    res = client.post(
        "/api/v1/admin/students/import",
        headers={"Authorization": f"Bearer {token}"},
        params={"dry_run": "true"},
        files={
            "file": (
                "s.xlsx",
                b"not-an-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert res.status_code == 403
    assert res.json()["code"] == "forbidden"
