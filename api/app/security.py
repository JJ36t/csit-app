# -*- coding: utf-8 -*-
"""أدوات الأمان: تجزئة كلمات المرور (bcrypt)، رموز JWT، وتجزئة رموز التجديد."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.config import settings


def hash_password(password: str, *, rounds: int | None = None) -> str:
    cost = rounds or 12
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=cost)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(*, user_id: str, role: str, device_id: str) -> tuple[str, int]:
    """يصدر رمز وصول قصير العمر (15 دقيقة افتراضياً) ويعيد (الرمز، عمره بالثواني)."""
    expires_in = settings.access_token_minutes * 60
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "dev": device_id,
        "typ": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    """يرفع jwt.PyJWTError عند رمز تالف أو منتهٍ."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def as_utc(value: datetime) -> datetime:
    """SQLite يعيد التواريخ بلا منطقة زمنية — نوحّدها إلى UTC قبل أي مقارنة."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
