# -*- coding: utf-8 -*-
"""اختبار حدّ محاولات الدخول: يُحسب الفشل فقط، والنجاح يصفّر العدّاد."""
import logging

import pytest
from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import User
from app.models.enums import UserRole, UserStatus
from app.security import hash_password
from app.services import rate_limit

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


# ------------------------- تخزين Redis (بعميل وهمي) -------------------------


class _FakeRedis:
    """بديل وهمي لعميل Redis: عدّاد + TTL + حذف، دون خدمة حقيقية."""

    def __init__(self, *, fail: bool = False) -> None:
        self.store: dict[str, int] = {}
        self.ttls: dict[str, int] = {}
        self.incr_calls = 0
        self.delete_calls = 0
        self.fail = fail

    def _check(self) -> None:
        if self.fail:
            raise ConnectionError("redis is down")

    def get(self, key: str) -> int | None:
        self._check()
        return self.store.get(key)

    def incr(self, key: str) -> int:
        self._check()
        self.incr_calls += 1
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    def expire(self, key: str, seconds: int) -> bool:
        self._check()
        self.ttls[key] = seconds
        return True

    def ttl(self, key: str) -> int:
        self._check()
        if key not in self.store:
            return -2
        return self.ttls.get(key, -1)

    def delete(self, key: str) -> int:
        self._check()
        self.delete_calls += 1
        self.store.pop(key, None)
        return 1


@pytest.fixture()
def redis_backend(monkeypatch):
    """يضبط رابط Redis وهمياً ويعزل حالة الوحدة بين الاختبارات."""
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "redis_url", "redis://fake:6379/0")
    rate_limit._reset_backend()
    yield
    rate_limit._reset_backend()


def _install(fake: _FakeRedis) -> None:
    rate_limit._client = fake
    rate_limit._client_url = settings.redis_url


def test_redis_counts_and_blocks(redis_backend):
    fake = _FakeRedis()
    _install(fake)

    assert rate_limit.guard("login:r1", limit=2) is True
    rate_limit.record("login:r1")
    assert rate_limit.guard("login:r1", limit=2) is True
    rate_limit.record("login:r1")
    assert rate_limit.guard("login:r1", limit=2) is False

    assert fake.incr_calls == 2
    # TTL يُضبط مرة واحدة عند أول تسجيل فقط
    assert fake.ttls == {"ratelimit:login:r1": 60}
    assert not rate_limit._windows


def test_redis_clear_resets_counter(redis_backend):
    fake = _FakeRedis()
    _install(fake)

    rate_limit.record("login:r2")
    rate_limit.record("login:r2")
    assert rate_limit.guard("login:r2", limit=2) is False

    rate_limit.clear("login:r2")
    assert rate_limit.guard("login:r2", limit=2) is True
    assert fake.delete_calls == 1
    assert "ratelimit:login:r2" not in fake.store


def test_redis_blocked_key_without_ttl_gets_expiry(redis_backend):
    """انقطاع بين INCR وEXPIRE لا يترك المفتاح محجوباً بلا نهاية."""
    fake = _FakeRedis()
    fake.store["ratelimit:login:r4"] = 2
    _install(fake)

    assert rate_limit.guard("login:r4", limit=2) is False
    assert fake.ttls == {"ratelimit:login:r4": 60}

    rate_limit.clear("login:r4")
    assert rate_limit.guard("login:r4", limit=2) is True


def test_redis_connection_error_falls_back_to_memory(redis_backend, caplog):
    fake = _FakeRedis(fail=True)
    _install(fake)

    with caplog.at_level(logging.WARNING, logger="app.services.rate_limit"):
        assert rate_limit.guard("login:r3", limit=2) is True
        rate_limit.record("login:r3")
        rate_limit.record("login:r3")
        assert rate_limit.guard("login:r3", limit=2) is False
        rate_limit.record("login:r3")  # لا تحذير ثانٍ ولا محاولة أخرى لـRedis

    warnings = [r for r in caplog.records if r.name == "app.services.rate_limit"]
    assert len(warnings) == 1
    assert rate_limit._redis_down is True
    assert fake.incr_calls == 0
    assert len(rate_limit._windows["login:r3"]) == 3


def test_without_redis_url_uses_memory(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "redis_url", "")
    rate_limit._reset_backend()

    rate_limit.record("scan:1")
    assert rate_limit.guard("scan:1", limit=1) is False
    assert rate_limit._client is None

    rate_limit.clear("scan:1")
    assert rate_limit.guard("scan:1", limit=1) is True
    rate_limit._reset_backend()
