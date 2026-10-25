# -*- coding: utf-8 -*-
"""الدرجات والتقييمات (المرحلة 5 من الخطة — قرار #3).

الدورة: التدريسي ينشئ التقييم ← يُدخل الدرجات كمسودة ← الكلية تنشر بموافقة.
كل إدخال/تعديل/نشر يُسجَّل في `audit_logs`، والطالب لا يرى إلا المنشور.
"""
import io
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.errors import ApiError
from app.models import (
    Assessment,
    Course,
    CourseOffering,
    Enrollment,
    Grade,
    User,
)
from app.models.enums import (
    AssessmentKind,
    EnrollmentStatus,
    UserRole,
)
from app.services.access import (
    require_enrollment,
    require_offering_staff,
    require_student_row,
)
from app.services.audit import log_action
from app.services.notifications import notify_offering_students

router = APIRouter(tags=["grades"])

MAX_SCORE_LIMIT = Decimal("1000")
WEIGHT_LIMIT = Decimal("100")


# ----------------------------- نماذج الطلب -----------------------------

class AssessmentIn(BaseModel):
    offering_id: uuid.UUID
    name: str = Field(min_length=2, max_length=200)
    kind: AssessmentKind = AssessmentKind.QUIZ
    max_score: Decimal = Field(default=Decimal("100"), gt=0, le=MAX_SCORE_LIMIT)
    weight: Decimal = Field(default=Decimal("0"), ge=0, le=WEIGHT_LIMIT)


class GradeRowIn(BaseModel):
    student_id: uuid.UUID
    score: Decimal = Field(ge=0, le=MAX_SCORE_LIMIT)


class GradesIn(BaseModel):
    rows: list[GradeRowIn] = Field(min_length=1, max_length=500)


# ----------------------------- أدوات -----------------------------

def _offering_or_404(db: Session, offering_id: uuid.UUID) -> CourseOffering:
    offering = db.get(CourseOffering, offering_id)
    if offering is None:
        raise ApiError(404, "offering_not_found", "المادة غير موجودة")
    return offering


def _assessment_or_404(db: Session, assessment_id: uuid.UUID) -> Assessment:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None or assessment.deleted_at is not None:
        raise ApiError(404, "assessment_not_found", "التقييم غير موجود")
    return assessment


def _weight_used(db: Session, offering_id: uuid.UUID, exclude_id: uuid.UUID | None = None) -> Decimal:
    query = select(func.coalesce(func.sum(Assessment.weight), 0)).where(
        Assessment.offering_id == offering_id,
        Assessment.deleted_at.is_(None),
    )
    if exclude_id is not None:
        query = query.where(Assessment.id != exclude_id)
    return Decimal(db.scalar(query) or 0)


def _assessment_payload(assessment: Assessment) -> dict:
    return {
        "assessment_id": str(assessment.id),
        "offering_id": str(assessment.offering_id),
        "name": assessment.name,
        "kind": assessment.kind.value,
        "max_score": float(assessment.max_score),
        "weight": float(assessment.weight),
        "is_published": bool(assessment.is_published),
    }


def _enrolled_students(db: Session, offering_id: uuid.UUID) -> list[tuple]:
    return db.execute(
        select(User.id, User.university_id, User.full_name_ar)
        .join(Enrollment, Enrollment.student_id == User.id)
        .where(
            Enrollment.offering_id == offering_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        .order_by(User.full_name_ar)
    ).all()


def _weighted_total(
    assessments: list[Assessment], scores: dict[uuid.UUID, Decimal]
) -> tuple[float, float]:
    total = Decimal("0")
    weight_sum = Decimal("0")
    for assessment in assessments:
        if assessment.weight <= 0:
            continue
        weight_sum += assessment.weight
        score = scores.get(assessment.id)
        if score is None or assessment.max_score <= 0:
            continue
        total += (score / assessment.max_score) * assessment.weight
    return float(round(total, 2)), float(round(weight_sum, 2))


# ----------------------------- التقييمات -----------------------------

@router.post("/assessments")
def create_assessment(
    body: AssessmentIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    offering = _offering_or_404(db, body.offering_id)
    require_offering_staff(db, user, offering)

    used = _weight_used(db, offering.id)
    if used + body.weight > WEIGHT_LIMIT:
        raise ApiError(
            400,
            "weight_exceeds_100",
            f"مجموع أوزان التقييمات سيتجاوز 100 (المستخدم {used} من 100)",
            {"used": float(used)},
        )

    assessment = Assessment(
        offering_id=offering.id,
        name=body.name.strip(),
        kind=body.kind,
        max_score=body.max_score,
        weight=body.weight,
    )
    db.add(assessment)
    db.flush()
    log_action(
        db,
        actor=user,
        action="assessment_created",
        entity="assessment",
        entity_id=str(assessment.id),
        after={
            "name": assessment.name,
            "kind": assessment.kind.value,
            "max_score": float(assessment.max_score),
            "weight": float(assessment.weight),
            "offering_id": str(offering.id),
        },
    )
    db.commit()
    return _assessment_payload(assessment)


@router.delete("/assessments/{assessment_id}")
def delete_assessment(
    assessment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    assessment = _assessment_or_404(db, assessment_id)
    offering = _offering_or_404(db, assessment.offering_id)
    require_offering_staff(db, user, offering)
    if assessment.is_published:
        raise ApiError(409, "assessment_published", "لا يمكن حذف تقييم منشور")

    assessment.deleted_at = datetime.now(timezone.utc)
    log_action(
        db,
        actor=user,
        action="assessment_deleted",
        entity="assessment",
        entity_id=str(assessment.id),
        before={"name": assessment.name},
    )
    db.commit()
    return {"assessment_id": str(assessment.id), "deleted": True}


# ----------------------------- إدخال الدرجات -----------------------------

@router.post("/assessments/{assessment_id}/grades")
def enter_grades(
    assessment_id: uuid.UUID,
    body: GradesIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """إدخال/تعديل دفعي كمسودة — لا يرى الطالب شيئاً قبل نشر التقييم."""
    assessment = _assessment_or_404(db, assessment_id)
    offering = _offering_or_404(db, assessment.offering_id)
    require_offering_staff(db, user, offering)
    if assessment.is_published:
        raise ApiError(
            409,
            "assessment_published",
            "التقييم منشور؛ لا يمكن تعديل درجاته. راجع الكلية لإعادة الفتح",
        )

    enrolled = {
        student_id
        for student_id, _uid, _name in _enrolled_students(db, offering.id)
    }
    existing = {
        grade.student_id: grade
        for grade in db.scalars(
            select(Grade).where(Grade.assessment_id == assessment.id)
        )
    }

    created = 0
    updated = 0
    for row in body.rows:
        if row.student_id not in enrolled:
            raise ApiError(
                400,
                "student_not_enrolled",
                "أحد الطلاب غير مسجَّل في هذه المادة",
                {"student_id": str(row.student_id)},
            )
        if row.score > assessment.max_score:
            raise ApiError(
                400,
                "score_exceeds_max",
                "درجة أحد الطلاب تتجاوز الدرجة العظمى للتقييم",
                {"student_id": str(row.student_id), "max_score": float(assessment.max_score)},
            )

        grade = existing.get(row.student_id)
        if grade is None:
            grade = Grade(
                assessment_id=assessment.id,
                student_id=row.student_id,
                score=row.score,
                entered_by=user.id,
            )
            db.add(grade)
            db.flush()
            existing[row.student_id] = grade
            created += 1
            log_action(
                db,
                actor=user,
                action="grade_entered",
                entity="grade",
                entity_id=str(grade.id),
                after={
                    "assessment_id": str(assessment.id),
                    "student_id": str(row.student_id),
                    "score": float(row.score),
                },
            )
        elif grade.score != row.score:
            before = float(grade.score)
            grade.score = row.score
            grade.entered_by = user.id
            updated += 1
            log_action(
                db,
                actor=user,
                action="grade_updated",
                entity="grade",
                entity_id=str(grade.id),
                before={"score": before},
                after={
                    "assessment_id": str(assessment.id),
                    "student_id": str(row.student_id),
                    "score": float(row.score),
                },
            )

    db.commit()
    return {
        "assessment_id": str(assessment.id),
        "created": created,
        "updated": updated,
        "unchanged": len(body.rows) - created - updated,
    }


# ----------------------------- النشر -----------------------------

@router.post("/assessments/{assessment_id}/publish")
def publish_assessment(
    assessment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """نشر بموافقة الكلية: مدير الكلية فقط، مع إشعار الطلاب المسجَّلين وتدقيق."""
    if user.role != UserRole.COLLEGE_ADMIN:
        raise ApiError(403, "not_college_admin", "نشر الدرجات يتطلب موافقة مدير الكلية")

    assessment = _assessment_or_404(db, assessment_id)
    offering = _offering_or_404(db, assessment.offering_id)
    if assessment.is_published:
        raise ApiError(409, "already_published", "هذا التقييم منشور مسبقاً")

    grades_count = db.scalar(
        select(func.count()).select_from(Grade).where(Grade.assessment_id == assessment.id)
    )
    if not grades_count:
        raise ApiError(400, "no_grades", "لا توجد درجات مُدخلة لهذا التقييم")

    assessment.is_published = True
    course = db.get(Course, offering.course_id)
    notified = notify_offering_students(
        db,
        offering.id,
        type_="grades_published",
        title="نُشرت درجات تقييم",
        body=f"{assessment.name} — {course.name_ar if course else ''}".strip(),
        data={"assessment_id": str(assessment.id), "offering_id": str(offering.id)},
    )
    log_action(
        db,
        actor=user,
        action="assessment_published",
        entity="assessment",
        entity_id=str(assessment.id),
        after={
            "name": assessment.name,
            "grades_count": int(grades_count),
            "notified": notified,
        },
    )
    db.commit()
    return {
        "assessment_id": str(assessment.id),
        "is_published": True,
        "notified": notified,
    }


# ----------------------------- قراءة التدريسي -----------------------------

@router.get("/offerings/{offering_id}/grades")
def offering_grades(
    offering_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    offering = _offering_or_404(db, offering_id)
    require_offering_staff(db, user, offering)
    course = db.get(Course, offering.course_id)

    assessments = list(
        db.scalars(
            select(Assessment)
            .where(
                Assessment.offering_id == offering.id,
                Assessment.deleted_at.is_(None),
            )
            .order_by(Assessment.created_at)
        )
    )
    grades: dict[uuid.UUID, dict[uuid.UUID, Decimal]] = {}
    for grade in db.scalars(
        select(Grade).where(
            Grade.assessment_id.in_([item.id for item in assessments] or [uuid.uuid4()])
        )
    ):
        grades.setdefault(grade.student_id, {})[grade.assessment_id] = grade.score

    students = []
    for student_id, university_id, full_name in _enrolled_students(db, offering.id):
        scores = grades.get(student_id, {})
        total, weight_sum = _weighted_total(assessments, scores)
        students.append(
            {
                "student_id": str(student_id),
                "university_id": university_id,
                "full_name_ar": full_name,
                "scores": {
                    str(assessment_id): float(score)
                    for assessment_id, score in scores.items()
                },
                "weighted_total": total,
                "weight_sum": weight_sum,
            }
        )

    return {
        "offering_id": str(offering.id),
        "course_code": course.code if course else "",
        "course_name_ar": course.name_ar if course else "",
        "assessments": [_assessment_payload(item) for item in assessments],
        "students": students,
    }


# ----------------------------- قراءة الطالب -----------------------------

@router.get("/grades")
def my_grades(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    require_student_row(db, user)
    enrollments = list(
        db.scalars(
            select(Enrollment).where(
                Enrollment.student_id == user.id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
    )

    items = []
    for enrollment in enrollments:
        offering = db.get(CourseOffering, enrollment.offering_id)
        course = db.get(Course, offering.course_id)
        assessments = list(
            db.scalars(
                select(Assessment)
                .where(
                    Assessment.offering_id == offering.id,
                    Assessment.deleted_at.is_(None),
                    Assessment.is_published.is_(True),
                )
                .order_by(Assessment.created_at)
            )
        )
        scores = {
            grade.assessment_id: grade.score
            for grade in db.scalars(
                select(Grade).where(
                    Grade.student_id == user.id,
                    Grade.assessment_id.in_([item.id for item in assessments] or [uuid.uuid4()]),
                )
            )
        }
        total, weight_sum = _weighted_total(assessments, scores)
        items.append(
            {
                "offering_id": str(offering.id),
                "course_code": course.code if course else "",
                "course_name_ar": course.name_ar if course else "",
                "assessments": [
                    {
                        "assessment_id": str(item.id),
                        "name": item.name,
                        "kind": item.kind.value,
                        "max_score": float(item.max_score),
                        "weight": float(item.weight),
                        "score": float(scores[item.id]) if item.id in scores else None,
                    }
                    for item in assessments
                ],
                "weighted_total": total,
                "weight_sum": weight_sum,
            }
        )

    return {"items": items}


# ----------------------------- تصدير Excel -----------------------------

@router.get("/offerings/{offering_id}/grades/export")
def export_grades(
    offering_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    offering = _offering_or_404(db, offering_id)
    require_offering_staff(db, user, offering)
    course = db.get(Course, offering.course_id)

    assessments = list(
        db.scalars(
            select(Assessment)
            .where(
                Assessment.offering_id == offering.id,
                Assessment.deleted_at.is_(None),
            )
            .order_by(Assessment.created_at)
        )
    )
    scores: dict[uuid.UUID, dict[uuid.UUID, Decimal]] = {}
    for grade in db.scalars(
        select(Grade).where(
            Grade.assessment_id.in_([item.id for item in assessments] or [uuid.uuid4()])
        )
    ):
        scores.setdefault(grade.student_id, {})[grade.assessment_id] = grade.score

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "الدرجات"
    sheet.sheet_view.rightToLeft = True

    header = ["الرقم الجامعي", "الاسم"]
    for item in assessments:
        max_txt = f"{item.max_score.normalize():f}"
        weight_txt = f"{item.weight.normalize():f}"
        header.append(f"{item.name} (/{max_txt}) ×{weight_txt}")
    header.append("المجموع الموزون")
    sheet.append(header)

    for student_id, university_id, full_name in _enrolled_students(db, offering.id):
        student_scores = scores.get(student_id, {})
        total, _weight_sum = _weighted_total(assessments, student_scores)
        row = [university_id, full_name]
        for item in assessments:
            score = student_scores.get(item.id)
            row.append(float(score) if score is not None else None)
        row.append(total)
        sheet.append(row)

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    code = (course.code if course else "offering").replace(" ", "_")
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="grades-{code}.xlsx"'
        },
    )
