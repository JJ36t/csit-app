# -*- coding: utf-8 -*-
"""تقارير الحضور والدرجات للوحة التحكم (JSON للعرض، CSV للتنزيل في Excel).

النطاق: التدريسي يرى مواده، رئيس القسم مواد قسمه، والمدير الكل — عبر
`user_offering_ids` نفسها المستخدمة في بقية الشاشات.

ملاحظة القياس: «نسبة الحضور» تُحسب على المحاضرات المنعقدة فقط
(مغلقة أو انتهى وقتها)، ولا تُحسب المحاضرات القادمة ضد الطالب.
الحضور المتأخر يُحتسب حضوراً في النسبة، ويُعرض عموداً مستقلاً.
"""
import csv
import io
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_roles
from app.errors import ApiError
from app.models import (
    Assessment,
    AttendanceRecord,
    Course,
    CourseOffering,
    Enrollment,
    Grade,
    Group,
    LectureSession,
    Student,
    User,
)
from app.models.enums import (
    EnrollmentStatus,
    LectureSessionStatus,
    UserRole,
)
from app.services.access import user_offering_ids

router = APIRouter(prefix="/admin/reports", tags=["admin-reports"])

REPORT_ROLES = (UserRole.COLLEGE_ADMIN, UserRole.DEPARTMENT_HEAD, UserRole.INSTRUCTOR)
STATUSES = ("present", "late", "absent", "excused")


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _offering_or_403(db: Session, user: User, offering_id: uuid.UUID) -> CourseOffering:
    if offering_id not in set(user_offering_ids(db, user)):
        raise ApiError(403, "not_offering_staff", "لا تملك صلاحية على هذه المادة")
    offering = db.get(CourseOffering, offering_id)
    if offering is None or offering.deleted_at is not None:
        raise ApiError(404, "offering_not_found", "المادة غير موجودة")
    return offering


def _offering_header(db: Session, offering: CourseOffering) -> dict:
    course = db.get(Course, offering.course_id)
    group = db.get(Group, offering.group_id)
    instructor = db.get(User, offering.instructor_id) if offering.instructor_id else None
    return {
        "offering_id": str(offering.id),
        "course_code": course.code if course else "",
        "course_name_ar": course.name_ar if course else "",
        "group_name": group.name if group else "",
        "stage": group.stage if group else None,
        "kind": offering.session_kind.value,
        "instructor_name_ar": instructor.full_name_ar if instructor else None,
    }


def _csv_response(rows: list[list[str]], filename: str) -> Response:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    # BOM كي يفتح Excel العربية بترميز صحيح
    return Response(
        content="\ufeff" + buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/attendance", response_model=None)
def attendance_report(
    offering_id: uuid.UUID,
    format: str = Query(default="json", pattern="^(json|csv)$"),
    user: User = Depends(require_roles(*REPORT_ROLES)),
    db: Session = Depends(get_db),
) -> Response | dict:
    offering = _offering_or_403(db, user, offering_id)
    header = _offering_header(db, offering)

    sessions = list(
        db.scalars(
            select(LectureSession)
            .where(
                LectureSession.offering_id == offering.id,
                LectureSession.status != LectureSessionStatus.CANCELLED,
            )
            .order_by(LectureSession.starts_at)
        )
    )
    now = datetime.now(timezone.utc)
    held_ids = [
        session.id
        for session in sessions
        if session.status == LectureSessionStatus.CLOSED or _as_utc(session.ends_at) < now
    ]
    held = len(held_ids)

    students = db.execute(
        select(Student, User)
        .join(User, User.id == Student.user_id)
        .join(Enrollment, Enrollment.student_id == Student.user_id)
        .where(
            Enrollment.offering_id == offering.id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        .order_by(User.full_name_ar)
    ).all()

    records: dict[uuid.UUID, dict[str, int]] = {
        student.user_id: {status: 0 for status in STATUSES} for student, _ in students
    }
    if held_ids:
        for record in db.scalars(
            select(AttendanceRecord).where(AttendanceRecord.session_id.in_(held_ids))
        ):
            bucket = records.get(record.student_id)
            if bucket is not None and record.status.value in bucket:
                bucket[record.status.value] += 1

    totals = {status: 0 for status in STATUSES}
    items = []
    for student, account in students:
        counts = records[student.user_id]
        for status in STATUSES:
            totals[status] += counts[status]
        attended = counts["present"] + counts["late"]
        rate = round(attended * 100 / held, 1) if held else 0.0
        items.append(
            {
                "student_id": str(student.user_id),
                "university_id": account.university_id,
                "full_name_ar": account.full_name_ar,
                "present": counts["present"],
                "late": counts["late"],
                "absent": counts["absent"],
                "excused": counts["excused"],
                "attendance_rate": rate,
            }
        )

    overall_rate = (
        round((totals["present"] + totals["late"]) * 100 / (held * len(items)), 1)
        if held and items
        else 0.0
    )

    if format == "csv":
        rows = [
            ["المادة", header["course_code"], header["course_name_ar"]],
            ["الشعبة", header["group_name"], "المحاضرات المنعقدة", str(held)],
            [],
            ["الرقم الجامعي", "الاسم", "حاضر", "متأخر", "غائب", "بعذر", "نسبة الحضور %"],
        ]
        for item in items:
            rows.append(
                [
                    item["university_id"],
                    item["full_name_ar"],
                    str(item["present"]),
                    str(item["late"]),
                    str(item["absent"]),
                    str(item["excused"]),
                    f"{item['attendance_rate']}",
                ]
            )
        rows.append(
            [
                "المجموع",
                "",
                str(totals["present"]),
                str(totals["late"]),
                str(totals["absent"]),
                str(totals["excused"]),
                f"{overall_rate}",
            ]
        )
        return _csv_response(rows, f"attendance-{header['course_code']}.csv")

    return {
        "offering": header,
        "totals": {
            "sessions": len(sessions),
            "held": held,
            **totals,
            "attendance_rate": overall_rate,
        },
        "students": items,
    }


@router.get("/grades", response_model=None)
def grades_report(
    offering_id: uuid.UUID,
    format: str = Query(default="json", pattern="^(json|csv)$"),
    user: User = Depends(require_roles(*REPORT_ROLES)),
    db: Session = Depends(get_db),
) -> Response | dict:
    offering = _offering_or_403(db, user, offering_id)
    header = _offering_header(db, offering)

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
    students = db.execute(
        select(Student, User)
        .join(User, User.id == Student.user_id)
        .join(Enrollment, Enrollment.student_id == Student.user_id)
        .where(
            Enrollment.offering_id == offering.id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        .order_by(User.full_name_ar)
    ).all()

    scores: dict[uuid.UUID, dict[uuid.UUID, float]] = {}
    if assessments:
        for grade in db.scalars(
            select(Grade).where(
                Grade.assessment_id.in_([row.id for row in assessments])
            )
        ):
            scores.setdefault(grade.student_id, {})[grade.assessment_id] = float(grade.score)

    assessment_stats = []
    for assessment in assessments:
        values = [bucket[assessment.id] for bucket in scores.values() if assessment.id in bucket]
        average = round(sum(values) / len(values), 2) if values else None
        assessment_stats.append(
            {
                "assessment_id": str(assessment.id),
                "name": assessment.name,
                "kind": assessment.kind.value,
                "max_score": float(assessment.max_score),
                "weight": float(assessment.weight),
                "is_published": bool(assessment.is_published),
                "graded": len(values),
                "average": average,
                "min": min(values) if values else None,
                "max": max(values) if values else None,
                "contribution_average": (
                    round(average * float(assessment.weight) / 100.0, 2)
                    if average is not None
                    else None
                ),
            }
        )

    items = []
    for student, account in students:
        bucket = scores.get(student.user_id, {})
        total = 0.0
        for row in assessments:
            value = bucket.get(row.id)
            if value is not None:
                total += value * float(row.weight) / 100.0
        items.append(
            {
                "student_id": str(student.user_id),
                "university_id": account.university_id,
                "full_name_ar": account.full_name_ar,
                "graded_count": len(bucket),
                "weighted_total": round(total, 2),
                "scores": {str(key): value for key, value in bucket.items()},
            }
        )

    total_weight = sum(float(row.weight) for row in assessments)
    if format == "csv":
        rows = [
            ["المادة", header["course_code"], header["course_name_ar"]],
            ["الشعبة", header["group_name"], "وزن التقييمات %", f"{total_weight:g}"],
            [],
            ["الرقم الجامعي", "الاسم"]
            + [f"{row.name} ({float(row.max_score):g})" for row in assessments]
            + ["المجموع الموزون"],
        ]
        for item in items:
            rows.append(
                [item["university_id"], item["full_name_ar"]]
                + [
                    f"{item['scores'].get(str(row.id), '')}"
                    for row in assessments
                ]
                + [f"{item['weighted_total']}"]
            )
        return _csv_response(rows, f"grades-{header['course_code']}.csv")

    return {
        "offering": header,
        "total_weight": total_weight,
        "assessments": assessment_stats,
        "students": items,
    }
