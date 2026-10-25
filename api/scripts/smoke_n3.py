# -*- coding: utf-8 -*-
"""فحص شامل لدورة N3 عبر HTTP حقيقي (بعد تشغيل الخدمة على 8000).

    python scripts/smoke_n3.py

يفترض بيانات العرض من `scripts/demo_seed.py` وحساب المدير من `create_admin.py`.
يغطي: تقييم ← إدخال درجة ← نشر بموافقة ← رؤية الطالب ← إعلان وإشعار ← مادة برابط موقّع.
قابل للتكرار: يعيد استخدام تقييم السموك ودرجاته إن وُجدت.
"""
import os
import sys

import httpx

BASE = os.environ.get("SMOKE_BASE", "http://127.0.0.1:8000/api/v1")
ORIGIN = BASE.split("/api/")[0]
TEACHER = ("T-100", "Test#12345", "smoke-teacher-01")
STUDENT = ("S-100", "Test#12345", "smoke-student-01")
ADMIN = ("ADMIN-001", "Admin#2026", "smoke-admin-01")
PDF = b"%PDF-1.4\n%smoke material\n"


def login(client: httpx.Client, credentials: tuple[str, str, str]) -> dict:
    university_id, password, device = credentials
    res = client.post(
        f"{BASE}/auth/login",
        json={
            "university_id": university_id,
            "password": password,
            "device": {"fingerprint": device, "model": "Smoke"},
        },
    )
    res.raise_for_status()
    return res.json()


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def offering_id_for_student(client: httpx.Client, student_token: str) -> str:
    res = client.get(f"{BASE}/grades", headers=headers(student_token))
    res.raise_for_status()
    items = res.json()["items"]
    assert items, "لا توجد مواد مسجَّلة للطالب — شغّل scripts/demo_seed.py"
    return items[0]["offering_id"]


def ensure_assessment(client: httpx.Client, teacher_token: str, offering_id: str) -> dict:
    matrix = client.get(f"{BASE}/offerings/{offering_id}/grades", headers=headers(teacher_token))
    matrix.raise_for_status()
    for row in matrix.json()["assessments"]:
        if row["name"] == "سموك N3":
            return row
    created = client.post(
        f"{BASE}/assessments",
        json={
            "offering_id": offering_id,
            "name": "سموك N3",
            "kind": "quiz",
            "max_score": 50,
            "weight": 10,
        },
        headers=headers(teacher_token),
    )
    created.raise_for_status()
    return created.json()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    with httpx.Client(timeout=60) as client:
        teacher = login(client, TEACHER)
        student = login(client, STUDENT)
        admin = login(client, ADMIN)
        teacher_token = teacher["access_token"]
        student_token = student["access_token"]
        admin_token = admin["access_token"]
        print("logins ok:", teacher["user"]["role"], student["user"]["role"], admin["user"]["role"])

        offering = offering_id_for_student(client, student_token)
        print("offering:", offering)

        assessment = ensure_assessment(client, teacher_token, offering)
        print("assessment:", assessment["name"], "| published:", assessment["is_published"])

        if not assessment["is_published"]:
            saved = client.post(
                f"{BASE}/assessments/{assessment['assessment_id']}/grades",
                json={"rows": [{"student_id": student["user"]["id"], "score": 45}]},
                headers=headers(teacher_token),
            )
            saved.raise_for_status()
            print("grades saved:", saved.json())

            published = client.post(
                f"{BASE}/assessments/{assessment['assessment_id']}/publish",
                headers=headers(admin_token),
            )
            published.raise_for_status()
            print("published | notified:", published.json()["notified"])
        else:
            print("already published — skip grading step")

        grades = client.get(f"{BASE}/grades", headers=headers(student_token))
        grades.raise_for_status()
        course = next(
            item for item in grades.json()["items"] if item["offering_id"] == offering
        )
        seen = [
            row for row in course["assessments"]
            if row["assessment_id"] == assessment["assessment_id"]
        ]
        assert seen and seen[0]["score"] == 45.0, course
        print("student sees score:", seen[0]["score"], "| weighted:", course["weighted_total"])

        created = client.post(
            f"{BASE}/admin/announcements",
            json={"scope": "college", "title": "سموك N3", "body": "فحص آلي"},
            headers=headers(admin_token),
        )
        created.raise_for_status()
        feed = client.get(f"{BASE}/announcements", headers=headers(student_token))
        feed.raise_for_status()
        assert "سموك N3" in [item["title"] for item in feed.json()["items"]]
        inbox = client.get(f"{BASE}/notifications", headers=headers(student_token))
        inbox.raise_for_status()
        print("announcement visible | unread:", inbox.json()["unread_count"])

        upload = client.post(
            f"{BASE}/offerings/{offering}/materials",
            data={"title": "سموك — محاضرة", "kind": "pdf", "is_published": "true"},
            files={"file": ("smoke.pdf", PDF, "application/pdf")},
            headers=headers(teacher_token),
        )
        upload.raise_for_status()
        material = upload.json()
        listing = client.get(f"{BASE}/offerings/{offering}/materials", headers=headers(student_token))
        listing.raise_for_status()
        item = next(
            row for row in listing.json()["items"] if row["material_id"] == material["material_id"]
        )
        download = client.get(f"{ORIGIN}{item['download_url']}")
        download.raise_for_status()
        assert download.content == PDF
        print("material download ok:", len(download.content), "bytes |", item["file_name"])

        print("\nN3 smoke: كل الخطوات نجحت")


if __name__ == "__main__":
    main()
