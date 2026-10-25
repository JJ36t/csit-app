# -*- coding: utf-8 -*-
"""استيراد طلاب من ملف Excel عبر سطر الأوامر (فحص افتراضي، والتنفيذ بـ --commit).

    python scripts/import_students.py students.xlsx
    python scripts/import_students.py students.xlsx --commit
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.services.import_students import import_students  # noqa: E402


def main() -> None:
    args = sys.argv[1:]
    if not args:
        raise SystemExit("الاستخدام: python scripts/import_students.py <students.xlsx> [--commit]")

    path = Path(args[0])
    if not path.exists():
        raise SystemExit(f"الملف غير موجود: {path}")
    commit = "--commit" in args

    with SessionLocal() as db:
        actor = db.scalar(select(User).where(User.role == UserRole.COLLEGE_ADMIN))
        if actor is None:
            raise SystemExit(
                "لا يوجد مدير كلية في القاعدة. أنشئ واحداً أولاً:\n"
                '  python scripts/create_admin.py ADMIN-001 "مدير الكلية"'
            )

        result = import_students(db, path.read_bytes(), dry_run=not commit, actor=actor)

        mode = "فحص فقط" if not commit else "تنفيذ فعلي"
        print(f"[{mode}] صفوف: {result.rows_total} | صالحة: {result.rows_valid} | خاطئة: {result.rows_invalid}")
        if result.groups_created:
            print(f"شُعب أُنشئت: {len(result.groups_created)}")
            for name in result.groups_created:
                print(f"  + {name}")
        for issue in result.errors[:50]:
            print(f"  صف {issue.row} [{issue.column}] {issue.code}: {issue.message_ar}")
        if result.truncated:
            print("  ... (بقية الأخطاء لم تُعرض)")
        if commit:
            print(f"حسابات أُنشئت: {len(result.created)}")
            print("كلمة المرور الأولية لكل طالب = رقمه الجامعي (مع إجبار التغيير عند أول دخول)")


if __name__ == "__main__":
    main()
