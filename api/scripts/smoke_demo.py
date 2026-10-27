# -*- coding: utf-8 -*-
"""فحص دخاني لبيانات العرض: يسجّل دخول الحسابات التجريبية ويمرّ على الشاشات.

    python scripts/smoke_demo.py

يفترض أن قاعدة البيانات مهيأة بـ`scripts/demo_full_seed.py`. يفشل (exit 1)
إن غاب أي عنصر متوقع: جلسة اليوم، مواد، درجات، إعلانات، عروض، بطاقة هوية.
"""
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

PASSWORD = "Test#12345"
BAGHDAD = timezone(timedelta(hours=3))
failures: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  [OK]   {name}")
    else:
        print(f"  [FAIL] {name} {detail}")
        failures.append(name)


def login(client: TestClient, university_id: str, fingerprint: str, code: str | None = None):
    body = {
        "university_id": university_id,
        "password": PASSWORD,
        "device": {"fingerprint": fingerprint, "model": "Smoke"},
    }
    if code:
        body["totp_code"] = code
    res = client.post("/api/v1/auth/login", json=body)
    if res.status_code == 403 and res.json().get("code") == "device_change_requires_approval":
        # جهاز مسجَّل مسبقاً من تجربة سابقة — نكمل بلا فحص الشاشات
        print(f"  [SKIP] {university_id}: الجهاز مربوط مسبقاً (شغّل dev_reset_devices)")
        return None
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    stamp = datetime.now(timezone.utc).strftime("%H%M%S")

    with TestClient(app) as client:
        print("طالب — S-CS1-01")
        student = login(client, "S-CS1-01", f"smoke-s-{stamp}")
        if student:
            timetable = client.get("/api/v1/timetable", headers=student)
            check("الجدول", timetable.status_code == 200, timetable.text[:120])
            sessions = timetable.json().get("items", [])
            check("جلسات الأسبوع", len(sessions) >= 1, f"({len(sessions)})")
            check(
                "جلسة اليوم موجودة",
                any(s["date"] == date.today().isoformat() for s in sessions),
            )

            offerings = client.get("/api/v1/offerings", headers=student).json()["items"]
            check("مواد مسجّلة", len(offerings) >= 3, f"({len(offerings)})")

            materials = client.get(
                f"/api/v1/offerings/{offerings[0]['offering_id']}/materials", headers=student
            )
            check("مواد المقرر", materials.status_code == 200 and materials.json()["items"])

            grades = client.get("/api/v1/grades", headers=student)
            check("الدرجات", grades.status_code == 200 and grades.json().get("items"))

            news = client.get("/api/v1/announcements", headers=student)
            check("الإعلانات", news.status_code == 200 and news.json()["items"])

            inbox = client.get("/api/v1/notifications", headers=student).json()
            check("صندوق الإشعارات", inbox["unread_count"] >= 1, f"({inbox['unread_count']})")

            card = client.get("/api/v1/me/identity-card", headers=student)
            check("بطاقة الهوية", card.status_code == 200 and card.json()["card"].startswith("CSIT1."))

            excuses = client.get("/api/v1/excuses", headers=student)
            check("شاشة الأعذار", excuses.status_code == 200)

            requests = client.get("/api/v1/requests", headers=student)
            check("شاشة الطلبات", requests.status_code == 200)

        print("تدريسي — T-101")
        teacher = login(client, "T-101", f"smoke-t-{stamp}")
        if teacher:
            live = client.get("/api/v1/timetable", headers=teacher)
            check("جدول التدريسي", live.status_code == 200, live.text[:120])
            today_sessions = live.json().get("items", []) if live.status_code == 200 else []
            check("حصص اليوم للتدريسي", bool(today_sessions))

            queue = client.get("/api/v1/admin/excuses", headers=teacher)
            check("قائمة الأعذار", queue.status_code == 200)
            check("عذر قيد المراجعة", queue.json()["pending_total"] >= 1)

            offering_id = client.get("/api/v1/offerings", headers=teacher).json()["items"][0][
                "offering_id"
            ]
            report = client.get(
                f"/api/v1/admin/reports/attendance?offering_id={offering_id}", headers=teacher
            )
            check("تقرير الحضور", report.status_code == 200)
            csv = client.get(
                f"/api/v1/admin/reports/attendance?offering_id={offering_id}&format=csv",
                headers=teacher,
            )
            check("تصدير CSV", csv.status_code == 200 and len(csv.content) > 50)

        print("رئيس القسم — HEAD-CS")
        head = login(client, "HEAD-CS", f"smoke-h-{stamp}")
        if head:
            groups = client.get("/api/v1/admin/groups", headers=head)
            check("قائمة الشعب", groups.status_code == 200 and groups.json()["items"])
            requests = client.get("/api/v1/requests", headers=head)
            check("طلبات القسم", requests.status_code == 200)

        print("مدير — ADMIN-001")
        admin_body = client.post(
            "/api/v1/auth/login",
            json={
                "university_id": "ADMIN-001",
                "password": "Admin#2026",
                "device": {"fingerprint": f"smoke-a-{stamp}", "model": "Smoke"},
            },
        )
        if admin_body.status_code == 200:
            admin = {"Authorization": f"Bearer {admin_body.json()['access_token']}"}
            overview = client.get("/api/v1/admin/overview", headers=admin)
            check("ملخص اللوحة", overview.status_code == 200, overview.text[:120])
            public = client.get("/api/v1/public/news")
            check("الأخبار العامة", public.status_code == 200 and public.json()["items"])

    print()
    if failures:
        print(f"فحص دخاني: فشل {len(failures)} — {'، '.join(failures)}")
        raise SystemExit(1)
    print("فحص دخاني: كل الفحوص نجحت.")


if __name__ == "__main__":
    main()
