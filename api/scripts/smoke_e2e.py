# -*- coding: utf-8 -*-
"""فحص شامل حقيقي عبر HTTP (شغّله بعد تشغيل الخدمة على قاعدة PostgreSQL).

    python scripts/smoke_e2e.py

يفترض وجود حساب مدير أُنشئ بـ:
    python scripts/create_admin.py ADMIN-001 "مدير الكلية" "Admin#2026"

السكربت قابل للتكرار: يعيد ضبط ربط جهاز الطالب التجريبي قبل البدء،
ويتعامل مع «الطالب مستورد مسبقاً» كحالة طبيعية.
"""
import os
import sys

import httpx

BASE = os.environ.get("SMOKE_BASE", "http://127.0.0.1:8123/api/v1")
ADMIN_ID = os.environ.get("SMOKE_ADMIN_ID", "ADMIN-001")
ADMIN_PW = os.environ.get("SMOKE_ADMIN_PW", "Admin#2026")

DEMO_STUDENT = "20240001"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    with httpx.Client(timeout=60) as client:
        # 1) دخول المدير
        r = client.post(
            f"{BASE}/auth/login",
            json={
                "university_id": ADMIN_ID,
                "password": ADMIN_PW,
                "device": {"fingerprint": "e2e-admin-device-01", "model": "Workstation"},
            },
        )
        r.raise_for_status()
        login = r.json()
        print(
            "admin login:", login["user"]["role"],
            "| must_change:", login["user"]["must_change_password"],
        )
        headers = {"Authorization": f"Bearer {login['access_token']}"}

        # 2) تنظيف حالة التشغيل السابق (إن وُجد الطالب)
        r = client.post(f"{BASE}/admin/users/{DEMO_STUDENT}/device/reset", headers=headers)
        print("pre-clean device reset:", r.status_code)

        # 3) تنزيل القالب ثم استيراده فعلياً
        r = client.get(f"{BASE}/admin/students/template", headers=headers)
        r.raise_for_status()
        print("template bytes:", len(r.content))

        r = client.post(
            f"{BASE}/admin/students/import",
            params={"dry_run": "false"},
            headers=headers,
            files={"file": ("students.xlsx", r.content, XLSX)},
        )
        r.raise_for_status()
        imported = r.json()
        print(
            "import: created =", imported["created_count"],
            "| valid =", imported["rows_valid"],
            "| errors =", len(imported["errors"]),
        )
        if imported["created_count"] == 0:
            codes = {issue["code"] for issue in imported["errors"]}
            assert codes == {"duplicate_university_id"}, codes
            print("student already imported in a previous run (ok)")

        # 4) دخول الطالب بكلمة المرور الأولية
        student = {
            "university_id": DEMO_STUDENT,
            "password": DEMO_STUDENT,
            "device": {"fingerprint": "e2e-phone-0001", "model": "Phone"},
        }
        r = client.post(f"{BASE}/auth/login", json=student)
        r.raise_for_status()
        body = r.json()
        print(
            "student login:", body["user"]["full_name_ar"],
            "| dept:", body["user"]["student"]["department"]["name_ar"],
            "| group:", body["user"]["student"]["group_name"],
            "| must_change:", body["user"]["must_change_password"],
        )

        # 5) جهاز ثانٍ يُرفض حتى موافقة القسم
        second = {**student, "device": {"fingerprint": "e2e-phone-0002", "model": "Phone2"}}
        r = client.post(f"{BASE}/auth/login", json=second)
        print("second device blocked:", r.status_code, r.json().get("code"))

        # 6) المدير يعيد ضبط الربط → الجهاز الجديد يعمل
        r = client.post(f"{BASE}/admin/users/{DEMO_STUDENT}/device/reset", headers=headers)
        r.raise_for_status()
        print(
            "device reset:", r.json()["devices_revoked"],
            "device(s), sessions:", r.json()["sessions_revoked"],
        )

        r = client.post(f"{BASE}/auth/login", json=second)
        print("second device after reset:", r.status_code)
        student_token = r.json().get("access_token")

        # 7) قائمة الطلاب للمدير، ورفض رمز الطالب على نقاط الإدارة
        r = client.get(f"{BASE}/admin/students", headers=headers, params={"q": DEMO_STUDENT})
        r.raise_for_status()
        print("students listed:", r.json()["total"])

        r = client.get(
            f"{BASE}/admin/students",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        print("student token on admin endpoint:", r.status_code, r.json().get("code"))


if __name__ == "__main__":
    main()
