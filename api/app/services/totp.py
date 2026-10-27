# -*- coding: utf-8 -*-
"""المصادقة الثنائية TOTP (RFC 6238) — بلا اعتماديات خارجية.

الخوارزمية: HMAC-SHA1 على عدّاد زمني بخطوة 30 ثانية و6 أرقام، وهي المتوافقة
مع Google Authenticator وMicrosoft Authenticator وAuthy. نسمح بنافذة ±1 خطوة
(30 ثانية قبل/بعد) لتفاوت ساعات الهاتف، ونعيد رقم الخطوة المستهلكة كي يمنع
المستدعي إعادة استخدام الرمز نفسه.
"""
import base64
import hashlib
import hmac
import secrets
import struct
from datetime import datetime, timezone
from urllib.parse import quote, urlencode

DEFAULT_STEP_SECONDS = 30
DEFAULT_DIGITS = 6


def new_secret(length: int = 20) -> str:
    """سرّ عشوائي Base32 بلا حشو — الصيغة التي تقبلها تطبيقات المصادقة."""
    return base64.b32encode(secrets.token_bytes(length)).decode("ascii").rstrip("=")


def _key(secret: str) -> bytes:
    normalized = secret.strip().upper()
    padding = "=" * (-len(normalized) % 8)
    return base64.b32decode(normalized + padding, casefold=True)


def _code_for_counter(key: bytes, counter: int, digits: int) -> str:
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(binary % (10**digits)).zfill(digits)


def step_at(moment: datetime | None = None, *, step: int = DEFAULT_STEP_SECONDS) -> int:
    moment = moment or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return int(moment.timestamp()) // step


def code(
    secret: str,
    *,
    at: datetime | None = None,
    step: int = DEFAULT_STEP_SECONDS,
    digits: int = DEFAULT_DIGITS,
) -> str:
    """رمز اللحظة الحالية — يُستخدم في الاختبارات وفي عرض مثال للمستخدم."""
    return _code_for_counter(_key(secret), step_at(at, step=step), digits)


def verify(
    secret: str,
    candidate: str,
    *,
    at: datetime | None = None,
    step: int = DEFAULT_STEP_SECONDS,
    digits: int = DEFAULT_DIGITS,
    window: int = 1,
) -> int | None:
    """يتحقق من الرمز ويعيد رقم الخطوة إن صح، وإلا None.

    المقارنة بزمن ثابت (compare_digest) لمنع هجوم القياس الزمني.
    """
    normalized = "".join(ch for ch in (candidate or "") if ch.isdigit())
    if len(normalized) != digits:
        return None

    key = _key(secret)
    current = step_at(at, step=step)
    for offset in range(-window, window + 1):
        counter = current + offset
        if hmac.compare_digest(_code_for_counter(key, counter, digits), normalized):
            return counter
    return None


def provisioning_uri(secret: str, account: str, *, issuer: str = "CSIT") -> str:
    """رابط otpauth:// الذي يقرأه تطبيق المصادقة من رمز QR."""
    label = quote(f"{issuer}:{account}")
    query = urlencode(
        {
            "secret": secret,
            "issuer": issuer,
            "algorithm": "SHA1",
            "digits": DEFAULT_DIGITS,
            "period": DEFAULT_STEP_SECONDS,
        }
    )
    return f"otpauth://totp/{label}?{query}"
