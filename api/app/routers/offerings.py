# -*- coding: utf-8 -*-
"""مواد المستخدم: قائمة العروض (course offerings) التي يراها حسب دوره."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Course, CourseOffering, Group, User
from app.services.access import user_offering_ids

router = APIRouter(tags=["offerings"])


@router.get("/offerings")
def list_offerings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """عروض المستخدم مرة واحدة لكل عرض، مرتّبة بالمقرر ثم الشعبة.

    المرحلة والشعبة ونوع الدراسة تُقرأ من شعبة العرض (Group)، والتدريسي
    قد يكون غير معيَّن فيكون الاسم null.
    """
    offering_ids = user_offering_ids(db, user)
    if not offering_ids:
        return {"items": []}

    rows = db.execute(
        select(CourseOffering, Course, Group, User)
        .join(Course, Course.id == CourseOffering.course_id)
        .join(Group, Group.id == CourseOffering.group_id)
        .outerjoin(User, User.id == CourseOffering.instructor_id)
        .where(CourseOffering.id.in_(offering_ids))
        .order_by(Course.code, Group.name)
    ).all()

    return {
        "items": [
            {
                "offering_id": str(offering.id),
                "course_code": course.code,
                "course_name_ar": course.name_ar,
                "kind": offering.session_kind.value,
                "stage": group.stage,
                "group_name": group.name,
                "study_type": group.study_type.value,
                "instructor_name_ar": (
                    instructor.full_name_ar if instructor is not None else None
                ),
            }
            for offering, course, group, instructor in rows
        ]
    }
