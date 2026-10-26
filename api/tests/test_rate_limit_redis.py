# -*- coding: utf-8 -*-
"""مسار Redis لحدّ المعدل — يُختبر بـfakeredis داخل العملية (لا يحتاج خدمة Redis خارجية).

يغطي: العدّاد في Redis، TTL عند أول تسجيل، تصفير النجاح، إصلاح مفتاح بلا TTL،
والرجوع الآمن إلى الذاكرة عند تعذّر الاتصال (بتحذير واحد فقط).
"""
import logging

import fakeredis
import pytest
import redis as redis_module

from app.config import settings
from app.services import rate_limit


@pytest.fixture()
def fake_redis(monkeypatch):
    client = fakeredis.FakeStrictRedis(server=fakeredis.FakeServer(), decode_responses=True)
    monkeypatch.setattr(settings, "redis_url", "redis://fake:6379/1")
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(
        redis_module.Redis, "from_url", classmethod(lambda cls, url, **kwargs: client)
    )
    rate_limit._reset_backend()
    yield client
    rate_limit._reset_backend()


def test_guard_and_record_use_redis_counter(fake_redis):
    key = "login:10.0.0.1"
    assert rate_limit.guard(key, limit=2) is True

    rate_limit.record(key)
    rate_limit.record(key)

    assert fake_redis.get(f"ratelimit:{key}") == "2"
    assert fake_redis.ttl(f"ratelimit:{key}") > 0
    assert rate_limit.guard(key, limit=2) is False


def test_clear_removes_redis_key(fake_redis):
    key = "scan:10.0.0.2"
    rate_limit.record(key)

    rate_limit.clear(key)

    assert fake_redis.get(f"ratelimit:{key}") is None
    assert rate_limit.guard(key, limit=1) is True


def test_guard_repairs_key_without_ttl(fake_redis):
    """مفتاح بلا TTL (انقطاع بين INCR وEXPIRE) يجب ألا يبقى محجوباً للأبد."""
    key = "login:no-ttl"
    fake_redis.set(f"ratelimit:{key}", 5)

    assert rate_limit.guard(key, limit=5) is False
    assert fake_redis.ttl(f"ratelimit:{key}") > 0


def test_falls_back_to_memory_when_redis_unreachable(monkeypatch, caplog):
    monkeypatch.setattr(settings, "redis_url", "redis://down:6379/0")
    monkeypatch.setattr(settings, "rate_limit_enabled", True)

    def explode(cls, url, **kwargs):
        raise redis_module.ConnectionError("redis down")

    monkeypatch.setattr(redis_module.Redis, "from_url", classmethod(explode))
    rate_limit._reset_backend()
    caplog.set_level(logging.WARNING)

    assert rate_limit.guard("login:down", limit=1) is True
    rate_limit.record("login:down")
    assert rate_limit.guard("login:down", limit=1) is False  # العدّاد المحلي يعمل

    warnings = [row for row in caplog.records if "Redis غير متاح" in row.getMessage()]
    assert len(warnings) == 1, [row.getMessage() for row in caplog.records]
    rate_limit._reset_backend()
