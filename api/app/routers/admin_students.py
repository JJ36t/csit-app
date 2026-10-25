# -*- coding: utf-8 -*-
"""إدارة الطلاب: الاستيراد من Excel مع تقرير الأخطاء، القالب الجاهز، وقائمة الطلاب."""
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import require_roles
from app.errors import ApiError
from app.models import Department, Group, Staff, Student, User
from app.models.enums import StudyType, UserRole
from app.services.audit import log_action
from app.services.import_students import build_template, import_students

router = APIRouter(prefix="/admin/students", tags=["admin-students"])

ADMIN_ROLES = (UserRole.COLLEGE_ADMIN, UserRole.DEPARTMENT_HEAD)


@router.post("/import")
def import_from_excel(
    request: Request,
    file: UploadFile = File(..., description="ملف xlsx وفق القالب"),
    dry_run: bool = Query(default=True, description="فحص فقط دون إنشاء حسابات"),
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    filename = (file.filename or "").lower()
    if not filename.endswith(".xlsx"):
        raise ApiError(400, "invalid_file_type", "يجب أن يكون الملف بصيغة xlsx")

    content = file.file.read(settings.max_import_bytes + 1)
    if len(content) > settings.max_import_bytes:
        raise ApiError(413, "file_too_large", "حجم الملف يتجاوز الحد المسموح (5 ميغابايت)")
    if not content:
        raise ApiError(400, "empty_file", "الملف فارغ")

    result = import_students(db, content, dry_run=dry_run, actor=user)
    log_action(
        db,
        actor=user,
        action="students_import",
        entity="students",
        entity_id=filename,
        after={
            "dry_run": dry_run,
            "rows_total": result.rows_total,
            "rows_valid": result.rows_valid,
            "created": len(result.created),
        },
        ip=request.client.host if request.client else None,
        commit=True,
    )
    return {
        "dry_run": dry_run,
        "rows_total": result.rows_total,
        "rows_valid": result.rows_valid,
        "rows_invalid": result.rows_invalid,
        "created_count": len(result.created),
        "created": result.created,
        "groups_created": result.groups_created,
        "errors": [issue.as_dict() for issue in result.errors],
        "errors_truncated": result.truncated,
    }


@router.get("/template")
def download_template(
    user: User = Depends(require_roles(*ADMIN_ROLES)),
) -> Response:
    return Response(
        content=build_template(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="students-template.xlsx"'},
    )


@router.get("")
def list_students(
    q: str | None = Query(default=None, max_length=100),
    department_code: str | None = Query(default=None, max_length=10),
    stage: int | None = Query(default=None, ge=1, le=6),
    study_type: StudyType | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    stmt = (
        select(User, Student, Department, Group)
        .join(Student, Student.user_id == User.id)
        .join(Department, Department.id == Student.department_id)
        .outerjoin(Group, Group.id == Student.group_id)
        .where(User.deleted_at.is_(None), User.role == UserRole.STUDENT)
    )

    if user.role == UserRole.DEPARTMENT_HEAD:
        staff = db.get(Staff, user.id)
        if staff is not None and staff.department_id is not None:
            stmt = stmt.where(Student.department_id == staff.department_id)

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(User.full_name_ar.ilike(like), User.university_id.ilike(like))
        )
    if department_code:
        stmt = stmt.where(Department.code == department_code.upper())
    if stage:
        stmt = stmt.where(Student.stage == stage)
    if study_type:
        stmt = stmt.where(Student.study_type == study_type)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(
        stmt.order_by(User.university_id).offset((page - 1) * limit).limit(limit)
    ).all()

    items = [
        {
            "university_id": u.university_id,
            "full_name_ar": u.full_name_ar,
            "department_code": d.code,
            "department_name_ar": d.name_ar,
            "stage": s.stage,
            "study_type": s.study_type.value,
            "group_name": g.name if g is not None else None,
            "status": u.status.value,
            "email": u.email,
            "phone": u.phone,
        }
        for u, s, d, g in rows
    ]
    return {"total": total, "page": page, "limit": limit, "items": items}
