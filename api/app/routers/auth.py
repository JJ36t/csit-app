# -*- coding: utf-8 -*-
"""المصادقة: دخول، تجديد، خروج، تغيير كلمة المرور، والملف الشخصي (القسم 9 من الخطة)."""
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_current_user
from app.errors import ApiError
from app.models import Department, Device, FcmToken, Group, RefreshToken, Staff, Student, User
from app.models.enums import DeviceStatus, UserRole, UserStatus
from app.services.audit import log_action
from app.schemas import (
    DepartmentRef,
    LoginOut,
    StaffProfile,
    StudentProfile,
    TokenPair,
    UserProfile,
)
from app.security import (
    as_utc,
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# حدّ معدل بسيط في الذاكرة (نسخة واحدة). يُستبدل بـ Redis عند التوسع.
_attempts: dict[str, deque[float]] = defaultdict(deque)


def _guard_rate_limit(key: str) -> None:
    """يمنع تجاوز حدّ المحاولات — يُحسب الفشل فقط، والنجاح يصفّر العدّاد."""
    if not settings.rate_limit_enabled:
        return
    now = time.monotonic()
    window = _attempts[key]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.login_attempts_per_minute:
        raise ApiError(
            429,
            "too_many_attempts",
            "محاولات دخول كثيرة خلال دقيقة واحدة؛ انتظر قليلاً ثم أعد المحاولة",
        )


def _record_login_failure(key: str) -> None:
    if settings.rate_limit_enabled:
        _attempts[key].append(time.monotonic())


def _clear_login_failures(key: str) -> None:
    _attempts.pop(key, None)


class DeviceIn(BaseModel):
    fingerprint: str = Field(min_length=8, max_length=255)
    model: str | None = Field(default=None, max_length=120)
    platform: str | None = Field(default=None, max_length=20)


class LoginIn(BaseModel):
    university_id: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=1, max_length=128)
    device: DeviceIn
    fcm_token: str | None = Field(default=None, max_length=255)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=200)


class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


def _bind_device(db: Session, user: User, body: DeviceIn) -> Device:
    """جهاز نشط واحد لكل حساب: نفس البصمة تمر، وجهاز مختلف يحتاج إعادة ضبط من القسم."""
    active = list(
        db.scalars(
            select(Device).where(
                Device.user_id == user.id, Device.status == DeviceStatus.ACTIVE
            )
        )
    )
    for device in active:
        if device.device_fingerprint == body.fingerprint:
            if body.model:
                device.model = body.model
            return device

    if active:
        raise ApiError(
            403,
            "device_change_requires_approval",
            "هذا الحساب مرتبط بجهاز آخر. لتغيير الجهاز راجع قسمك لإعادة ضبط الربط",
        )

    existing = db.scalar(
        select(Device).where(Device.device_fingerprint == body.fingerprint)
    )
    if existing is not None:
        if existing.user_id != user.id:
            raise ApiError(
                403,
                "device_belongs_to_another_account",
                "هذا الجهاز مرتبط بحساب آخر",
            )
        existing.status = DeviceStatus.ACTIVE
        existing.bound_at = datetime.now(timezone.utc)
        if body.model:
            existing.model = body.model
        return existing

    device = Device(
        user_id=user.id,
        device_fingerprint=body.fingerprint,
        model=body.model,
        bound_at=datetime.now(timezone.utc),
        status=DeviceStatus.ACTIVE,
    )
    db.add(device)
    db.flush()
    return device


def _upsert_fcm_token(db: Session, user: User, device: Device, token: str) -> None:
    row = db.scalar(select(FcmToken).where(FcmToken.token == token))
    now = datetime.now(timezone.utc)
    if row is None:
        db.add(
            FcmToken(
                user_id=user.id,
                device_id=device.id,
                token=token,
                last_seen_at=now,
            )
        )
    else:
        row.user_id = user.id
        row.device_id = device.id
        row.last_seen_at = now


def build_profile(db: Session, user: User) -> UserProfile:
    student_profile: StudentProfile | None = None
    staff_profile: StaffProfile | None = None

    if user.role == UserRole.STUDENT:
        student = db.get(Student, user.id)
        if student is not None:
            department = db.get(Department, student.department_id)
            group = db.get(Group, student.group_id) if student.group_id else None
            student_profile = StudentProfile(
                stage=student.stage,
                study_type=student.study_type,
                department=(
                    DepartmentRef(code=department.code, name_ar=department.name_ar)
                    if department
                    else None
                ),
                group_name=group.name if group else None,
            )
    else:
        staff = db.get(Staff, user.id)
        if staff is not None:
            department = (
                db.get(Department, staff.department_id) if staff.department_id else None
            )
            staff_profile = StaffProfile(
                academic_title=staff.academic_title,
                department=(
                    DepartmentRef(code=department.code, name_ar=department.name_ar)
                    if department
                    else None
                ),
            )

    return UserProfile(
        id=user.id,
        university_id=user.university_id,
        full_name_ar=user.full_name_ar,
        role=user.role,
        status=user.status,
        must_change_password=user.must_change_password,
        student=student_profile,
        staff=staff_profile,
    )


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)) -> LoginOut:
    client_ip = request.client.host if request.client else "unknown"
    limit_key = f"{body.university_id}|{client_ip}"
    _guard_rate_limit(limit_key)

    user = db.scalar(
        select(User).where(
            User.university_id == body.university_id, User.deleted_at.is_(None)
        )
    )
    if user is None or not verify_password(body.password, user.password_hash):
        _record_login_failure(limit_key)
        log_action(
            db,
            actor=None,
            action="login_failed",
            entity="user",
            entity_id=body.university_id,
            after={"reason": "invalid_credentials"},
            ip=client_ip,
            commit=True,
        )
        raise ApiError(401, "invalid_credentials", "الرقم الجامعي أو كلمة المرور غير صحيحة")
    if user.status != UserStatus.ACTIVE:
        raise ApiError(403, "account_inactive", "الحساب غير مفعّل؛ راجع قسمك")

    try:
        device = _bind_device(db, user, body.device)
    except ApiError as exc:
        if exc.code == "device_change_requires_approval":
            log_action(
                db,
                actor=user,
                action="device_change_denied",
                entity="device",
                entity_id=body.device.fingerprint,
                after={"reason": exc.code},
                ip=client_ip,
                commit=True,
            )
        raise
    if body.fcm_token:
        _upsert_fcm_token(db, user, device, body.fcm_token)

    refresh_raw = new_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            device_id=device.id,
            token_hash=hash_refresh_token(refresh_raw),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_days),
        )
    )
    user.last_login_at = datetime.now(timezone.utc)
    log_action(
        db,
        actor=user,
        action="login_success",
        entity="user",
        entity_id=user.university_id,
        after={"device": device.device_fingerprint},
        ip=client_ip,
    )
    db.commit()
    _clear_login_failures(limit_key)

    access_token, expires_in = create_access_token(
        user_id=str(user.id), role=user.role.value, device_id=str(device.id)
    )
    return LoginOut(
        access_token=access_token,
        expires_in=expires_in,
        refresh_token=refresh_raw,
        user=build_profile(db, user),
        device_id=device.id,
    )


@router.post("/refresh", response_model=TokenPair)
def refresh_tokens(body: RefreshIn, db: Session = Depends(get_db)) -> TokenPair:
    row = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(body.refresh_token)
        )
    )
    if row is None:
        raise ApiError(401, "invalid_refresh_token", "رمز التجديد غير صالح؛ أعد تسجيل الدخول")

    if row.revoked_at is not None:
        # إعادة استخدام رمز ملغى = احتمال سرقة جلسة → إنهاء كل الجلسات
        now = datetime.now(timezone.utc)
        for token in db.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == row.user_id, RefreshToken.revoked_at.is_(None)
            )
        ):
            token.revoked_at = now
        db.commit()
        raise ApiError(
            401,
            "refresh_token_reused",
            "أُعيد استخدام رمز تجديد ملغى؛ أُنهيت كل الجلسات لأسباب أمنية",
        )

    if as_utc(row.expires_at) < datetime.now(timezone.utc):
        raise ApiError(401, "refresh_token_expired", "انتهت صلاحية رمز التجديد؛ أعد تسجيل الدخول")

    user = db.get(User, row.user_id)
    device = db.get(Device, row.device_id)
    if user is None or user.deleted_at is not None or user.status != UserStatus.ACTIVE:
        raise ApiError(403, "account_inactive", "الحساب غير مفعّل؛ راجع قسمك")
    if device is None or device.status != DeviceStatus.ACTIVE:
        raise ApiError(401, "device_not_active", "أُلغي ربط هذا الجهاز؛ راجع قسمك")

    row.revoked_at = datetime.now(timezone.utc)
    new_raw = new_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            device_id=device.id,
            token_hash=hash_refresh_token(new_raw),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_days),
        )
    )
    db.commit()

    access_token, expires_in = create_access_token(
        user_id=str(user.id), role=user.role.value, device_id=str(device.id)
    )
    return TokenPair(
        access_token=access_token, expires_in=expires_in, refresh_token=new_raw
    )


@router.post("/logout")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    now = datetime.now(timezone.utc)
    for token in db.scalars(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
        )
    ):
        token.revoked_at = now
    db.commit()
    return {"ok": True}


@router.post("/change-password")
def change_password(
    body: ChangePasswordIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not verify_password(body.current_password, user.password_hash):
        raise ApiError(400, "wrong_current_password", "كلمة المرور الحالية غير صحيحة")
    if body.new_password == body.current_password:
        raise ApiError(400, "same_password", "كلمة المرور الجديدة يجب أن تختلف عن الحالية")
    if body.new_password == user.university_id:
        raise ApiError(400, "weak_password", "لا يمكن استخدام الرقم الجامعي كلمة مرور")

    user.password_hash = hash_password(body.new_password)
    user.must_change_password = False

    # إلغاء كل الجلسات عند تغيير كلمة المرور (سياسة الخطة)
    now = datetime.now(timezone.utc)
    for token in db.scalars(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
        )
    ):
        token.revoked_at = now
    log_action(
        db,
        actor=user,
        action="password_changed",
        entity="user",
        entity_id=user.university_id,
        after={"must_change_password": False},
    )
    db.commit()
    return {"ok": True, "reauth_required": True}


@router.get("/me", response_model=UserProfile)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserProfile:
    return build_profile(db, user)
