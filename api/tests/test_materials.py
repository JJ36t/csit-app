# -*- coding: utf-8 -*-
"""اختبارات المواد والملفات (N3): رفع مع تحقق النوع/الحجم، رؤية المنشور، روابط موقّعة."""
from app.config import settings
from app.services.file_links import _digest, signed_path
from world import auth_headers, build_world, login

PDF_BYTES = b"%PDF-1.4\n%test material\n"


def _upload(
    client,
    headers,
    offering_id: str,
    *,
    title: str = "محاضرة 1 — مقدمة",
    kind: str = "pdf",
    content: bytes | None = PDF_BYTES,
    mime: str = "application/pdf",
    published: bool = True,
    url: str | None = None,
):
    data = {
        "title": title,
        "kind": kind,
        "is_published": "true" if published else "false",
    }
    if url is not None:
        data["url"] = url
    files = {"file": ("lecture-1.pdf", content, mime)} if content is not None else None
    return client.post(
        f"/api/v1/offerings/{offering_id}/materials",
        data=data,
        files=files,
        headers=headers,
    )


def test_teacher_uploads_pdf_and_student_downloads_signed_link(client):
    world = build_world()
    teacher = auth_headers(login(client, "T-100", "mat-dev-01"))
    student = auth_headers(login(client, "S-100", "mat-dev-02"))

    created = _upload(client, teacher, world["offering"])
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["kind"] == "pdf"
    assert body["download_url"]
    assert body["file_name"] == "lecture-1.pdf"

    listed = client.get(f"/api/v1/offerings/{world['offering']}/materials", headers=student)
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert len(items) == 1

    download = client.get(items[0]["download_url"])
    assert download.status_code == 200
    assert download.content == PDF_BYTES


def test_unpublished_material_hidden_from_students_but_visible_to_teacher(client):
    world = build_world()
    teacher = auth_headers(login(client, "T-100", "mat-dev-03"))
    student = auth_headers(login(client, "S-100", "mat-dev-04"))

    _upload(client, teacher, world["offering"], published=False)

    student_view = client.get(
        f"/api/v1/offerings/{world['offering']}/materials", headers=student
    ).json()["items"]
    assert student_view == []

    teacher_view = client.get(
        f"/api/v1/offerings/{world['offering']}/materials", headers=teacher
    ).json()["items"]
    assert len(teacher_view) == 1


def test_upload_rejects_unsupported_type_and_oversize(client, monkeypatch):
    world = build_world()
    teacher = auth_headers(login(client, "T-100", "mat-dev-05"))

    bad_type = _upload(client, teacher, world["offering"], content=b"MZ", mime="application/x-msdownload")
    assert bad_type.status_code == 400
    assert bad_type.json()["code"] == "file_must_be_pdf"

    monkeypatch.setattr(settings, "max_upload_bytes", 10)
    too_big = _upload(client, teacher, world["offering"], content=b"x" * 64)
    assert too_big.status_code == 413
    assert too_big.json()["code"] == "file_too_large"

    monkeypatch.setattr(settings, "max_upload_bytes", 25 * 1024 * 1024)
    not_pdf = _upload(client, teacher, world["offering"], content=b"GIF89a", mime="image/gif")
    assert not_pdf.status_code == 400
    assert not_pdf.json()["code"] == "file_must_be_pdf"


def test_link_material_requires_valid_url(client):
    world = build_world()
    teacher = auth_headers(login(client, "T-100", "mat-dev-06"))

    missing = _upload(client, teacher, world["offering"], kind="video_link", content=None)
    assert missing.status_code == 400
    assert missing.json()["code"] == "url_required"

    bad = _upload(
        client, teacher, world["offering"], kind="link", content=None, url="ftp://x/y"
    )
    assert bad.status_code == 400

    ok = _upload(
        client,
        teacher,
        world["offering"],
        kind="video_link",
        content=None,
        url="https://example.edu/lecture",
    )
    assert ok.status_code == 200
    assert ok.json()["url"] == "https://example.edu/lecture"


def test_signed_link_rejects_tampered_and_expired(client):
    world = build_world()
    teacher = auth_headers(login(client, "T-100", "mat-dev-07"))
    body = _upload(client, teacher, world["offering"]).json()
    file_id = body["file_id"]

    tampered = client.get(body["download_url"][:-4] + "aaaa")
    assert tampered.status_code == 403
    assert tampered.json()["code"] == "invalid_or_expired_link"

    past_sig = _digest(file_id, 1)
    expired = client.get(f"/api/v1/files/{file_id}/download?expires=1&sig={past_sig}")
    assert expired.status_code == 403

    assert signed_path(file_id).startswith(f"/api/v1/files/{file_id}/download?")
