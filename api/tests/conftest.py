# -*- coding: utf-8 -*-
"""تهيئة بيئة الاختبارات: قاعدة معزولة + بيانات الأقسام + حساب مدير."""
import os
import shutil
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))

os.environ.setdefault("DATABASE_URL", f"sqlite:///{API_DIR / 'test_api.db'}")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("UPLOAD_DIR", str(API_DIR / "test_uploads"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.db import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, User  # noqa: E402
from app.models.enums import UserRole, UserStatus  # noqa: E402
from app.security import hash_password  # noqa: E402
from scripts.seed import seed_departments  # noqa: E402

# على PostgreSQL: drop_all لا يُسقط أنواع Enum — تُسقط يدوياً بين الاختبارات.
_PG_ENUM_NAMES = (
    "userrole, userstatus, devicestatus, studytype, studentstatus, "
    "enrollmentsource, enrollmentstatus, sessionkind, timetablechangetype, "
    "lecturesessionstatus, attendancestatus, attendancemethod, excusestatus, "
    "materialkind, assessmentkind, announcementscope, announcementpriority, requeststatus"
)


def _reset_schema() -> None:
    Base.metadata.drop_all(bind=engine)
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(
                text(f"DROP TYPE IF EXISTS {_PG_ENUM_NAMES} CASCADE")
            )
    Base.metadata.create_all(bind=engine)

ADMIN_ID = "ADMIN-001"
ADMIN_PASSWORD = "Admin@1234"
ADMIN_DEVICE = {"fingerprint": "admin-device-0001", "model": "Workstation"}


@pytest.fixture()
def client():
    """قاعدة اختبار نظيفة مع الأقسام الأربعة، لكل اختبار."""
    shutil.rmtree(API_DIR / "test_uploads", ignore_errors=True)
    _reset_schema()
    with SessionLocal() as db:
        seed_departments(db)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def admin_client(client):
    """عميل مسجّل الدخول كمدير كلية (Authorization مضبوط)."""
    with SessionLocal() as db:
        db.add(
            User(
                university_id=ADMIN_ID,
                full_name_ar="مدير الكلية",
                role=UserRole.COLLEGE_ADMIN,
                password_hash=hash_password(ADMIN_PASSWORD),
                status=UserStatus.ACTIVE,
                must_change_password=False,
            )
        )
        db.commit()

    res = client.post(
        "/api/v1/auth/login",
        json={
            "university_id": ADMIN_ID,
            "password": ADMIN_PASSWORD,
            "device": ADMIN_DEVICE,
        },
    )
    assert res.status_code == 200, res.text
    client.headers.update({"Authorization": f"Bearer {res.json()['access_token']}"})
    return client
