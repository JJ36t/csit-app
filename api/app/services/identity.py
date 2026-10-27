# -*- coding: utf-8 -*-
"""الهوية الرقمية: بطاقة QR موقّعة تُثبت أن الطالب هو صاحب الحساب.

الفكرة: لا نكشف كلمة مرور ولا صورة هوية، بل رمزاً قصير العمر يحمل الحد الأدنى
من البيانات (الاسم، القسم، المرحلة، الشعبة) وموقّعاً بمفتاح الخادم. جهاز
التدريسي (أو بوابة القاعة) يتحقق من التوقيع فيثبت أن البطاقة صادرة من النظام
ولم تنتهِ صلاحيتها، فلا تنفع لقطة شاشة قديمة أو بطاقة معدّلة.

الصيغة: ``CSIT1.<base64url(payload)>.<base64url(hmac_sha256)>``
- التوقيع على النص المرمّز نفسه (لا على JSON) لتفادي فروق التسلسل.
- مدة الصلاحية قصيرة (3 دقائق افتراضياً) وتُعرض عدّاداً في التطبيق.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import settings
from app.errors import ApiError

PREFIX = "CSIT1"


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64d(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def _sign(payload_segment: str) -> str:
    digest = hmac.new(
        settings.identity_secret.encode("utf-8"),
        payload_segment.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64e(digest)


def issue(payload: dict[str, Any], *, ttl_seconds: int | None = None) -> tuple[str, datetime]:
    """يبني البطاقة ويعيد (النص، وقت الانتهاء)."""
    now = datetime.now(timezone.utc)
    ttl = ttl_seconds if ttl_seconds is not None else settings.identity_card_ttl_seconds
    expires_at = now + timedelta(seconds=max(ttl, 30))
    body = {
        **payload,
        "v": 1,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "nonce": secrets.token_hex(4),
    }
    segment = _b64e(
        json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    return f"{PREFIX}.{segment}.{_sign(segment)}", expires_at


def read(text: str) -> dict[str, Any]:
    """يتحقق من التوقيع والصلاحية ويعيد الحمولة — أو يرمي 400/410."""
    parts = (text or "").strip().split(".")
    if len(parts) != 3 or parts[0] != PREFIX:
        raise ApiError(400, "invalid_card", "البطاقة ليست بطاقة هوية صادرة من التطبيق")

    segment, signature = parts[1], parts[2]
    if not hmac.compare_digest(_sign(segment), signature):
        raise ApiError(400, "invalid_card_signature", "توقيع البطاقة غير صالح")

    try:
        body = json.loads(_b64d(segment).decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ApiError(400, "invalid_card", "تعذّر قراءة بيانات البطاقة") from exc

    if int(body.get("exp", 0)) <= int(datetime.now(timezone.utc).timestamp()):
        raise ApiError(
            410, "card_expired", "انتهت صلاحية البطاقة؛ اطلب من الطالب تحديثها في تطبيقه"
        )
    return body


def build_payload(
    *,
    user_id: uuid.UUID,
    university_id: str,
    full_name_ar: str,
    department_name: str | None,
    stage: int | None,
    group_name: str | None,
    study_type: str | None,
) -> dict[str, Any]:
    return {
        "uid": str(user_id),
        "sid": university_id,
        "name": full_name_ar,
        "dept": department_name,
        "stage": stage,
        "grp": group_name,
        "study": study_type,
    }
