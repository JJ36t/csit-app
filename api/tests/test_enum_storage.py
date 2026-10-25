# -*- coding: utf-8 -*-
"""القوائم المعرِّفة تُخزَّن بقيمها النصية الصغيرة كما في الخطة (student, active…)."""
from sqlalchemy import select, text

from app.db import SessionLocal
from app.models import User
from app.models.enums import UserRole, UserStatus


def test_enum_values_stored_lowercase(client):
    with SessionLocal() as db:
        db.add(
            User(
                university_id="T-001",
                full_name_ar="مستخدم اختبار",
                role=UserRole.STUDENT,
                password_hash="x",
                status=UserStatus.ACTIVE,
                must_change_password=True,
            )
        )
        db.commit()

        raw = db.execute(
            text("select role, status from users where university_id = 'T-001'")
        ).one()
        assert raw[0] == "student"
        assert raw[1] == "active"

        # والقراءة عبر ORM تعيد عضو القائمة الصحيح
        db.expire_all()
        got = db.scalar(select(User).where(User.university_id == "T-001"))
        assert got is not None
        assert got.role is UserRole.STUDENT
        assert got.status is UserStatus.ACTIVE
