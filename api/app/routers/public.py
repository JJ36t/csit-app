# -*- coding: utf-8 -*-
"""الأخبار العامة (بلا تسجيل) — صفحة الكلية على الويب وروابط المشاركة.

تُعرض إعلانات نطاق «الكلية» المنشورة وغير المنتهية فقط؛ لا تُسرَّب إعلانات
الأقسام أو الشعب لأنها موجّهة ولا تُفترض علنية.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Announcement
from app.models.enums import AnnouncementScope

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/news")
def public_news(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    now = datetime.now(timezone.utc)
    rows = list(
        db.scalars(
            select(Announcement)
            .where(
                Announcement.deleted_at.is_(None),
                Announcement.scope == AnnouncementScope.COLLEGE,
                or_(Announcement.publish_at.is_(None), Announcement.publish_at <= now),
                or_(Announcement.expires_at.is_(None), Announcement.expires_at > now),
            )
            .order_by(
                Announcement.pinned.desc(),
                func.coalesce(Announcement.publish_at, Announcement.created_at).desc(),
            )
            .limit(limit)
            .offset(offset)
        )
    )
    return {
        "items": [
            {
                "id": str(row.id),
                "title": row.title,
                "body": row.body,
                "pinned": bool(row.pinned),
                "priority": row.priority.value,
                "published_at": (
                    row.publish_at.isoformat()
                    if row.publish_at
                    else (row.created_at.isoformat() if row.created_at else None)
                ),
            }
            for row in rows
        ]
    }
