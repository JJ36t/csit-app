# -*- coding: utf-8 -*-
"""إدارة البنية الأكاديمية من لوحة التحكم: الشعب (groups) وعروض المواد (offerings).

كانت هذه النقاط ناقصة من جدول الـAPI في الخطة (ص13): لا يمكن إنشاء شعبة أو
عرض مادة إلا بسكربت. هنا تُنشأ من اللوحة بتحقق كامل:
- الشعبة فريدة داخل (قسم، مرحلة، اسم، نوع دراسة، فصل).
- العرض فريد داخل (مادة، فصل، شعبة، نوع جلسة)، والمادة يجب أن تطابق قسم
  الشعبة ومرحلتها.
- إنشاء العرض يسجّل طلبة الشعبة النشطين تلقائياً (source=auto) — وهو ما كانت
  الخطة تطلبه كي تظهر المواد للطالب فوراً.
"""
import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_roles
from app.errors import ApiError
from app.models import (
    AcademicYear,
    Course,
    CourseOffering,
    Department,
    Enrollment,
    Group,
    Staff,
    Student,
    Term,
    User,
)
from app.models.enums import (
    EnrollmentSource,
    EnrollmentStatus,
    SessionKind,
    StudentStatus,
    StudyType,
    UserRole,
)
from app.services.access import staff_department_id
from app.services.audit import log_action

router = APIRouter(prefix="/admin", tags=["admin-academic"])

MANAGER_ROLES = (UserRole.COLLEGE_ADMIN, UserRole.DEPARTMENT_HEAD)


class GroupIn(BaseModel):
    department_id: uuid.UUID
    stage: int = Field(ge=1, le=8)
    name: str = Field(min_length=1, max_length=50)
    study_type: StudyType = StudyType.MORNING
    term_id: uuid.UUID


class OfferingIn(BaseModel):
    course_id: uuid.UUID
    group_id: uuid.UUID
    instructor_id: uuid.UUID | None = None
    session_kind: SessionKind | None = None


def _require_department(db: Session, user: User, department_id: uuid.UUID) -> None:
    if user.role == UserRole.COLLEGE_ADMIN:
        return
    if staff_department_id(db, user) != department_id:
        raise ApiError(403, "outside_your_department", "هذه الشعبة خارج قسمك")


def _group_payload(group: Group, department: Department | None, term: Term | None) -> dict:
    return {
        "group_id": str(group.id),
        "department_id": str(group.department_id),
        "department_code": department.code if department else None,
        "department_name_ar": department.name_ar if department else None,
        "stage": group.stage,
        "name": group.name,
        "study_type": group.study_type.value,
        "term_id": str(group.term_id),
        "term_name": term.name if term else None,
    }


def _offering_payload(
    offering: CourseOffering,
    course: Course,
    group: Group,
    instructor: User | None,
    enrolled: int,
) -> dict:
    return {
        "offering_id": str(offering.id),
        "course_id": str(course.id),
        "course_code": course.code,
        "course_name_ar": course.name_ar,
        "group_id": str(group.id),
        "group_name": group.name,
        "stage": group.stage,
        "study_type": group.study_type.value,
        "kind": offering.session_kind.value,
        "instructor_id": str(instructor.id) if instructor else None,
        "instructor_name_ar": instructor.full_name_ar if instructor else None,
        "enrolled": enrolled,
    }


@router.get("/terms")
def list_terms(
    user: User = Depends(require_roles(*MANAGER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    """الفصول الدراسية — تحتاجها لوحة التحكم لإنشاء شعبة جديدة."""
    rows = db.execute(
        select(Term, AcademicYear)
        .join(AcademicYear, AcademicYear.id == Term.academic_year_id)
        .where(Term.deleted_at.is_(None))
        .order_by(Term.start_date.desc())
    ).all()
    return {
        "items": [
            {
                "term_id": str(term.id),
                "name": term.name,
                "year_label": year.label,
                "start_date": term.start_date.isoformat() if term.start_date else None,
                "end_date": term.end_date.isoformat() if term.end_date else None,
                "is_current": bool(term.is_current),
            }
            for term, year in rows
        ]
    }


@router.get("/groups")
def list_groups(
    department_id: uuid.UUID | None = Query(default=None),
    stage: int | None = Query(default=None, ge=1, le=8),
    user: User = Depends(require_roles(*MANAGER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    conditions = [Group.deleted_at.is_(None)]
    if department_id is not None:
        _require_department(db, user, department_id)
        conditions.append(Group.department_id == department_id)
    elif user.role == UserRole.DEPARTMENT_HEAD:
        own = staff_department_id(db, user)
        if own is None:
            return {"items": []}
        conditions.append(Group.department_id == own)
    if stage is not None:
        conditions.append(Group.stage == stage)

    rows = db.execute(
        select(Group, Department, Term)
        .join(Department, Department.id == Group.department_id)
        .join(Term, Term.id == Group.term_id)
        .where(*conditions)
        .order_by(Department.code, Group.stage, Group.name)
    ).all()
    return {"items": [_group_payload(group, dept, term) for group, dept, term in rows]}


@router.post("/groups")
def create_group(
    body: GroupIn,
    user: User = Depends(require_roles(*MANAGER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    _require_department(db, user, body.department_id)
    department = db.get(Department, body.department_id)
    if department is None or department.deleted_at is not None:
        raise ApiError(404, "department_not_found", "القسم غير موجود")
    term = db.get(Term, body.term_id)
    if term is None or term.deleted_at is not None:
        raise ApiError(404, "term_not_found", "الفصل الدراسي غير موجود")

    existing = db.scalar(
        select(Group).where(
            Group.department_id == body.department_id,
            Group.stage == body.stage,
            Group.name == body.name.strip(),
            Group.study_type == body.study_type,
            Group.term_id == body.term_id,
            Group.deleted_at.is_(None),
        )
    )
    if existing is not None:
        raise ApiError(409, "group_exists", "هذه الشعبة موجودة بالفعل")

    group = Group(
        department_id=body.department_id,
        stage=body.stage,
        name=body.name.strip(),
        study_type=body.study_type,
        term_id=body.term_id,
    )
    db.add(group)
    db.flush()
    log_action(
        db,
        actor=user,
        action="group_created",
        entity="group",
        entity_id=str(group.id),
        after={
            "department_id": str(group.department_id),
            "stage": group.stage,
            "name": group.name,
            "study_type": group.study_type.value,
        },
    )
    db.commit()
    return _group_payload(group, department, term)


@router.get("/courses")
def list_courses(
    department_id: uuid.UUID | None = Query(default=None),
    stage: int | None = Query(default=None, ge=1, le=8),
    user: User = Depends(require_roles(*MANAGER_ROLES, UserRole.INSTRUCTOR)),
    db: Session = Depends(get_db),
) -> dict:
    conditions = [Course.deleted_at.is_(None)]
    if department_id is not None:
        conditions.append(Course.department_id == department_id)
    if stage is not None:
        conditions.append(Course.stage == stage)
    rows = list(
        db.scalars(select(Course).where(*conditions).order_by(Course.code))
    )
    return {
        "items": [
            {
                "course_id": str(row.id),
                "code": row.code,
                "name_ar": row.name_ar,
                "department_id": str(row.department_id),
                "stage": row.stage,
                "units": row.units,
                "kind": row.kind.value,
            }
            for row in rows
        ]
    }


@router.get("/offerings")
def list_offerings(
    group_id: uuid.UUID | None = Query(default=None),
    department_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(require_roles(*MANAGER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    conditions = [CourseOffering.deleted_at.is_(None), Group.deleted_at.is_(None)]
    if group_id is not None:
        conditions.append(CourseOffering.group_id == group_id)
    if department_id is not None:
        _require_department(db, user, department_id)
        conditions.append(Group.department_id == department_id)
    elif user.role == UserRole.DEPARTMENT_HEAD:
        own = staff_department_id(db, user)
        if own is None:
            return {"items": []}
        conditions.append(Group.department_id == own)

    rows = db.execute(
        select(CourseOffering, Course, Group, User)
        .join(Course, Course.id == CourseOffering.course_id)
        .join(Group, Group.id == CourseOffering.group_id)
        .outerjoin(User, User.id == CourseOffering.instructor_id)
        .where(*conditions)
        .order_by(Course.code, Group.name)
    ).all()

    counts = dict(
        db.execute(
            select(Enrollment.offering_id, func.count())
            .where(Enrollment.status == EnrollmentStatus.ACTIVE)
            .group_by(Enrollment.offering_id)
        ).all()
    )
    return {
        "items": [
            _offering_payload(offering, course, group, instructor, int(counts.get(offering.id, 0)))
            for offering, course, group, instructor in rows
        ]
    }


@router.post("/offerings")
def create_offering(
    body: OfferingIn,
    user: User = Depends(require_roles(*MANAGER_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    group = db.get(Group, body.group_id)
    if group is None or group.deleted_at is not None:
        raise ApiError(404, "group_not_found", "الشعبة غير موجودة")
    _require_department(db, user, group.department_id)

    course = db.get(Course, body.course_id)
    if course is None or course.deleted_at is not None:
        raise ApiError(404, "course_not_found", "المادة غير موجودة")
    if course.department_id != group.department_id or course.stage != group.stage:
        raise ApiError(
            400,
            "course_group_mismatch",
            "المادة لا تطابق قسم الشعبة أو مرحلتها",
        )

    kind = body.session_kind or course.kind
    instructor: User | None = None
    if body.instructor_id is not None:
        instructor = db.get(User, body.instructor_id)
        if instructor is None or instructor.deleted_at is not None:
            raise ApiError(404, "instructor_not_found", "التدريسي غير موجود")
        if instructor.role not in (UserRole.INSTRUCTOR, UserRole.DEPARTMENT_HEAD):
            raise ApiError(400, "invalid_instructor", "الحساب المحدد ليس تدريسياً")
        if db.get(Staff, instructor.id) is None:
            raise ApiError(400, "invalid_instructor", "لا يوجد ملف تدريسي لهذا الحساب")

    existing = db.scalar(
        select(CourseOffering).where(
            CourseOffering.course_id == course.id,
            CourseOffering.term_id == group.term_id,
            CourseOffering.group_id == group.id,
            CourseOffering.session_kind == kind,
            CourseOffering.deleted_at.is_(None),
        )
    )
    if existing is not None:
        raise ApiError(409, "offering_exists", "هذا العرض موجود بالفعل لنفس الشعبة")

    offering = CourseOffering(
        course_id=course.id,
        term_id=group.term_id,
        group_id=group.id,
        instructor_id=instructor.id if instructor else None,
        session_kind=kind,
    )
    db.add(offering)
    db.flush()

    # تسجيل تلقائي لطلبة الشعبة النشطين
    students = list(
        db.scalars(
            select(Student.user_id).where(
                Student.group_id == group.id,
                Student.status == StudentStatus.ACTIVE,
                Student.deleted_at.is_(None),
            )
        )
    )
    for student_id in students:
        db.add(
            Enrollment(
                student_id=student_id,
                offering_id=offering.id,
                source=EnrollmentSource.AUTO,
                status=EnrollmentStatus.ACTIVE,
            )
        )

    log_action(
        db,
        actor=user,
        action="offering_created",
        entity="course_offering",
        entity_id=str(offering.id),
        after={
            "course_id": str(course.id),
            "group_id": str(group.id),
            "kind": kind.value,
            "instructor_id": str(instructor.id) if instructor else None,
            "auto_enrolled": len(students),
        },
    )
    db.commit()
    return _offering_payload(offering, course, group, instructor, len(students))
