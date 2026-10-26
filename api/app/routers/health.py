# -*- coding: utf-8 -*-
"""نقطة فحص الجهوزية — تراقبها Uptime Kuma بحسب الخطة.

الفحص «عميق» عمداً: يتحقق من الاتصال بقاعدة البيانات (SELECT 1) ويقرأ رقم
الترحيل الحالي من ‎alembic_version‎ إن وُجد. تعطّل القاعدة يعني 503 مع
‎status: degraded‎ كي يلتقطه Uptime Kuma وHEALTHCHECK في Docker.
"""
from typing import Any

from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import SessionLocal

router = APIRouter(tags=["health"])


def _probe_database() -> tuple[bool, str | None]:
    """يعيد (هل القاعدة متاحة، رقم الترحيل الحالي أو None)."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            try:
                revision = db.scalar(text("SELECT version_num FROM alembic_version"))
            except SQLAlchemyError:
                # قاعدة لم تُرحَّل بعد: الجدول غير موجود، وهذا ليس عطلاً.
                db.rollback()
                revision = None
        return True, revision
    except SQLAlchemyError:
        return False, None


@router.get("/health")
def health(response: Response) -> dict[str, Any]:
    database_ok, revision = _probe_database()
    if not database_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "degraded", "database": "unavailable", "revision": None}
    return {"status": "ok", "database": "ok", "revision": revision}
