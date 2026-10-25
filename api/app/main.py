# -*- coding: utf-8 -*-
"""الخدمة الرئيسية — تطبيق كلية علوم الحاسوب وتكنولوجيا المعلومات، جامعة القادسية."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.errors import install_error_handlers
from app.routers import (
    admin_students,
    admin_timetable,
    admin_users,
    announcements,
    attendance,
    auth,
    departments,
    grades,
    health,
    materials,
    notifications,
    timetable,
)

app = FastAPI(
    title=settings.app_name,
    version="0.3.0",
    description=(
        "خلفية تطبيق الكلية — الجدول والحضور والمواد والإعلانات والدرجات، "
        "مع المصادقة (JWT + تجديد + ربط جهاز) واستيراد الطلاب من Excel."
    ),
)

install_error_handlers(app)

# تطوير محلي: Flutter web ولوحة التحكم على localhost
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(departments.router, prefix=settings.api_v1_prefix)
app.include_router(admin_students.router, prefix=settings.api_v1_prefix)
app.include_router(admin_users.router, prefix=settings.api_v1_prefix)
app.include_router(admin_timetable.router, prefix=settings.api_v1_prefix)
app.include_router(announcements.router, prefix=settings.api_v1_prefix)
app.include_router(attendance.router, prefix=settings.api_v1_prefix)
app.include_router(grades.router, prefix=settings.api_v1_prefix)
app.include_router(materials.router, prefix=settings.api_v1_prefix)
app.include_router(notifications.router, prefix=settings.api_v1_prefix)
app.include_router(timetable.router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {"app": settings.app_name, "docs": "/docs", "health": "/health"}
