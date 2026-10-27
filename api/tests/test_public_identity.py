# -*- coding: utf-8 -*-
"""اختبارات الأخبار العامة والهوية الرقمية (التوقيع، الانتهاء، والتزوير)."""
import json
from datetime import datetime, timezone

from app.services import identity
from world import auth_headers, build_world, login


def test_public_news_serves_college_scope_only_without_auth(client):
    world = build_world()
    admin = auth_headers(login(client, "ADMIN-9", "pub-dev-01"))

    client.post(
        "/api/v1/admin/announcements",
        json={"scope": "college", "title": "بدء التسجيل", "body": "التسجيل مفتوح"},
        headers=admin,
    )
    client.post(
        "/api/v1/admin/announcements",
        json={
            "scope": "department",
            "scope_id": world["department"],
            "title": "اجتماع القسم",
            "body": "خاص بالقسم",
        },
        headers=admin,
    )

    # بلا أي رمز وصول
    news = client.get("/api/v1/public/news")
    assert news.status_code == 200
    titles = [item["title"] for item in news.json()["items"]]
    assert titles == ["بدء التسجيل"]
    assert news.json()["items"][0]["body"] == "التسجيل مفتوح"


def test_identity_card_issue_and_verify(client):
    build_world()
    student = auth_headers(login(client, "S-100", "id-dev-01"))
    teacher = auth_headers(login(client, "T-100", "id-dev-02"))

    card = client.get("/api/v1/me/identity-card", headers=student)
    assert card.status_code == 200, card.text
    body = card.json()
    assert body["card"].startswith("CSIT1.")
    assert body["profile"]["university_id"] == "S-100"
    assert body["ttl_seconds"] > 0

    verified = client.post(
        "/api/v1/identity/verify", json={"card": body["card"]}, headers=teacher
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["valid"] is True
    assert verified.json()["student"]["university_id"] == "S-100"
    assert verified.json()["student"]["department"]

    # بطاقة معدّلة → توقيع غير صالح
    prefix, segment, signature = body["card"].split(".")
    flipped = ("A" if segment[0] != "A" else "B") + segment[1:]
    tampered = f"{prefix}.{flipped}.{signature}"
    bad = client.post("/api/v1/identity/verify", json={"card": tampered}, headers=teacher)
    assert bad.status_code == 400
    assert bad.json()["code"] in ("invalid_card_signature", "invalid_card")

    # الطالب لا يتحقق من البطاقات
    assert (
        client.post("/api/v1/identity/verify", json={"card": body["card"]}, headers=student).status_code
        == 403
    )


def test_expired_card_is_rejected(client):
    world = build_world()
    teacher = auth_headers(login(client, "T-100", "id-dev-03"))

    now = int(datetime.now(timezone.utc).timestamp())
    payload = {
        "v": 1,
        "uid": world["student"],
        "sid": "S-100",
        "name": "علي حسن محمد",
        "dept": "علوم الحاسوب",
        "stage": 1,
        "grp": "A",
        "study": "morning",
        "iat": now - 600,
        "exp": now - 300,
        "nonce": "abcd1234",
    }
    segment = identity._b64e(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    card = f"CSIT1.{segment}.{identity._sign(segment)}"

    expired = client.post("/api/v1/identity/verify", json={"card": card}, headers=teacher)
    assert expired.status_code == 410
    assert expired.json()["code"] == "card_expired"


def test_identity_card_requires_student_account(client):
    build_world()
    teacher = auth_headers(login(client, "T-100", "id-dev-04"))
    denied = client.get("/api/v1/me/identity-card", headers=teacher)
    assert denied.status_code == 403
    assert denied.json()["code"] == "not_a_student"
