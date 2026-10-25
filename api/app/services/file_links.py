# -*- coding: utf-8 -*-
"""روابط تنزيل موقّعة قصيرة العمر (HMAC-SHA256).

الرابط يحمل `expires` (Unix) و`sig`؛ لا يكشف اسم الملف ولا مساره،
وينتهي تلقائياً بعد `settings.file_link_ttl_minutes`.
"""
import hashlib
import hmac
import time

from app.config import settings

_PURPOSE = "csit:file-link"


def _digest(file_id: str, expires: int) -> str:
    message = f"{_PURPOSE}:{file_id}:{expires}".encode("utf-8")
    secret = (settings.jwt_secret + ":files").encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()[:32]


def signed_path(file_id: str, *, ttl_minutes: int | None = None) -> str:
    """مسار التنزيل الموقّع (نسبة إلى جذر الـAPI)."""
    ttl = settings.file_link_ttl_minutes if ttl_minutes is None else ttl_minutes
    expires = int(time.time()) + max(1, ttl) * 60
    return (
        f"{settings.api_v1_prefix}/files/{file_id}/download"
        f"?expires={expires}&sig={_digest(file_id, expires)}"
    )


def verify(file_id: str, expires: int, signature: str) -> bool:
    if expires < int(time.time()):
        return False
    return hmac.compare_digest(_digest(file_id, expires), signature)
