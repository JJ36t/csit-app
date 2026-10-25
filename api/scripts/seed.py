# -*- coding: utf-8 -*-
"""تهيئة البيانات الأولية: الأقسام الأربعة + السنة الدراسية الحالية.

تشغيل من مجلد api:
    python scripts/seed.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import AcademicYear, Department  # noqa: E402

# الأقسام الأربعة المعتمدة (قرار رقم 5) — الرموز مبدئية وتُثبَّت مع البيانات الرسمية
DEPARTMENTS: list[tuple[str, str, str]] = [
    ("CS", "علوم الحاسوب", "Computer Science"),
    ("IS", "نظم المعلومات", "Information Systems"),
    ("MS", "الأنظمة الطبية", "Medical Systems"),
    ("CY", "الأمن السيبراني", "Cybersecurity"),
]

CURRENT_YEAR_LABEL = "2026–2027"


def seed_departments(db: Session) -> int:
    """إضافة الأقسام الناقصة (idempotent) وإرجاء عدد المضاف."""
    added = 0
    for code, name_ar, name_en in DEPARTMENTS:
        exists = db.scalar(select(Department).where(Department.code == code))
        if exists is None:
            db.add(Department(code=code, name_ar=name_ar, name_en=name_en))
            added += 1
    db.commit()
    return added


def seed_current_year(db: Session) -> None:
    """تعيين السنة الدراسية الحالية 2026–2027 (idempotent) وتصفية غيرها."""
    year = db.scalar(select(AcademicYear).where(AcademicYear.label == CURRENT_YEAR_LABEL))
    if year is None:
        year = AcademicYear(label=CURRENT_YEAR_LABEL, is_current=True)
        db.add(year)
        db.flush()
    for other in db.scalars(select(AcademicYear).where(AcademicYear.is_current.is_(True))):
        if other.id != year.id:
            other.is_current = False
    year.is_current = True
    db.commit()


def main() -> None:
    with SessionLocal() as db:
        added = seed_departments(db)
        seed_current_year(db)
        total = len(db.scalars(select(Department)).all())
        print(f"departments added: {added} | total in db: {total} (CS, IS, MS, CY)")
        print(f"current academic year: {CURRENT_YEAR_LABEL}")


if __name__ == "__main__":
    main()
