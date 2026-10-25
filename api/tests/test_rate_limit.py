# -*- coding: utf-8 -*-
"""اختبار حدّ محاولات الدخول: يُحسب الفشل فقط، والنجاح يصفّر العدّاد."""
from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import User
from app.models.enums import UserRole, UserStatus
from app.security import hash_password

PASSWORD = "Student#2026"
DEVICE = {"fingerprint": "rate-limit-device-01", "model": "Pixel"}


def _make_student(university_id: str) -> None:
    with SessionLocal() as db:
        db.add(
            User(
                university_id=university_id,
                full_name_ar="طالب حدّ المحاولات",
                role=UserRole.STUDENT,
                password_hash=hash_password(PASSWORD, rounds=4),
                status=UserStatus.ACTIVE,
                must_change_password=False,
            )
        )
        db.commit()


def _login(client, university_id: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        json={"university_id": university_id, "password": password, "device": DEVICE},
    )


def test_rate_limit_counts_failures_only(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "login_attempts_per_minute", 3)

    _make_student("20260100")

    # محاولتان فاشلتان ثم نجاح → يُصفَّر العدّاد
    assert _login(client, "20260100", "bad-1").status_code == 401
    assert _login(client, "20260100", "bad-2").status_code == 401
    assert _login(client, "20260100", PASSWORD).status_code == 200

    # ثلاث محاولات فاشلة تصل بالعدّاد إلى الحد
    assert _login(client, "20260100", "bad-3").status_code == 401
    assert _login(client, "20260100", "bad-4").status_code == 401
    assert _login(client, "20260100", "bad-5").status_code == 401

    blocked = _login(client, "20260100", PASSWORD)
    assert blocked.status_code == 429
    assert blocked.json()["code"] == "too_many_attempts"


def test_rate_limit_disabled_in_tests_by_default(client):
    # الإعداد الافتراضي في الاختبارات: معطّل — فلا يمنع تكرار المحاولات
    assert settings.rate_limit_enabled is False
