# -*- coding: utf-8 -*-
"""إدارة المستخدمين من لوحة التحكم: القائمة، إعادة ضبط ربط الجهاز وكلمة المرور.

مصفوفة الصلاحيات (القسم 3 من الخطة): مدير الكلية لأي مستخدم،
ورئيس القسم لطلاب قسمه فقط.
"""
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, literal, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_roles
from app.errors import ApiError
from app.models import (
    Department,
    Device,
    Group,
    RefreshToken,
    Staff,
    Student,
    User,
)
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


@router.get("")
def list_users(
    q: str | None = Query(default=None, max_length=100, description="اسم أو رقم جامعي"),
    role: UserRole | None = Query(default=None),
    department_code: str | None = Query(default=None, max_length=10),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    actor: User = Depends(require_roles(*MANAGER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    """قائمة المستخدمين غير المحذوفين: مدير الكلية يرى الكل، ورئيس القسم طلاب قسمه فقط.

    القسم والشعبة يُقرآن من بطاقة الطالب أو التدريسي، وحالة الجهاز من وجود جهاز نشط.
    لا يُرجع أي حقل سرّي (لا `password_hash` ولا التوكنات).
    """
    head_department_id = None
    if actor.role == UserRole.DEPARTMENT_HEAD:
        head_staff = db.get(Staff, actor.id)
        head_department_id = head_staff.department_id if head_staff is not None else None
        if head_department_id is None:
            # رئيس قسم بلا قسم محدد: لا نطاق له، وقائمة فارغة أكثر أماناً من عرض الجميع
            return {"total": 0, "page": page, "limit": limit, "items": []}

    # قسم المستخدم من بطاقة الطالب أو التدريسي (مدير الكلية قد لا يملك أيّهما)
    department_id = func.coalesce(Student.department_id, Staff.department_id)
    has_active_device = (
        select(literal(1))
        .where(Device.user_id == User.id, Device.status == DeviceStatus.ACTIVE)
        .exists()
        .label("has_active_device")
    )

    stmt = (
        select(User, Department, Group, has_active_device)
        .outerjoin(Student, Student.user_id == User.id)
        .outerjoin(Staff, Staff.user_id == User.id)
        .outerjoin(Department, Department.id == department_id)
        .outerjoin(Group, Group.id == Student.group_id)
        .where(User.deleted_at.is_(None))
    )

    if head_department_id is not None:
        stmt = stmt.where(Student.department_id == head_department_id)
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(User.full_name_ar.ilike(like), User.university_id.ilike(like))
        )
    if role is not None:
        stmt = stmt.where(User.role == role)
    if department_code:
        stmt = stmt.where(Department.code == department_code.upper())

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(
        stmt.order_by(User.university_id).offset((page - 1) * limit).limit(limit)
    ).all()

    items = [
        {
            "user_id": str(u.id),
            "university_id": u.university_id,
            "full_name_ar": u.full_name_ar,
            "role": u.role.value,
            "status": u.status.value,
            "must_change_password": bool(u.must_change_password),
            "department_code": d.code if d is not None else None,
            "department_name_ar": d.name_ar if d is not None else None,
            "group_name": g.name if g is not None else None,
            "device_status": "active" if has_device else "none",
        }
        for u, d, g, has_device in rows
    ]
    return {"total": total, "page": page, "limit": limit, "items": items}


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


@router.post("/{university_id}/2fa/reset")
def reset_totp(
    university_id: str,
    request: Request,
    actor: User = Depends(require_roles(*MANAGER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    """إعادة ضبط المصادقة الثنائية عند فقدان الهاتف — بموافقة الإدارة وسجل تدقيق."""
    target = _load_target(db, university_id, actor)
    was_enabled = bool(target.totp_enabled)

    target.totp_enabled = False
    target.totp_secret = None
    target.totp_confirmed_at = None
    target.totp_last_step = None

    log_action(
        db,
        actor=actor,
        action="totp_reset",
        entity="user",
        entity_id=target.university_id,
        before={"enabled": was_enabled},
        after={"enabled": False},
        ip=_client_ip(request),
    )
    db.commit()
    return {"ok": True, "was_enabled": was_enabled}
