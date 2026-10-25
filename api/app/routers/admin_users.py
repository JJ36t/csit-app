# -*- coding: utf-8 -*-
"""إدارة المستخدمين من لوحة التحكم: إعادة ضبط ربط الجهاز وكلمة المرور.

مصفوفة الصلاحيات (القسم 3 من الخطة): مدير الكلية لأي مستخدم،
ورئيس القسم لطلاب قسمه فقط.
"""
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_roles
from app.errors import ApiError
from app.models import Device, RefreshToken, Staff, Student, User
from app.models.enums import DeviceStatus, UserRole
from app.security import hash_password
from app.services.audit import log_action

router = APIRouter(prefix="/admin/users", tags=["admin-users"])

MANAGER_ROLES = (UserRole.COLLEGE_ADMIN, UserRole.DEPARTMENT_HEAD)


def _load_target(db: Session, university_id: str, actor: User) -> User:
    target = db.scalar(
        select(User).where(
            User.university_id == university_id, User.deleted_at.is_(None)
        )
    )
    if target is None:
        raise ApiError(404, "user_not_found", "لا يوجد مستخدم بهذا الرقم الجامعي")

    if actor.role == UserRole.DEPARTMENT_HEAD:
        staff = db.get(Staff, actor.id)
        student = db.get(Student, target.id)
        if (
            staff is None
            or staff.department_id is None
            or student is None
            or student.department_id != staff.department_id
        ):
            raise ApiError(
                403, "outside_your_department", "هذا المستخدم خارج قسمك"
            )
    return target


def _revoke_sessions(db: Session, user: User) -> int:
    now = datetime.now(timezone.utc)
    count = 0
    for token in db.scalars(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
        )
    ):
        token.revoked_at = now
        count += 1
    return count


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/{university_id}/device/reset")
def reset_device(
    university_id: str,
    request: Request,
    actor: User = Depends(require_roles(*MANAGER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    """إلغاء ربط كل أجهزة المستخدم وإنهاء جلساته — بعد موافقة القسم على تغيير الجهاز."""
    target = _load_target(db, university_id, actor)

    devices = list(db.scalars(select(Device).where(Device.user_id == target.id)))
    revoked = 0
    for device in devices:
        if device.status == DeviceStatus.ACTIVE:
            revoked += 1
        device.status = DeviceStatus.REVOKED

    sessions = _revoke_sessions(db, target)
    log_action(
        db,
        actor=actor,
        action="device_reset",
        entity="user",
        entity_id=target.university_id,
        before={"devices": len(devices), "active": revoked},
        after={"active": 0, "sessions_revoked": sessions},
        ip=_client_ip(request),
    )
    db.commit()
    return {"ok": True, "devices_revoked": revoked, "sessions_revoked": sessions}


@router.post("/{university_id}/reset-password")
def reset_password(
    university_id: str,
    request: Request,
    actor: User = Depends(require_roles(*MANAGER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    """كلمة مرور مؤقتة تُعرض مرة واحدة، مع إجبار التغيير عند أول دخول وإنهاء الجلسات."""
    target = _load_target(db, university_id, actor)

    temporary = secrets.token_urlsafe(6)[:10]
    target.password_hash = hash_password(temporary)
    target.must_change_password = True
    sessions = _revoke_sessions(db, target)

    log_action(
        db,
        actor=actor,
        action="password_reset",
        entity="user",
        entity_id=target.university_id,
        after={"must_change_password": True, "sessions_revoked": sessions},
        ip=_client_ip(request),
    )
    db.commit()
    return {
        "ok": True,
        "temporary_password": temporary,
        "sessions_revoked": sessions,
    }
