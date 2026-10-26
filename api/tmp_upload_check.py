# -*- coding: utf-8 -*-
"""فحص استمرارية ملفات المواد عبر إعادة تشغيل حاوية api (volume uploads)."""
import sys

import httpx

BASE = "http://127.0.0.1:8080/api/v1"
PDF = b"%PDF-1.4\n%compose volume check\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    with httpx.Client(timeout=30) as client:
        login = client.post(
            f"{BASE}/auth/login",
            json={
                "university_id": "T-100",
                "password": "Test#12345",
                "device": {"fingerprint": "compose-upload", "model": "Compose"},
            },
        )
        login.raise_for_status()
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        offerings = client.get(f"{BASE}/offerings", headers=headers)
        offerings.raise_for_status()
        offering_id = offerings.json()["items"][0]["offering_id"]

        uploaded = client.post(
            f"{BASE}/offerings/{offering_id}/materials",
            data={"title": "فحص volume", "kind": "pdf", "is_published": "true"},
            files={"file": ("volume-check.pdf", PDF, "application/pdf")},
            headers=headers,
        )
        uploaded.raise_for_status()
        material_id = uploaded.json()["material_id"]
        print("uploaded:", material_id)

        listing = client.get(f"{BASE}/offerings/{offering_id}/materials", headers=headers)
        listing.raise_for_status()
        item = next(row for row in listing.json()["items"] if row["material_id"] == material_id)
        print("download_url:", item["download_url"][:60], "…")
        print("OFFERING", offering_id)
        print("URL", item["download_url"])


if __name__ == "__main__":
    main()
