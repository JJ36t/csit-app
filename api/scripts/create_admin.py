# -*- coding: utf-8 -*-
"""إنشاء أو إعادة تعيين حساب مدير الكلية.

    python scripts/create_admin.py ADMIN-001 "اسم المدير" [كلمة المرور]

إن حُذفت كلمة المرور تُولَّد عشوائياً وتُطبع مرة واحدة.
"""
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.models.enums import UserRole, UserStatus  # noqa: E402
from app.security import hash_password  # noqa: E402


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2:
        raise SystemExit('الاستخدام: python scripts/create_admin.py <الرقم> "<الاسم>" [كلمة المرور]')

    university_id, full_name = args[0], args[1]
    password = args[2] if len(args) > 2 else secrets.token_urlsafe(9)
    generated = len(args) <= 2

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.university_id == university_id))
        if user is None:
            user = User(
                university_id=university_id,
                full_name_ar=full_name,
                role=UserRole.COLLEGE_ADMIN,
                password_hash=hash_password(password),
                status=UserStatus.ACTIVE,
                must_change_password=True,
            )
            db.add(user)
            action = "created"
        else:
            user.role = UserRole.COLLEGE_ADMIN
            user.full_name_ar = full_name
            user.password_hash = hash_password(password)
            user.status = UserStatus.ACTIVE
            user.must_change_password = True
            action = "updated"
        db.commit()

    print(f"admin {action}: {university_id}")
    print(f"initial password: {password}" + ("  (generated — save it now)" if generated else ""))


if __name__ == "__main__":
    main()
