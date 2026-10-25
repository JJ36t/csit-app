# -*- coding: utf-8 -*-
"""نقاط الأقسام — أول نقطة أعمال حقيقية في الخدمة."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Department
from app.schemas import DepartmentOut

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db)) -> list[Department]:
    stmt = (
        select(Department)
        .where(Department.deleted_at.is_(None))
        .order_by(Department.name_ar)
    )
    return list(db.scalars(stmt))
