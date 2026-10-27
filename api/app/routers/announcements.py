# -*- coding: utf-8 -*-
"""الإعلانات (N3): إنشاء بنطاق (كلية/قسم/مرحلة/شعبة/مادة) بجدولة نشر،
وخلاصة الموجّه للمستخدم بعلامة «مقروء»، مع إشعارات صندوق وارد عند النشر.
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, false, func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, require_roles
from app.errors import ApiError
from app.models import (
    Announcement,
    AnnouncementRead,
    CourseOffering,
    Department,
    Enrollment,
    Group,
    Staff,
    Student,
    User,
)
from app.models.enums import (
    AnnouncementPriority,
    AnnouncementScope,
    EnrollmentStatus,
    UserRole,
)
from app.services.access import is_department_head_of, require_offering_staff
from app.services.audit import log_action
from app.services.notifications import (
    announcement_audience,
    notify_users,
    staff_offering_ids,
)

router = APIRouter(tags=["announcements"])

MANAGER_ROLES = (UserRole.COLLEGE_ADMIN, UserRole.DEPARTMENT_HEAD)


class AnnouncementIn(BaseModel):
    scope: AnnouncementScope
    scope_id: uuid.UUID | None = None
    stage: int | None = Field(default=None, ge=1, le=8)
    title: str = Field(min_length=3, max_length=300)
    body: str = Field(min_length=1, max_length=5000)
    priority: AnnouncementPriority = AnnouncementPriority.NORMAL
    pinned: bool = False
    publish_at: datetime | None = None
    expires_at: datetime | None = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _announcement_payload(row: Announcement, is_read: bool = False) -> dict:
    return {
        "announcement_id": str(row.id),
        "scope": row.scope.value,
        "scope_id": str(row.scope_id) if row.scope_id else None,
        "stage": row.stage,
        "title": row.title,
        "body": row.body,
        "priority": row.priority.value,
        "pinned": bool(row.pinned),
        "publish_at": row.publish_at.isoformat() if row.publish_at else None,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "is_read": is_read,
    }


def _require_scope_rights(db: Session, user: User, body: AnnouncementIn) -> None:
    """صلاحيات النشر: الكلية للمدير، القسم/المرحلة/الشعبة لرئيس القسم، والمادة لطاقمها."""
    scope = body.scope
    scope_id = body.scope_id

    if scope == AnnouncementScope.COLLEGE:
        if scope_id is not None:
            raise ApiError(400, "invalid_scope_id", "إعلان الكلية لا يقبل معرّف جهة")
        if user.role != UserRole.COLLEGE_ADMIN:
            raise ApiError(403, "not_allowed_scope", "إعلان على مستوى الكلية يتطلب مدير الكلية")
        return

    if scope in (AnnouncementScope.DEPARTMENT, AnnouncementScope.STAGE):
        if scope_id is None:
            raise ApiError(400, "scope_id_required", "حدّد القسم المستهدف")
        if db.get(Department, scope_id) is None:
            raise ApiError(404, "department_not_found", "القسم غير موجود")
        if scope == AnnouncementScope.STAGE and body.stage is None:
            raise ApiError(400, "stage_required", "حدّد المرحلة المستهدفة")
        if user.role == UserRole.COLLEGE_ADMIN:
            return
        if is_department_head_of(db, user, scope_id):
            return
        raise ApiError(403, "not_allowed_scope", "هذا النطاق متاح لرئيس القسم أو مدير الكلية")

    if scope == AnnouncementScope.GROUP:
        if scope_id is None:
            raise ApiError(400, "scope_id_required", "حدّد الشعبة المستهدفة")
        group = db.get(Group, scope_id)
        if group is None:
            raise ApiError(404, "group_not_found", "الشعبة غير موجودة")
        if user.role == UserRole.COLLEGE_ADMIN:
            return
        if is_department_head_of(db, user, group.department_id):
            return
        raise ApiError(403, "not_allowed_scope", "هذا النطاق متاح لرئيس القسم أو مدير الكلية")

    if scope == AnnouncementScope.OFFERING:
        if scope_id is None:
            raise ApiError(400, "scope_id_required", "حدّد المادة المستهدفة")
        offering = db.get(CourseOffering, scope_id)
        if offering is None:
            raise ApiError(404, "offering_not_found", "المادة غير موجودة")
        require_offering_staff(db, user, offering)
        return


def _can_manage(db: Session, user: User, row: Announcement) -> bool:
    if user.role == UserRole.COLLEGE_ADMIN:
        return True
    if row.scope == AnnouncementScope.COLLEGE:
        return False
    if row.scope in (AnnouncementScope.DEPARTMENT, AnnouncementScope.STAGE):
        return is_department_head_of(db, user, row.scope_id)
    if row.scope == AnnouncementScope.GROUP:
        group = db.get(Group, row.scope_id)
        return group is not None and is_department_head_of(db, user, group.department_id)
    if row.scope == AnnouncementScope.OFFERING:
        offering = db.get(CourseOffering, row.scope_id)
        return offering is not None and offering.instructor_id == user.id
    return False


def _visibility_condition(db: Session, user: User) -> Any:
    """شرط SQL لِما يراه المستخدم؛ None = كل الإعلانات (مدير الكلية)."""
    if user.role == UserRole.COLLEGE_ADMIN:
        return None

    conditions = []
    student = db.get(Student, user.id)
    if student is not None:
        conditions.append(Announcement.scope == AnnouncementScope.COLLEGE)
        conditions.append(
            and_(
                Announcement.scope == AnnouncementScope.DEPARTMENT,
                Announcement.scope_id == student.department_id,
            )
        )
        conditions.append(
            and_(
                Announcement.scope == AnnouncementScope.STAGE,
                Announcement.scope_id == student.department_id,
                Announcement.stage == student.stage,
            )
        )
        if student.group_id is not None:
            conditions.append(
                and_(
                    Announcement.scope == AnnouncementScope.GROUP,
                    Announcement.scope_id == student.group_id,
                )
            )
        offering_ids = list(
            db.scalars(
                select(Enrollment.offering_id).where(
                    Enrollment.student_id == user.id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
            )
        )
        if offering_ids:
            conditions.append(
                and_(
                    Announcement.scope == AnnouncementScope.OFFERING,
                    Announcement.scope_id.in_(offering_ids),
                )
            )
    else:
        staff = db.get(Staff, user.id)
        conditions.append(Announcement.scope == AnnouncementScope.COLLEGE)
        if staff is not None and staff.department_id is not None:
            conditions.append(
                and_(
                    Announcement.scope == AnnouncementScope.DEPARTMENT,
                    Announcement.scope_id == staff.department_id,
                )
            )
        offering_ids = staff_offering_ids(db, user)
        if offering_ids:
            conditions.append(
                and_(
                    Announcement.scope == AnnouncementScope.OFFERING,
                    Announcement.scope_id.in_(offering_ids),
                )
            )

    return or_(*conditions) if conditions else false()


# ----------------------------- إدارة -----------------------------

def _as_utc(value: datetime | None) -> datetime | None:
    """SQLite يعيد التواريخ بلا منطقة زمنية — نقرأها كما تُكتب: UTC."""
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _announcement_status(row: Announcement, now: datetime) -> str:
    """حالة مشتقة: مجدول قبل publish_at، منتهٍ بعد expires_at، وإلا نشط."""
    publish_at = _as_utc(row.publish_at)
    if publish_at is not None and publish_at > now:
        return "scheduled"
    expires_at = _as_utc(row.expires_at)
    if expires_at is not None and expires_at <= now:
        return "expired"
    return "active"


@router.get("/admin/announcements")
def list_admin_announcements(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_roles(*MANAGER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    """قائمة الإدارة: تشمل المجدولة والمنتهية (بخلاف الخلاصة الموجّهة) بلا المحذوفة."""
    conditions = [Announcement.deleted_at.is_(None)]
    if user.role == UserRole.DEPARTMENT_HEAD:
        staff = db.get(Staff, user.id)
        if staff is None or staff.department_id is None:
            conditions.append(Announcement.scope == AnnouncementScope.COLLEGE)
        else:
            conditions.append(
                or_(
                    Announcement.scope == AnnouncementScope.COLLEGE,
                    and_(
                        Announcement.scope == AnnouncementScope.DEPARTMENT,
                        Announcement.scope_id == staff.department_id,
                    ),
                )
            )

    rows = db.scalars(
        select(Announcement)
        .where(*conditions)
        .order_by(
            Announcement.pinned.desc(),
            func.coalesce(Announcement.publish_at, Announcement.created_at).desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    now = _utc_now()
    items = []
    for row in rows:
        payload = _announcement_payload(row)
        payload["status"] = _announcement_status(row, now)
        items.append(payload)
    return {"items": items}


@router.post("/admin/announcements")
def create_announcement(
    body: AnnouncementIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _require_scope_rights(db, user, body)

    publish_at = body.publish_at
    if publish_at is not None and publish_at.tzinfo is None:
        publish_at = publish_at.replace(tzinfo=timezone.utc)
    expires_at = body.expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if publish_at is not None and expires_at is not None and expires_at <= publish_at:
        raise ApiError(400, "invalid_window", "تاريخ الانتهاء يجب أن يكون بعد تاريخ النشر")

    row = Announcement(
        scope=body.scope,
        scope_id=body.scope_id,
        stage=body.stage,
        title=body.title.strip(),
        body=body.body.strip(),
        priority=body.priority,
        pinned=body.pinned,
        publish_at=publish_at,
        expires_at=expires_at,
        created_by=user.id,
    )
    db.add(row)
    db.flush()

    notified = 0
    now = _utc_now()
    if publish_at is None or publish_at <= now:
        notified = notify_users(
            db,
            announcement_audience(db, row),
            type_="announcement",
            title=row.title,
            body=row.body[:200],
            data={"announcement_id": str(row.id), "scope": row.scope.value},
        )

    log_action(
        db,
        actor=user,
        action="announcement_created",
        entity="announcement",
        entity_id=str(row.id),
        after={
            "scope": row.scope.value,
            "scope_id": str(row.scope_id) if row.scope_id else None,
            "stage": row.stage,
            "scheduled": publish_at is not None and publish_at > now,
            "notified": notified,
        },
    )
    db.commit()
    payload = _announcement_payload(row)
    payload["notified"] = notified
    payload["status"] = _announcement_status(row, _utc_now())
    return payload


@router.delete("/admin/announcements/{announcement_id}")
def delete_announcement(
    announcement_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(Announcement, announcement_id)
    if row is None or row.deleted_at is not None:
        raise ApiError(404, "announcement_not_found", "الإعلان غير موجود")
    if not _can_manage(db, user, row):
        raise ApiError(403, "not_allowed_scope", "لا تملك صلاحية حذف هذا الإعلان")

    row.deleted_at = _utc_now()
    log_action(
        db,
        actor=user,
        action="announcement_deleted",
        entity="announcement",
        entity_id=str(row.id),
        before={"title": row.title, "scope": row.scope.value},
    )
    db.commit()
    return {"announcement_id": str(row.id), "deleted": True}


# ----------------------------- الخلاصة -----------------------------

@router.get("/announcements")
def my_announcements(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    updated_since: datetime | None = Query(
        default=None, description="مزامنة جزئية: ما تغيّر بعد هذا الوقت فقط"
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    now = _utc_now()
    conditions = [
        Announcement.deleted_at.is_(None),
        or_(Announcement.publish_at.is_(None), Announcement.publish_at <= now),
        or_(Announcement.expires_at.is_(None), Announcement.expires_at > now),
    ]
    if updated_since is not None:
        conditions.append(Announcement.updated_at > updated_since)
    visibility = _visibility_condition(db, user)
    if visibility is not None:
        conditions.append(visibility)

    read_exists = (
        select(AnnouncementRead.id)
        .where(
            AnnouncementRead.announcement_id == Announcement.id,
            AnnouncementRead.user_id == user.id,
        )
        .exists()
    )
    rows = db.execute(
        select(Announcement, read_exists.label("is_read"))
        .where(*conditions)
        .order_by(
            Announcement.pinned.desc(),
            func.coalesce(Announcement.publish_at, Announcement.created_at).desc(),
        )
        .limit(limit)
        .offset(offset)
    ).all()

    return {
        "server_time": _utc_now().isoformat(),
        "items": [
            _announcement_payload(row, is_read=bool(is_read))
            for row, is_read in rows
        ],
    }


@router.post("/announcements/{announcement_id}/read")
def mark_read(
    announcement_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(Announcement, announcement_id)
    if row is None or row.deleted_at is not None:
        raise ApiError(404, "announcement_not_found", "الإعلان غير موجود")

    visibility = _visibility_condition(db, user)
    if visibility is not None:
        visible = db.scalar(
            select(Announcement.id).where(
                Announcement.id == row.id,
                Announcement.deleted_at.is_(None),
                visibility,
            )
        )
        if visible is None:
            raise ApiError(404, "announcement_not_found", "الإعلان غير موجود")

    existing = db.scalar(
        select(AnnouncementRead).where(
            AnnouncementRead.announcement_id == row.id,
            AnnouncementRead.user_id == user.id,
        )
    )
    if existing is None:
        db.add(AnnouncementRead(announcement_id=row.id, user_id=user.id))
        db.commit()
    return {"announcement_id": str(row.id), "is_read": True}
