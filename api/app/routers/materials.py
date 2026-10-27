# -*- coding: utf-8 -*-
"""المواد الدراسية والملفات (N3).

- التدريسي يرفع ملفاً (PDF/عرض) أو رابطاً، مع تحقق النوع والحجم.
- الطالب المسجَّل يرى المنشور فقط، ويُنزّل عبر رابط موقّع قصير العمر.
- روابط التنزيل تحمل `expires` و`sig` بلا كشف مسار أو اسم داخلي.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_current_user
from app.errors import ApiError
from app.models import Course, CourseOffering, Material, StoredFile, User
from app.models.enums import MaterialKind
from app.services.access import require_enrollment, require_offering_staff
from app.services.audit import log_action
from app.services.file_links import signed_path, verify
from app.services.notifications import notify_offering_students
from app.services.storage import delete_file, resolve_path, save_upload

router = APIRouter(tags=["materials"])


def _offering_or_404(db: Session, offering_id: uuid.UUID) -> CourseOffering:
    offering = db.get(CourseOffering, offering_id)
    if offering is None:
        raise ApiError(404, "offering_not_found", "المادة غير موجودة")
    return offering


def _material_payload(material: Material, file_row: StoredFile | None) -> dict:
    payload = {
        "material_id": str(material.id),
        "offering_id": str(material.offering_id),
        "title": material.title,
        "kind": material.kind.value,
        "week_no": material.week_no,
        "is_published": bool(material.is_published),
        "url": material.url,
        "file_id": str(material.file_id) if material.file_id else None,
        "download_url": None,
    }
    if file_row is not None:
        payload["download_url"] = signed_path(str(file_row.id))
        payload["file_name"] = file_row.original_name
        payload["file_size"] = file_row.size
    return payload


@router.post("/offerings/{offering_id}/materials")
async def create_material(
    offering_id: uuid.UUID,
    title: str = Form(min_length=2, max_length=300),
    kind: MaterialKind = Form(),
    file: UploadFile | None = File(default=None),
    url: str | None = Form(default=None),
    week_no: int | None = Form(default=None),
    is_published: bool = Form(default=False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    offering = _offering_or_404(db, offering_id)
    require_offering_staff(db, user, offering)

    if week_no is not None and not (1 <= week_no <= 30):
        raise ApiError(400, "invalid_week", "رقم الأسبوع يجب أن يكون بين 1 و30")

    file_row: StoredFile | None = None
    if kind == MaterialKind.PDF:
        if file is None:
            raise ApiError(400, "file_required", "مواد PDF تتطلب ملفاً مرفوعاً")
        if (file.content_type or "").lower() != "application/pdf":
            raise ApiError(400, "file_must_be_pdf", "نوع المادة PDF يتطلب ملف PDF")
        saved = await save_upload(file)
        file_row = StoredFile(**saved, uploader_id=user.id)
        db.add(file_row)
        db.flush()
        material = Material(
            offering_id=offering.id,
            title=title.strip(),
            kind=kind,
            file_id=file_row.id,
            week_no=week_no,
            is_published=is_published,
        )
    else:
        if not url or not url.startswith(("http://", "https://")):
            raise ApiError(400, "url_required", "مواد الرابط تتطلب رابطاً يبدأ بـhttp(s)://")
        if len(url) > 500:
            raise ApiError(400, "url_too_long", "الرابط أطول من 500 محرف")
        material = Material(
            offering_id=offering.id,
            title=title.strip(),
            kind=kind,
            url=url,
            week_no=week_no,
            is_published=is_published,
        )

    db.add(material)
    db.flush()
    log_action(
        db,
        actor=user,
        action="material_created",
        entity="material",
        entity_id=str(material.id),
        after={
            "title": material.title,
            "kind": material.kind.value,
            "offering_id": str(offering.id),
            "is_published": bool(material.is_published),
            "file_id": str(material.file_id) if material.file_id else None,
        },
    )
    db.commit()
    return _material_payload(material, file_row)


@router.get("/offerings/{offering_id}/materials")
def list_materials(
    offering_id: uuid.UUID,
    updated_since: datetime | None = Query(
        default=None, description="مزامنة جزئية: ما تغيّر بعد هذا الوقت فقط"
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    offering = _offering_or_404(db, offering_id)

    is_staff = offering.instructor_id == user.id
    if not is_staff:
        try:
            require_offering_staff(db, user, offering)
            is_staff = True
        except ApiError:
            require_enrollment(db, user, offering.id)

    query = select(Material).where(
        Material.offering_id == offering.id,
        Material.deleted_at.is_(None),
    )
    if not is_staff:
        query = query.where(Material.is_published.is_(True))
    if updated_since is not None:
        query = query.where(Material.updated_at > updated_since)
    materials = list(db.scalars(query.order_by(Material.week_no, Material.created_at)))

    files = {
        row.id: row
        for row in db.scalars(
            select(StoredFile).where(
                StoredFile.id.in_([item.file_id for item in materials if item.file_id] or [uuid.uuid4()])
            )
        )
    }
    course = db.get(Course, offering.course_id)

    return {
        "offering_id": str(offering.id),
        "course_code": course.code if course else "",
        "course_name_ar": course.name_ar if course else "",
        "server_time": datetime.now(timezone.utc).isoformat(),
        "items": [
            _material_payload(item, files.get(item.file_id)) for item in materials
        ],
    }


@router.delete("/materials/{material_id}")
def delete_material(
    material_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    material = db.get(Material, material_id)
    if material is None or material.deleted_at is not None:
        raise ApiError(404, "material_not_found", "المادة غير موجودة")
    offering = _offering_or_404(db, material.offering_id)
    require_offering_staff(db, user, offering)

    material.deleted_at = datetime.now(timezone.utc)
    log_action(
        db,
        actor=user,
        action="material_deleted",
        entity="material",
        entity_id=str(material.id),
        before={"title": material.title},
    )
    db.commit()
    return {"material_id": str(material.id), "deleted": True}


@router.get("/files/{file_id}/download")
def download_file(
    file_id: uuid.UUID,
    expires: int,
    sig: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    """تنزيل برابط موقّع قصير العمر (بلا رمز وصول — الرابط نفسه هو الإذن)."""
    if not verify(str(file_id), expires, sig):
        raise ApiError(
            403, "invalid_or_expired_link", "رابط التنزيل غير صالح أو منتهٍ؛ أعد طلب الملف"
        )

    file_row = db.get(StoredFile, file_id)
    if file_row is None or file_row.deleted_at is not None:
        raise ApiError(404, "file_not_found", "الملف غير موجود")

    path = resolve_path(file_row.storage_key)
    return FileResponse(
        path,
        media_type=file_row.mime,
        filename=file_row.original_name or file_row.storage_key,
    )


def cleanup_material_file(db: Session, material: Material) -> None:
    """حذف الملف الفيزيائي عند حذفه نهائياً (يُستدعى من سكربت الصيانة)."""
    if material.file_id is None:
        return
    file_row = db.get(StoredFile, material.file_id)
    if file_row is None:
        return
    delete_file(file_row.storage_key)
    db.delete(file_row)
    db.commit()


class MaterialPatchIn(BaseModel):
    """تعديل جزئي لمادة: العنوان/الأسبوع/الرابط/النشر — لا يُستبدل الملف."""

    title: str | None = Field(default=None, min_length=2, max_length=300)
    week_no: int | None = Field(default=None, ge=1, le=30)
    is_published: bool | None = None
    url: str | None = Field(default=None, max_length=500)


@router.patch("/materials/{material_id}")
def update_material(
    material_id: uuid.UUID,
    body: MaterialPatchIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    material = db.get(Material, material_id)
    if material is None or material.deleted_at is not None:
        raise ApiError(404, "material_not_found", "المادة غير موجودة")
    offering = _offering_or_404(db, material.offering_id)
    require_offering_staff(db, user, offering)

    before = {
        "title": material.title,
        "week_no": material.week_no,
        "is_published": bool(material.is_published),
        "url": material.url,
    }
    became_published = False

    if body.title is not None:
        material.title = body.title.strip()
    if body.week_no is not None:
        material.week_no = body.week_no
    if body.url is not None:
        if material.kind == MaterialKind.PDF:
            raise ApiError(400, "url_not_allowed", "مادة PDF لا تقبل رابطاً؛ استبدل الملف برفع جديد")
        if not body.url.startswith(("http://", "https://")):
            raise ApiError(400, "invalid_url", "الرابط يجب أن يبدأ بـhttp(s)://")
        material.url = body.url
    if body.is_published is not None and bool(material.is_published) != body.is_published:
        material.is_published = body.is_published
        became_published = body.is_published

    if became_published:
        course = db.get(Course, offering.course_id)
        notify_offering_students(
            db,
            offering.id,
            type_="material_published",
            title="مادة جديدة في مقررك",
            body=f"{material.title} — {course.name_ar if course else ''}",
            data={"material_id": str(material.id), "offering_id": str(offering.id)},
        )

    log_action(
        db,
        actor=user,
        action="material_updated",
        entity="material",
        entity_id=str(material.id),
        before=before,
        after={
            "title": material.title,
            "week_no": material.week_no,
            "is_published": bool(material.is_published),
            "url": material.url,
        },
    )
    db.commit()
    file_row = db.get(StoredFile, material.file_id) if material.file_id else None
    return _material_payload(material, file_row)
