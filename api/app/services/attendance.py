# -*- coding: utf-8 -*-
"""منطق الحضور: رموز QR متجددة (HMAC)، حساب المسافة، وتحديد الحالة."""
import hashlib
import hmac
import math
import secrets
from datetime import datetime

# هامش نافذة الرمز: نقبل الرمز الحالي والنافذة السابقة/التالية (تأخير الشبكة)
DEFAULT_TOLERANCE = 1


def new_secret() -> str:
    return secrets.token_urlsafe(32)


def window_for(now: datetime, rotation_s: int) -> int:
    return int(now.timestamp()) // max(1, rotation_s)


def make_token(secret: str, session_id: str, window: int) -> str:
    message = f"{session_id}:{window}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return f"{window}.{digest[:16]}"


def parse_token(token: str) -> tuple[int, str] | None:
    try:
        window_raw, sig = token.split(".", 1)
        return int(window_raw), sig
    except (ValueError, AttributeError):
        return None


def token_status(
    *,
    secret: str,
    session_id: str,
    token: str,
    rotation_s: int,
    tolerance: int,
    now: datetime,
) -> str:
    """يعيد: ok | stale (منتهٍ) | invalid (تالف أو مستقبلي)."""
    parsed = parse_token(token)
    if parsed is None:
        return "invalid"

    window, _sig = parsed
    current = window_for(now, rotation_s)
    if window > current + tolerance:
        return "invalid"

    expected = make_token(secret, session_id, window)
    if not hmac.compare_digest(expected, token):
        return "invalid"
    if window < current - tolerance:
        return "stale"
    return "ok"


def distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """المسافة بالأمتار بين نقطتين (هافرساين)."""
    radius = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))
