# -*- coding: utf-8 -*-
"""الطلبات والمحادثة مع القسم (V2 في الخطة).

الطالب يفتح طلباً (استفسار/شكوى/وثيقة) فيُوجَّه إلى قسمه تلقائياً، ويجري
تبادل الرسائل داخل الطلب نفسه. رئيس القسم أو المدير يغيّر الحالة ويعيّن
مسؤولاً، وكل تغيير يُسجَّل في سجل التدقيق ويُشعر الطرف الآخر.

الخصوصية: الطالب يرى طلباته فقط، والموظف يرى طلبات قسمه أو ما أُسند إليه.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.errors import ApiError
from app.models import Department, Request, RequestMessage, Staff, Student, User
from app.models.enums import RequestStatus, UserRole
from app.services.audit import log_action
from app.services.notifications import notify_users

router = APIRouter(tags=["requests"])

CATEGORIES = {
    "academic": "مسألة أكاديمية",
    "schedule": "الجدول والقاعات",
    "grades": "درجة أو تقييم",
    "documents": "وثيقة أو تأييد",
    "other": "أخرى",
}


class RequestIn(BaseModel):
    category: str = Field(min_length=2, max_length=50)
    subject: str = Field(min_length=3, max_length=300)
    body: str = Field(min_length=5, max_length=4000)


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class RequestPatchIn(BaseModel):
    status: RequestStatus | None = None
    assigned_to: uuid.UUID | None = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _department_heads(db: Session, department_id: uuid.UUID) -> list[uuid.UUID]:
    return list(
        db.scalars(
            select(Staff.user_id)
            .join(User, User.id == Staff.user_id)
            .where(
                Staff.department_id == department_id,
                User.role == UserRole.DEPARTMENT_HEAD,
                User.deleted_at.is_(None),
            )
        )
    )


def _can_staff_access(db: Session, user: User, row: Request) -> bool:
    if user.role == UserRole.COLLEGE_ADMIN:
        return True
    if row.assigned_to == user.id:
        return True
    if user.role == UserRole.DEPARTMENT_HEAD:
        staff = db.get(Staff, user.id)
        return staff is not None and staff.department_id == row.department_id
    if user.role == UserRole.INSTRUCTOR:
        # التدريسي يرى ما أُسند إليه فقط (لا يرى شكاوى القسم كاملة)
        return row.assigned_to == user.id
    return False


def _request_payload(row: Request, messages: list[RequestMessage] | None = None) -> dict:
    payload = {
        "request_id": str(row.id),
        "category": row.category,
        "category_label": CATEGORIES.get(row.category, row.category),
        "subject": row.subject,
        "status": row.status.value,
        "assigned_to": str(row.assigned_to) if row.assigned_to else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }
    if messages is not None:
        payload["messages"] = [
            {
                "message_id": str(message.id),
                "sender_id": str(message.sender_id),
                "body": message.body,
                "created_at": message.created_at.isoformat() if message.created_at else None,
            }
            for message in messages
        ]
    return payload


def _load_request(db: Session, request_id: uuid.UUID) -> Request:
    row = db.get(Request, request_id)
    if row is None or row.deleted_at is not None:
        raise ApiError(404, "request_not_found", "الطلب غير موجود")
    return row


def _messages(db: Session, request_id: uuid.UUID) -> list[RequestMessage]:
    return list(
        db.scalars(
            select(RequestMessage)
            .where(RequestMessage.request_id == request_id)
            .order_by(RequestMessage.created_at)
        )
    )


@router.post("/requests")
def create_request(
    body: RequestIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    student = db.get(Student, user.id)
    if student is None:
        raise ApiError(403, "not_a_student", "فتح الطلبات متاح للطلبة فقط")
    if body.category not in CATEGORIES:
        raise ApiError(400, "invalid_category", "تصنيف الطلب غير معروف")

    row = Request(
        student_id=user.id,
        department_id=student.department_id,
        category=body.category,
        subject=body.subject.strip(),
        status=RequestStatus.OPEN,
    )
    db.add(row)
    db.flush()
    db.add(RequestMessage(request_id=row.id, sender_id=user.id, body=body.body.strip()))

    department = db.get(Department, student.department_id)
    notify_users(
        db,
        _department_heads(db, student.department_id),
        type_="request_created",
        title="طلب جديد من طالب",
        body=f"{body.subject.strip()}\n{department.name_ar if department else ''}",
        data={"request_id": str(row.id)},
    )
    log_action(
        db,
        actor=user,
        action="request_created",
        entity="request",
        entity_id=str(row.id),
        after={"category": row.category, "department_id": str(row.department_id)},
    )
    db.commit()
    return _request_payload(row, _messages(db, row.id))


@router.get("/requests")
def list_requests(
    status: RequestStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    conditions = [Request.deleted_at.is_(None)]
    if user.role == UserRole.STUDENT:
        conditions.append(Request.student_id == user.id)
    elif user.role == UserRole.COLLEGE_ADMIN:
        pass
    elif user.role == UserRole.DEPARTMENT_HEAD:
        staff = db.get(Staff, user.id)
        department_id = staff.department_id if staff else None
        if department_id is None:
            return {"items": []}
        conditions.append(
            or_(Request.department_id == department_id, Request.assigned_to == user.id)
        )
    else:
        conditions.append(Request.assigned_to == user.id)

    if status is not None:
        conditions.append(Request.status == status)

    rows = list(
        db.scalars(
            select(Request)
            .where(*conditions)
            .order_by(Request.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    return {"items": [_request_payload(row) for row in rows]}


@router.get("/requests/{request_id}")
def get_request(
    request_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    row = _load_request(db, request_id)
    if user.role == UserRole.STUDENT:
        if row.student_id != user.id:
            raise ApiError(404, "request_not_found", "الطلب غير موجود")
    elif not _can_staff_access(db, user, row):
        raise ApiError(403, "forbidden", "لا تملك صلاحية على هذا الطلب")

    payload = _request_payload(row, _messages(db, row.id))
    payload["department_id"] = str(row.department_id)
    return payload


@router.post("/requests/{request_id}/messages")
def add_message(
    request_id: uuid.UUID,
    body: MessageIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    row = _load_request(db, request_id)
    is_owner = row.student_id == user.id
    if not is_owner and user.role == UserRole.STUDENT:
        raise ApiError(404, "request_not_found", "الطلب غير موجود")
    if not is_owner and not _can_staff_access(db, user, row):
        raise ApiError(403, "forbidden", "لا تملك صلاحية على هذا الطلب")
    if row.status in (RequestStatus.RESOLVED, RequestStatus.CLOSED):
        raise ApiError(409, "request_closed", "الطلب مغلق؛ افتح طلباً جديداً")

    message = RequestMessage(
        request_id=row.id, sender_id=user.id, body=body.body.strip()
    )
    db.add(message)

    # أول رد من موظف ينقل الطلب تلقائياً إلى «قيد المعالجة»
    if not is_owner and row.status == RequestStatus.OPEN:
        row.status = RequestStatus.IN_PROGRESS

    recipients: list[uuid.UUID]
    if is_owner:
        recipients = [row.assigned_to] if row.assigned_to else _department_heads(
            db, row.department_id
        )
        title = "رد جديد على طلبك"
    else:
        recipients = [row.student_id]
        title = "رد من القسم على طلبك"
    notify_users(
        db,
        [value for value in recipients if value is not None and value != user.id],
        type_="request_message",
        title=title,
        body=f"{row.subject}: {body.body.strip()[:120]}",
        data={"request_id": str(row.id)},
    )
    db.commit()
    return _request_payload(row, _messages(db, row.id))


@router.patch("/admin/requests/{request_id}")
def update_request(
    request_id: uuid.UUID,
    body: RequestPatchIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """تغيير الحالة أو الإسناد — لرئيس القسم ومدير الكلية (والمسند إليه)."""
    row = _load_request(db, request_id)
    if user.role == UserRole.STUDENT:
        raise ApiError(403, "forbidden", "هذا الإجراء للتدريسي والإدارة")
    if not _can_staff_access(db, user, row):
        raise ApiError(403, "forbidden", "لا تملك صلاحية على هذا الطلب")

    before = {"status": row.status.value, "assigned_to": str(row.assigned_to) if row.assigned_to else None}
    if body.status is not None:
        row.status = body.status
    if body.assigned_to is not None:
        assignee = db.get(User, body.assigned_to)
        if assignee is None or assignee.deleted_at is not None:
            raise ApiError(404, "assignee_not_found", "المستخدم غير موجود")
        row.assigned_to = assignee.id
        notify_users(
            db,
            [assignee.id],
            type_="request_assigned",
            title="أُسند إليك طلب",
            body=row.subject,
            data={"request_id": str(row.id)},
        )

    log_action(
        db,
        actor=user,
        action="request_updated",
        entity="request",
        entity_id=str(row.id),
        before=before,
        after={
            "status": row.status.value,
            "assigned_to": str(row.assigned_to) if row.assigned_to else None,
        },
    )
    db.commit()
    return _request_payload(row, _messages(db, row.id))
