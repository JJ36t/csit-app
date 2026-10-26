# -*- coding: utf-8 -*-
"""فحوصات الوصول المشتركة: تدريسي المادة، رئيس القسم، وتسجيل الطالب."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import CourseOffering, Enrollment, Group, Staff, Student, User
from app.models.enums import EnrollmentStatus, UserRole


def staff_department_id(db: Session, user: User) -> object | None:
    staff = db.get(Staff, user.id)
    return staff.department_id if staff is not None else None


def user_offering_ids(db: Session, user: User) -> list[uuid.UUID]:
    """معرّفات العروض التي يراها المستخدم حسب دوره (نطاق الجدول والمواد).

    الطالب: عروض تسجيله النشط فقط، التدريسي: عروضه، رئيس القسم: شعب قسمه،
    مدير الكلية: الكل. أي دور آخر أو غياب بيانات: قائمة فارغة.
    """
    if user.role == UserRole.STUDENT:
        return list(
            db.scalars(
                select(Enrollment.offering_id).where(
                    Enrollment.student_id == user.id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
            )
        )
    if user.role == UserRole.INSTRUCTOR:
        return list(
            db.scalars(
                select(CourseOffering.id).where(CourseOffering.instructor_id == user.id)
            )
        )
    if user.role == UserRole.DEPARTMENT_HEAD:
        department_id = staff_department_id(db, user)
        if department_id is None:
            return []
        return list(
            db.scalars(
                select(CourseOffering.id)
                .join(Group, Group.id == CourseOffering.group_id)
                .where(Group.department_id == department_id)
            )
        )
    if user.role == UserRole.COLLEGE_ADMIN:
        return list(db.scalars(select(CourseOffering.id)))
    return []


def is_department_head_of(db: Session, user: User, department_id) -> bool:
    if user.role != UserRole.DEPARTMENT_HEAD:
        return False
    return staff_department_id(db, user) == department_id


def offering_department_id(db: Session, offering: CourseOffering):
    group = db.get(Group, offering.group_id)
    return group.department_id if group is not None else None


def require_offering_staff(db: Session, user: User, offering: CourseOffering) -> None:
    """التدريسي المسؤول عن المادة، أو رئيس القسم التابعة له، أو مدير الكلية."""
    if user.role == UserRole.COLLEGE_ADMIN:
        return
    if offering.instructor_id == user.id:
        return
    if is_department_head_of(db, user, offering_department_id(db, offering)):
        return
    raise ApiError(403, "not_offering_staff", "هذا الإجراء متاح لتدريسي المادة أو رئيس قسمها")


def require_enrollment(db: Session, user: User, offering_id) -> Enrollment:
    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == user.id,
            Enrollment.offering_id == offering_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
    )
    if enrollment is None:
        raise ApiError(403, "not_enrolled", "أنت غير مسجَّل في هذه المادة")
    return enrollment


def require_student_row(db: Session, user: User) -> Student:
    student = db.get(Student, user.id)
    if student is None:
        raise ApiError(403, "not_a_student", "هذا الإجراء متاح للطلبة فقط")
    return student
