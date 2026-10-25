# -*- coding: utf-8 -*-
"""اختبارات نقاط الـAPI المتاحة حالياً."""


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


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
