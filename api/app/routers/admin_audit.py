# -*- coding: utf-8 -*-
"""سجل التدقيق — قراءة `audit_logs` بترشيح وترقيم للوحة التحكم.

سجل حساس: مدير الكلية فقط. العرض بالأحدث أولاً مع left join للمستخدم لبيان الفاعل.
`date_from`/`date_to` يومان محليان بتوقيت بغداد (UTC+3)، ويُحوَّلان إلى نافذة UTC.
"""
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_roles
from app.models import AuditLog, User
from app.models.enums import UserRole

router = APIRouter(prefix="/admin/audit", tags=["admin-audit"])

# سجل التدقيق يكشف نشاط كل المستخدمين — لا يُفتح لرؤساء الأقسام
READER_ROLES = (UserRole.COLLEGE_ADMIN,)

# توقيت بغداد ثابت UTC+3 (العراق بلا توقيت صيفي)
BAGHDAD = timezone(timedelta(hours=3), "Asia/Baghdad")


def _utc_iso(value: datetime | None) -> str | None:
    """SQLite يعيد تواريخ بلا منطقة زمنية؛ نعتبرها UTC حتى لا يخطئ العرض المحلي."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _baghdad_start(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=BAGHDAD).astimezone(timezone.utc)


def _apply_filters(
    stmt: Select,
    *,
    q: str | None,
    action: str | None,
    entity: str | None,
    actor: str | None,
    date_from: date | None,
    date_to: date | None,
) -> Select:
    if q:
        needle = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(AuditLog.entity_id.ilike(needle), AuditLog.action.ilike(needle))
        )
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity:
        stmt = stmt.where(AuditLog.entity == entity)
    if actor:
        stmt = stmt.where(func.lower(User.university_id) == actor.strip().lower())
    if date_from is not None:
        stmt = stmt.where(AuditLog.created_at >= _baghdad_start(date_from))
    if date_to is not None:
        # اليوم الأخير مشمول: النافذة تنتهي عند منتصف ليل اليوم التالي بتوقيت بغداد
        end = _baghdad_start(date_to + timedelta(days=1))
        stmt = stmt.where(AuditLog.created_at < end)
    return stmt


@router.get("")
def list_audit(
    q: str | None = Query(default=None, max_length=120, description="بحث في رقم الكيان أو الإجراء"),
    action: str | None = Query(default=None, max_length=100),
    entity: str | None = Query(default=None, max_length=50),
    actor: str | None = Query(default=None, max_length=20, description="الرقم الجامعي للفاعل"),
    date_from: date | None = Query(default=None, description="من تاريخ (بغداد) YYYY-MM-DD"),
    date_to: date | None = Query(default=None, description="إلى تاريخ (بغداد) YYYY-MM-DD"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_roles(*READER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    base = select(AuditLog).outerjoin(User, User.id == AuditLog.actor_id)
    base = _apply_filters(
        base,
        q=q,
        action=action,
        entity=entity,
        actor=actor,
        date_from=date_from,
        date_to=date_to,
    )

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    rows = db.execute(
        base.add_columns(User)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    items = []
    for log, actor_row in rows:
        items.append(
            {
                "audit_id": str(log.id),
                "created_at": _utc_iso(log.created_at),
                "actor_university_id": actor_row.university_id if actor_row else None,
                "actor_name_ar": actor_row.full_name_ar if actor_row else None,
                "action": log.action,
                "entity": log.entity,
                "entity_id": log.entity_id,
                "ip": log.ip,
                "before": log.before,
                "after": log.after,
            }
        )

    return {"total": total, "page": page, "limit": limit, "items": items}
