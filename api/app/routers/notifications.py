# -*- coding: utf-8 -*-
"""صندوق الإشعارات داخل التطبيق + تسجيل رمز FCM للجهاز (N3)."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.errors import ApiError
from app.models import Device, FcmToken, Notification, User
from app.models.enums import DeviceStatus

router = APIRouter(tags=["notifications"])


class FcmTokenIn(BaseModel):
    token: str = Field(min_length=8, max_length=255)
    device_id: uuid.UUID


def _payload(row: Notification) -> dict:
    return {
        "notification_id": str(row.id),
        "type": row.type,
        "title": row.title,
        "body": row.body,
        "data": row.data,
        "read": row.read_at is not None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _unread_count(db: Session, user: User) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        )
        or 0
    )


@router.get("/notifications")
def my_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    query = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    rows = list(
        db.scalars(query.order_by(Notification.created_at.desc()).limit(limit).offset(offset))
    )
    return {
        "items": [_payload(row) for row in rows],
        "unread_count": _unread_count(db, user),
    }


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(Notification, notification_id)
    if row is None or row.user_id != user.id:
        raise ApiError(404, "notification_not_found", "الإشعار غير موجود")
    if row.read_at is None:
        row.read_at = datetime.now(timezone.utc)
        db.commit()
    return {"notification_id": str(row.id), "read": True}


@router.post("/notifications/read-all")
def mark_all_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    now = datetime.now(timezone.utc)
    rows = list(
        db.scalars(
            select(Notification).where(
                Notification.user_id == user.id, Notification.read_at.is_(None)
            )
        )
    )
    for row in rows:
        row.read_at = now
    db.commit()
    return {"updated": len(rows), "unread_count": 0}


@router.put("/devices/fcm-token")
def update_fcm_token(
    body: FcmTokenIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """يسجّل/يحدّث رمز الإشعارات للجهاز المربوط النشط — الإرسال الفعلي عبر FCM لاحقاً."""
    device = db.get(Device, body.device_id)
    if device is None or device.user_id != user.id or device.status != DeviceStatus.ACTIVE:
        raise ApiError(403, "device_not_bound", "هذا الجهاز غير مربوط بحسابك")

    now = datetime.now(timezone.utc)
    row = db.scalar(select(FcmToken).where(FcmToken.token == body.token))
    if row is None:
        db.add(
            FcmToken(
                user_id=user.id,
                device_id=device.id,
                token=body.token,
                last_seen_at=now,
            )
        )
    else:
        row.user_id = user.id
        row.device_id = device.id
        row.last_seen_at = now
    db.commit()
    return {"ok": True}
