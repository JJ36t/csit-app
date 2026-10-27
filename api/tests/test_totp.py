# -*- coding: utf-8 -*-
"""اختبارات TOTP: مطابقة متجه RFC 6238، النافذة، ومنع إعادة الاستخدام.
ثم مسار المصادقة الثنائية الكامل عبر الـAPI.
"""
import base64
from datetime import datetime, timedelta, timezone

from app.services import totp
from world import PASSWORD, auth_headers, build_world, login

RFC_SECRET = base64.b32encode(b"12345678901234567890").decode("ascii")


def test_matches_rfc6238_reference_vector():
    # المتجه المرجعي: T=59s، سرّ ASCII "12345678901234567890"، 8 أرقام
    moment = datetime.fromtimestamp(59, timezone.utc)
    assert totp.code(RFC_SECRET, at=moment, digits=8) == "94287082"


def test_verify_accepts_neighbouring_step_and_rejects_others():
    moment = datetime.now(timezone.utc)
    secret = totp.new_secret()

    current = totp.code(secret, at=moment)
    assert totp.verify(secret, current, at=moment) == totp.step_at(moment)

    previous = totp.code(secret, at=moment - timedelta(seconds=30))
    assert totp.verify(secret, previous, at=moment) is not None

    stale = totp.code(secret, at=moment - timedelta(minutes=5))
    assert totp.verify(secret, stale, at=moment) is None
    assert totp.verify(secret, "", at=moment) is None


def test_provisioning_uri_contains_secret_and_issuer():
    uri = totp.provisioning_uri("ABCDEFGH", "T-100", issuer="CSIT")
    assert uri.startswith("otpauth://totp/CSIT%3AT-100?")
    assert "secret=ABCDEFGH" in uri
    assert "issuer=CSIT" in uri


def test_2fa_full_flow_for_instructor(client):
    build_world()
    headers = auth_headers(login(client, "T-100", "totp-dev-01"))

    status = client.get("/api/v1/auth/2fa/status", headers=headers).json()
    assert status == {"enabled": False, "available": True, "confirmed_at": None}

    setup = client.post("/api/v1/auth/2fa/setup", headers=headers)
    assert setup.status_code == 200, setup.text
    secret = setup.json()["secret"]
    assert setup.json()["otpauth_uri"].startswith("otpauth://totp/")

    # رمز الخطوة الحالية يُفعّل الحساب
    enabled = client.post(
        "/api/v1/auth/2fa/enable", json={"code": totp.code(secret)}, headers=headers
    )
    assert enabled.status_code == 200, enabled.text
    assert enabled.json()["enabled"] is True

    # إعادة التفعيل مرفوضة
    again = client.post(
        "/api/v1/auth/2fa/enable", json={"code": totp.code(secret)}, headers=headers
    )
    assert again.status_code == 409

    # دخول من الجهاز نفسه بلا رمز → مطلوب
    missing = client.post(
        "/api/v1/auth/login",
        json={
            "university_id": "T-100",
            "password": PASSWORD,
            "device": {"fingerprint": "totp-dev-01"},
        },
    )
    assert missing.status_code == 401
    assert missing.json()["code"] == "totp_required"
    assert missing.json()["details"]["totp_required"] is True

    # رمز الخطوة التالية (الحالية استُهلكت في التفعيل)
    next_code = totp.code(secret, at=datetime.now(timezone.utc) + timedelta(seconds=30))
    ok = client.post(
        "/api/v1/auth/login",
        json={
            "university_id": "T-100",
            "password": PASSWORD,
            "device": {"fingerprint": "totp-dev-01"},
            "totp_code": next_code,
        },
    )
    assert ok.status_code == 200, ok.text

    # إعادة استخدام الرمز نفسه مرفوضة (replay)
    replay = client.post(
        "/api/v1/auth/login",
        json={
            "university_id": "T-100",
            "password": PASSWORD,
            "device": {"fingerprint": "totp-dev-01"},
            "totp_code": next_code,
        },
    )
    assert replay.status_code == 401
    assert replay.json()["code"] == "totp_replayed"


def test_disable_requires_password(client):
    build_world()
    headers = auth_headers(login(client, "T-100", "totp-dev-10"))
    secret = client.post("/api/v1/auth/2fa/setup", headers=headers).json()["secret"]
    client.post(
        "/api/v1/auth/2fa/enable", json={"code": totp.code(secret)}, headers=headers
    )

    wrong = client.post(
        "/api/v1/auth/2fa/disable", json={"password": "wrong-pass"}, headers=headers
    )
    assert wrong.status_code == 400

    disabled = client.post(
        "/api/v1/auth/2fa/disable", json={"password": PASSWORD}, headers=headers
    )
    assert disabled.status_code == 200
    assert disabled.json()["enabled"] is False

    # بعد التعطيل يعود الدخول بلا رمز
    assert login(client, "T-100", "totp-dev-10")["access_token"]


def test_students_cannot_use_2fa_and_admin_can_reset(client):
    build_world()
    student = auth_headers(login(client, "S-100", "totp-dev-20"))
    denied = client.post("/api/v1/auth/2fa/setup", headers=student)
    assert denied.status_code == 403
    assert denied.json()["code"] == "totp_not_available"

    teacher_headers = auth_headers(login(client, "T-100", "totp-dev-21"))
    secret = client.post("/api/v1/auth/2fa/setup", headers=teacher_headers).json()["secret"]
    client.post(
        "/api/v1/auth/2fa/enable", json={"code": totp.code(secret)}, headers=teacher_headers
    )

    admin = auth_headers(login(client, "ADMIN-9", "totp-dev-22"))
    reset = client.post("/api/v1/admin/users/T-100/2fa/reset", headers=admin)
    assert reset.status_code == 200
    assert reset.json()["was_enabled"] is True

    # الدخول يعمل الآن بلا رمز (الجهاز نفسه المربوط)
    assert login(client, "T-100", "totp-dev-21")["access_token"]
