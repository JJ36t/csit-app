# -*- coding: utf-8 -*-
"""تخزين الملفات على القرص: تحقق النوع/الحجم، مفتاح تخزين عشوائي، وبصمة تحقق.

القاعدة الأمنية: لا يُستخدم اسم الملف الأصلي في المسار إطلاقاً (منع الاجتياز)،
ويُبنى المسار من مفتاح عشوائي داخل `settings.upload_dir` فقط.
"""
import hashlib
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.errors import ApiError

# أنواع مسموحة للمواد (البادئة تكفي: pdf، صور، صوت/فيديو، Office، نص)
ALLOWED_MIME_PREFIXES = (
    "application/pdf",
    "image/",
    "video/",
    "audio/",
    "text/plain",
    "application/vnd.openxmlformats-officedocument",
    "application/vnd.ms-",
    "application/msword",
)


def upload_root() -> Path:
    root = Path(settings.upload_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


async def save_upload(upload: UploadFile) -> dict:
    """يحفظ الملف ويعيد بيانات السجل (بلا كتابة في قاعدة البيانات)."""
    mime = (upload.content_type or "").lower().strip()
    if not mime or not mime.startswith(ALLOWED_MIME_PREFIXES):
        raise ApiError(
            400,
            "unsupported_file_type",
            "نوع الملف غير مدعوم؛ المسموح PDF أو صورة أو فيديو أو مستند",
        )

    data = await upload.read()
    if not data:
        raise ApiError(400, "empty_file", "الملف فارغ")
    if len(data) > settings.max_upload_bytes:
        raise ApiError(
            413,
            "file_too_large",
            f"حجم الملف يتجاوز الحد ({settings.max_upload_bytes // (1024 * 1024)}MB)",
        )

    suffix = Path(upload.filename or "").suffix.lower()
    if len(suffix) > 10 or not suffix.isascii():
        suffix = ""
    storage_key = f"{uuid.uuid4().hex}{suffix}"
    (upload_root() / storage_key).write_bytes(data)

    return {
        "storage_key": storage_key,
        "original_name": (upload.filename or "file")[:255],
        "mime": mime,
        "size": len(data),
        "checksum": hashlib.sha256(data).hexdigest(),
    }


def resolve_path(storage_key: str) -> Path:
    """مسار آمن داخل مجلد الرفع فقط — وإلا 404 بدل كشف المسارات."""
    root = upload_root()
    path = (root / storage_key).resolve()
    if path.parent != root:
        raise ApiError(404, "file_not_found", "الملف غير موجود")
    if not path.is_file():
        raise ApiError(404, "file_not_found", "الملف غير موجود")
    return path


def delete_file(storage_key: str) -> None:
    root = upload_root()
    path = (root / storage_key).resolve()
    if path.parent == root and path.is_file():
        path.unlink(missing_ok=True)
