# -*- coding: utf-8 -*-
"""واجهات الهوية الرقمية: إصدار بطاقة للطالب، والتحقق منها أمام القاعة/الامتحان."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.errors import ApiError
from app.models import Department, Group, Student, User
from app.models.enums import UserRole
from app.services import identity
from app.services.audit import log_action

router = APIRouter(tags=["identity"])

VERIFIER_ROLES = (UserRole.INSTRUCTOR, UserRole.DEPARTMENT_HEAD, UserRole.COLLEGE_ADMIN)


class VerifyIn(BaseModel):
    card: str = Field(min_length=20, max_length=2000)


@router.get("/me/identity-card")
def my_identity_card(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    student = db.get(Student, user.id)
    if student is None:
        raise ApiError(403, "not_a_student", "البطاقة الرقمية للطلبة فقط")

    department = db.get(Department, student.department_id)
    group = db.get(Group, student.group_id) if student.group_id else None
    payload = identity.build_payload(
        user_id=user.id,
        university_id=user.university_id,
        full_name_ar=user.full_name_ar,
        department_name=department.name_ar if department else None,
        stage=student.stage,
        group_name=group.name if group else None,
        study_type=student.study_type.value,
    )
    card, expires_at = identity.issue(payload)
    return {
        "card": card,
        "expires_at": expires_at.isoformat(),
        "ttl_seconds": int((expires_at - datetime.now(timezone.utc)).total_seconds()),
        "profile": {
            "university_id": user.university_id,
            "full_name_ar": user.full_name_ar,
            "department": department.name_ar if department else None,
            "stage": student.stage,
            "group": group.name if group else None,
        },
    }


@router.post("/identity/verify")
def verify_card(
    body: VerifyIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """يتحقق التدريسي/الإدارة من بطاقة الطالب — ويُسجَّل كل تحقق في التدقيق."""
    if user.role not in VERIFIER_ROLES:
        raise ApiError(403, "forbidden", "التحقق من البطاقة متاح للتدريسي والإدارة")

    payload = identity.read(body.card)
    try:
        student_user = db.get(User, uuid.UUID(str(payload.get("uid"))))
    except (ValueError, TypeError) as exc:
        raise ApiError(400, "invalid_card", "معرّف الطالب في البطاقة غير صالح") from exc

    if student_user is None or student_user.deleted_at is not None:
        raise ApiError(404, "student_not_found", "الطالب غير موجود في النظام")
    if student_user.university_id != payload.get("sid"):
        raise ApiError(400, "card_mismatch", "بيانات البطاقة لا تطابق سجل الطالب")

    student = db.get(Student, student_user.id)
    department = db.get(Department, student.department_id) if student else None

    log_action(
        db,
        actor=user,
        action="identity_verified",
        entity="user",
        entity_id=student_user.university_id,
        after={"exp": payload.get("exp"), "nonce": payload.get("nonce")},
        ip=request.client.host if request.client else None,
        commit=True,
    )
    return {
        "valid": True,
        "student": {
            "university_id": student_user.university_id,
            "full_name_ar": student_user.full_name_ar,
            "department": department.name_ar if department else payload.get("dept"),
            "stage": payload.get("stage"),
            "group": payload.get("grp"),
            "study_type": payload.get("study"),
        },
        "issued_at": datetime.fromtimestamp(int(payload["iat"]), timezone.utc).isoformat(),
        "expires_at": datetime.fromtimestamp(int(payload["exp"]), timezone.utc).isoformat(),
    }
