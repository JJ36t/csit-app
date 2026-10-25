# -*- coding: utf-8 -*-
"""بيانات عرض تجريبية (تطوير فقط): تدريسي وشعبة ومادة وحصة اليوم وجلسة.

    python scripts/demo_seed.py

يُنشئ/يعيد استخدام: قسم علوم الحاسوب، فصل 2026-2027، شعبة 1-A، مادة CS101،
تدريسي T-100/Test#12345، طالبين S-100/S-200 بكلمة المرور نفسها، حصة اليوم مع
جلسة قابلة للفتح من تطبيق التدريسي. قابل للتكرار بلا تكرار البيانات.
"""
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    AcademicYear,
    Course,
    CourseOffering,
    Department,
    Enrollment,
    Group,
    LectureSession,
    Room,
    Staff,
    Student,
    Term,
    TimetableSlot,
    User,
)
from app.models.enums import (  # noqa: E402
    EnrollmentStatus,
    LectureSessionStatus,
    SessionKind,
    StudentStatus,
    StudyType,
    UserRole,
    UserStatus,
)
from app.security import hash_password  # noqa: E402

PASSWORD = "Test#12345"
BAGHDAD = timezone(timedelta(hours=3))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    now = datetime.now(timezone.utc)
    local_now = now.astimezone(BAGHDAD)

    with SessionLocal() as db:
        dept = db.scalar(select(Department).where(Department.code == "CS"))
        if dept is None:
            raise SystemExit("شغّل scripts/seed.py أولاً (الأقسام غير موجودة)")

        year = db.scalar(select(AcademicYear).where(AcademicYear.is_current.is_(True)))
        if year is None:
            year = AcademicYear(label="2026-2027", is_current=True)
            db.add(year)
            db.flush()

        term = db.scalar(
            select(Term).where(Term.academic_year_id == year.id, Term.is_current.is_(True))
        )
        if term is None:
            term = Term(
                academic_year_id=year.id,
                name="الفصل الأول",
                is_current=True,
                start_date=date(2026, 10, 1),
                end_date=date(2027, 1, 31),
            )
            db.add(term)
            db.flush()

        group = db.scalar(
            select(Group).where(
                Group.department_id == dept.id, Group.stage == 1, Group.name == "A"
            )
        )
        if group is None:
            group = Group(
                department_id=dept.id,
                stage=1,
                name="A",
                study_type=StudyType.MORNING,
                term_id=term.id,
            )
            db.add(group)
            db.flush()

        course = db.scalar(select(Course).where(Course.code == "CS101"))
        if course is None:
            course = Course(
                code="CS101",
                name_ar="مقدمة في علوم الحاسوب",
                department_id=dept.id,
                stage=1,
                units=3,
                kind=SessionKind.THEORY,
            )
            db.add(course)
            db.flush()

        def ensure_user(university_id: str, name: str, role: UserRole) -> User:
            row = db.scalar(select(User).where(User.university_id == university_id))
            if row is None:
                row = User(
                    university_id=university_id,
                    full_name_ar=name,
                    role=role,
                    password_hash=hash_password(PASSWORD, rounds=4),
                    status=UserStatus.ACTIVE,
                    must_change_password=False,
                )
                db.add(row)
                db.flush()
            return row

        teacher = ensure_user("T-100", "د. أحمد التدريسي", UserRole.INSTRUCTOR)
        if db.get(Staff, teacher.id) is None:
            db.add(Staff(user_id=teacher.id, department_id=dept.id, academic_title="مدرس"))
            db.flush()

        students = []
        for university_id, name in (("S-100", "علي حسن محمد"), ("S-200", "زينب كريم جواد")):
            user = ensure_user(university_id, name, UserRole.STUDENT)
            if db.get(Student, user.id) is None:
                db.add(
                    Student(
                        user_id=user.id,
                        department_id=dept.id,
                        stage=1,
                        study_type=StudyType.MORNING,
                        group_id=group.id,
                        enrollment_year=2026,
                        status=StudentStatus.ACTIVE,
                    )
                )
                db.flush()
            students.append(user)

        offering = db.scalar(
            select(CourseOffering).where(
                CourseOffering.course_id == course.id,
                CourseOffering.term_id == term.id,
                CourseOffering.group_id == group.id,
                CourseOffering.session_kind == SessionKind.THEORY,
            )
        )
        if offering is None:
            offering = CourseOffering(
                course_id=course.id,
                term_id=term.id,
                group_id=group.id,
                instructor_id=teacher.id,
                session_kind=SessionKind.THEORY,
            )
            db.add(offering)
            db.flush()

        for user in students:
            exists = db.scalar(
                select(Enrollment).where(
                    Enrollment.student_id == user.id,
                    Enrollment.offering_id == offering.id,
                )
            )
            if exists is None:
                db.add(
                    Enrollment(
                        student_id=user.id,
                        offering_id=offering.id,
                        status=EnrollmentStatus.ACTIVE,
                    )
                )

        room = db.scalar(select(Room).where(Room.name == "قاعة 108"))
        if room is None:
            room = Room(
                name="قاعة 108",
                lat=31.9901,
                lng=44.9201,
                radius_m=120,
            )
            db.add(room)
            db.flush()

        slot = db.scalar(
            select(TimetableSlot).where(TimetableSlot.offering_id == offering.id)
        )
        if slot is None:
            slot = TimetableSlot(
                offering_id=offering.id,
                weekday=(local_now.weekday() + 1) % 7,
                start_time=time(10, 0),
                end_time=time(11, 30),
                room_id=room.id,
                kind=SessionKind.THEORY,
            )
            db.add(slot)
            db.flush()

        session = db.scalar(
            select(LectureSession).where(
                LectureSession.offering_id == offering.id,
                LectureSession.date == local_now.date(),
            )
        )
        if session is None:
            starts = now - timedelta(minutes=5)
            session = LectureSession(
                offering_id=offering.id,
                slot_id=slot.id,
                date=local_now.date(),
                starts_at=starts,
                ends_at=starts + timedelta(minutes=90),
                status=LectureSessionStatus.SCHEDULED,
                window_s=20,
            )
            db.add(session)

        db.commit()

    print("تم تجهيز بيانات العرض:")
    print(f"  تدريسي:  T-100 / {PASSWORD}")
    print(f"  طالب:    S-100 / {PASSWORD}   و  S-200 / {PASSWORD}")
    print(f"  المادة:  CS101 — {course.name_ar} · {room.name}")
    print(f"  جلسة اليوم: {session.id}")
    print("  لوحة التحكم تحتاج مديراً: python scripts/create_admin.py ADMIN-001 \"مدير الكلية\" \"Admin#2026\"")


if __name__ == "__main__":
    main()
