# -*- coding: utf-8 -*-
"""الخدمة الرئيسية — تطبيق كلية علوم الحاسوب وتكنولوجيا المعلومات، جامعة القادسية."""
import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.errors import install_error_handlers
from app.services.push_worker import run_forever as run_push_worker
from app.routers import (
    admin_academic,
    admin_audit,
    admin_overview,
    admin_reports,
    admin_students,
    admin_timetable,
    admin_users,
    announcements,
    attendance,
    auth,
    departments,
    excuses,
    grades,
    health,
    identity,
    materials,
    notifications,
    offerings,
    public,
    requests,
    timetable,
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """مهمة خلفية واحدة تُفرّغ طابور إشعارات الدفع أثناء حياة الخدمة.

    لا تبدأ إن كان FCM معطّلاً (الوضع الافتراضي محلياً وفي الاختبارات).
    """
    task: asyncio.Task | None = None
    if settings.fcm_enabled and settings.push_dispatch_enabled:
        task = asyncio.create_task(run_push_worker())
    yield
    if task is not None:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title=settings.app_name,
    version="0.4.0",
    lifespan=lifespan,
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
app.include_router(public.router, prefix=settings.api_v1_prefix)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(departments.router, prefix=settings.api_v1_prefix)
app.include_router(excuses.router, prefix=settings.api_v1_prefix)
app.include_router(identity.router, prefix=settings.api_v1_prefix)
app.include_router(requests.router, prefix=settings.api_v1_prefix)
app.include_router(admin_students.router, prefix=settings.api_v1_prefix)
app.include_router(admin_users.router, prefix=settings.api_v1_prefix)
app.include_router(admin_audit.router, prefix=settings.api_v1_prefix)
app.include_router(admin_academic.router, prefix=settings.api_v1_prefix)
app.include_router(admin_reports.router, prefix=settings.api_v1_prefix)
app.include_router(admin_overview.router, prefix=settings.api_v1_prefix)
app.include_router(admin_timetable.router, prefix=settings.api_v1_prefix)
app.include_router(announcements.router, prefix=settings.api_v1_prefix)
app.include_router(attendance.router, prefix=settings.api_v1_prefix)
app.include_router(grades.router, prefix=settings.api_v1_prefix)
app.include_router(materials.router, prefix=settings.api_v1_prefix)
app.include_router(notifications.router, prefix=settings.api_v1_prefix)
app.include_router(offerings.router, prefix=settings.api_v1_prefix)
app.include_router(timetable.router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {"app": settings.app_name, "docs": "/docs", "health": "/health"}
