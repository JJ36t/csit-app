# -*- coding: utf-8 -*-
"""تبعيات المصادقة والصلاحيات: التحقق من رمز الوصول، الجهاز، والدور."""
import uuid

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ApiError
from app.models import Device, User
from app.models.enums import DeviceStatus, UserRole, UserStatus
from app.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise ApiError(401, "not_authenticated", "يلزم تسجيل الدخول")

    try:
        payload = decode_access_token(creds.credentials)
    except jwt.ExpiredSignatureError as exc:
        raise ApiError(401, "access_token_expired", "انتهت صلاحية الجلسة؛ جدّد الدخول") from exc
    except jwt.PyJWTError as exc:
        raise ApiError(401, "invalid_access_token", "رمز الدخول غير صالح") from exc

    if payload.get("typ") != "access":
        raise ApiError(401, "invalid_access_token", "رمز الدخول غير صالح")

    try:
        user_id = uuid.UUID(str(payload.get("sub")))
        device_id = uuid.UUID(str(payload.get("dev")))
    except (ValueError, TypeError) as exc:
        raise ApiError(401, "invalid_access_token", "رمز الدخول غير صالح") from exc

    user = db.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise ApiError(401, "user_not_found", "الحساب غير موجود")
    if user.status != UserStatus.ACTIVE:
        raise ApiError(403, "account_inactive", "الحساب غير مفعّل؛ راجع قسمك")

    device = db.get(Device, device_id)
    if device is None or device.user_id != user.id or device.status != DeviceStatus.ACTIVE:
        raise ApiError(401, "device_not_active", "أُلغي ربط هذا الجهاز؛ راجع قسمك")

    return user


def require_roles(*roles: UserRole):
    """تبعية صلاحيات: تمر فقط إن كان دور المستخدم ضمن الأدوار المسموحة."""

    def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ApiError(403, "forbidden", "لا تملك صلاحية لهذا الإجراء")
        return user

    return _dependency
