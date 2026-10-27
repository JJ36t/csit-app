# -*- coding: utf-8 -*-
"""أرشفة نهاية الفصل: ترقية المراحل، تخريج المرحلة الرابعة، وإغلاق التسجيلات.

    python scripts/archive_term.py --dry-run     # معاينة بلا كتابة
    python scripts/archive_term.py               # تنفيذ

ما يفعله (داخل معاملة واحدة):
1. كل جلسة حضور مفتوحة تُغلق (لا تبقى جلسة تقبل مسحاً بعد نهاية الفصل).
2. تسجيلات مواد الفصل الحالي تنتقل إلى «مكتمل» (تحفظ الدرجات والحضور).
3. طالب المرحلة 1–3: يرتفع للمرحلة التالية ويُفرَّغ من شعبة الفصل المنتهي
   (الشعبة الجديدة تُسند عند إنشاء شعب الفصل القادم).
4. طالب المرحلة 4 (أو 5–8 لبرامج أطول): «متخرج» ولا يُسجَّل تلقائياً بعدها.
5. سجل تدقيق واحد بالنتيجة — الأرشفة عملية إدارية تُراجَع لاحقاً.

التراجع: لا يوجد تراجع تلقائي؛ لذلك `--dry-run` مطبوع بالتفصيل، والنسخة
الاحتياطية اليومية هي شبكة الأمان.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    AcademicYear,
    CourseOffering,
    Enrollment,
    LectureSession,
    Student,
    Term,
)
from app.models.enums import (  # noqa: E402
    EnrollmentStatus,
    LectureSessionStatus,
    StudentStatus,
)
from app.services.audit import log_action  # noqa: E402

GRADUATION_STAGE = 4


def _current_term(db) -> Term:
    term = db.scalar(select(Term).where(Term.is_current.is_(True)))
    if term is not None:
        return term
    year = db.scalar(select(AcademicYear).where(AcademicYear.is_current.is_(True)))
    if year is None:
        raise SystemExit("لا توجد سنة دراسية حالية؛ شغّل scripts/seed.py أولاً")
    term = db.scalar(
        select(Term).where(Term.academic_year_id == year.id).order_by(Term.start_date.desc())
    )
    if term is None:
        raise SystemExit("لا يوجد فصل دراسي؛ أنشئ فصلاً أولاً")
    return term


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="أرشفة نهاية الفصل الدراسي")
    parser.add_argument("--dry-run", action="store_true", help="عرض الأثر بلا كتابة")
    parser.add_argument("--term-id", help="معرّف الفصل (افتراضياً الفصل الحالي)")
    parser.add_argument(
        "--graduation-stage",
        type=int,
        default=GRADUATION_STAGE,
        help=f"مرحلة التخرّج (افتراضياً {GRADUATION_STAGE})",
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        if args.term_id:
            import uuid

            term = db.get(Term, uuid.UUID(args.term_id))
            if term is None:
                raise SystemExit("الفصل غير موجود")
        else:
            term = _current_term(db)

        offering_ids = list(
            db.scalars(select(CourseOffering.id).where(CourseOffering.term_id == term.id))
        )

        open_sessions = list(
            db.scalars(
                select(LectureSession).where(
                    LectureSession.status == LectureSessionStatus.OPEN
                )
            )
        )

        active_students = list(
            db.scalars(
                select(Student).where(
                    Student.status == StudentStatus.ACTIVE,
                    Student.deleted_at.is_(None),
                )
            )
        )
        promote = [row for row in active_students if row.stage < args.graduation_stage]
        graduate = [row for row in active_students if row.stage >= args.graduation_stage]

        enrollments = (
            list(
                db.scalars(
                    select(Enrollment).where(
                        Enrollment.offering_id.in_(offering_ids),
                        Enrollment.status == EnrollmentStatus.ACTIVE,
                    )
                )
            )
            if offering_ids
            else []
        )

        print(f"الفصل: {term.name} ({term.start_date} → {term.end_date})")
        print(f"عروض المواد: {len(offering_ids)}")
        print(f"جلسات مفتوحة ستُغلق: {len(open_sessions)}")
        print(f"تسجيلات نشطة ستُكمل: {len(enrollments)}")
        print(f"طلبة سيُرقّون: {len(promote)}")
        print(f"طلبة سيتخرّجون: {len(graduate)}")
        for row in promote[:10]:
            print(f"  ترقية: {row.user_id} {row.stage} → {row.stage + 1}")
        if len(promote) > 10:
            print(f"  … و{len(promote) - 10} آخرون")

        if args.dry_run:
            print("\nمعاينة فقط (--dry-run): لم تُكتب أي بيانات.")
            return

        for session in open_sessions:
            session.status = LectureSessionStatus.CLOSED

        for enrollment in enrollments:
            enrollment.status = EnrollmentStatus.COMPLETED

        for student in promote:
            student.stage += 1
            student.group_id = None

        for student in graduate:
            student.status = StudentStatus.GRADUATED
            student.group_id = None

        # الأشكال القديمة للشعبة تبقى للتاريخ، ولا تُحذف
        log_action(
            db,
            actor=None,
            action="term_archived",
            entity="term",
            entity_id=str(term.id),
            after={
                "sessions_closed": len(open_sessions),
                "enrollments_completed": len(enrollments),
                "students_promoted": len(promote),
                "students_graduated": len(graduate),
                "graduation_stage": args.graduation_stage,
            },
        )
        db.commit()

    print("\nتمت الأرشفة. أنشئ شعب الفصل الجديد ثم عروض المواد من لوحة التحكم.")
    print("تذكير: عروض الفصل الجديد تُسجّل طلبة الشعبة تلقائياً عند إنشائها.")


if __name__ == "__main__":
    main()
