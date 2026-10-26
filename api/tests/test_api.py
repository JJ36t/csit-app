# -*- coding: utf-8 -*-
"""اختبارات نقاط الـAPI المتاحة حالياً."""
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

import app.routers.health as health_router
from app.db import engine


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert "revision" in body


def test_health_reports_migration_revision(client):
    """يقرأ رقم الترحيل من ‎alembic_version‎ عندما يكون الجدول موجوداً."""
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        conn.execute(
            text("INSERT INTO alembic_version (version_num) VALUES ('0003_materials_announcements')")
        )
    try:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json() == {
            "status": "ok",
            "database": "ok",
            "revision": "0003_materials_announcements",
        }
    finally:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))


def test_health_degrades_when_database_unreachable(client, monkeypatch):
    """تعطّل القاعدة ⇒ 503 مع status=degraded وبقاء المفتاح status."""

    def _unreachable():
        raise OperationalError("SELECT 1", {}, OSError("database is down"))

    monkeypatch.setattr(health_router, "SessionLocal", _unreachable)
    res = client.get("/health")
    assert res.status_code == 503
    assert res.json() == {"status": "degraded", "database": "unavailable", "revision": None}

def test_root(client):
    res = client.get("/")
    assert res.status_code == 200
    body = res.json()
    assert body["health"] == "/health"
    assert body["docs"] == "/docs"


def test_departments_seeded_four(client):
    res = client.get("/api/v1/departments")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 4
    assert {d["code"] for d in data} == {"CS", "IS", "MS", "CY"}
    assert {d["name_ar"] for d in data} == {
        "علوم الحاسوب",
        "نظم المعلومات",
        "الأنظمة الطبية",
        "الأمن السيبراني",
    }
