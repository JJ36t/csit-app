# -*- coding: utf-8 -*-
"""عالم اختباري موحّد: قسم/فصل/شعبة/مادة/تدريسي/طالبان/قاعة/حصة/جلسة/مدير."""
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.models import (
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
from app.models.enums import (
    EnrollmentStatus,
    LectureSessionStatus,
    SessionKind,
    StudentStatus,
    StudyType,
    UserRole,
    UserStatus,
)
from app.security import hash_password

PASSWORD = "Test#2026"
BAGHDAD = timezone(timedelta(hours=3))


def build_world(*, start_offset_minutes: int = -5, duration_minutes: int = 45) -> dict:
    now = datetime.now(timezone.utc)
    local_now = now.astimezone(BAGHDAD)

    with SessionLocal() as db:
        dept = db.scalar(select(Department).where(Department.code == "CS"))
        year = AcademicYear(label="2026-2027", is_current=True)
        db.add(year)
        db.flush()
        term = Term(
            academic_year_id=year.id,
            name="الفصل الأول",
            is_current=True,
            start_date=date(2026, 10, 1),
            end_date=date(2027, 1, 31),
        )
        db.add(term)
        db.flush()
        group = Group(
            department_id=dept.id,
            stage=1,
            name="A",
            study_type=StudyType.MORNING,
            term_id=term.id,
        )
        db.add(group)
        db.flush()
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

        def user(university_id: str, name: str, role: UserRole) -> User:
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

        instructor = user("T-100", "د. أحمد التدريسي", UserRole.INSTRUCTOR)
        db.add(Staff(user_id=instructor.id, department_id=dept.id, academic_title="مدرس"))

        student = user("S-100", "علي حسن محمد", UserRole.STUDENT)
        db.add(
            Student(
                user_id=student.id,
                department_id=dept.id,
                stage=1,
                study_type=StudyType.MORNING,
                group_id=group.id,
                enrollment_year=2026,
                status=StudentStatus.ACTIVE,
            )
        )

        other = user("S-200", "زينب كريم جواد", UserRole.STUDENT)
        db.add(
            Student(
                user_id=other.id,
                department_id=dept.id,
                stage=1,
                study_type=StudyType.MORNING,
                group_id=group.id,
                enrollment_year=2026,
                status=StudentStatus.ACTIVE,
            )
        )

        outsider = user("S-300", "طالب غير مسجَّل", UserRole.STUDENT)
        db.add(
            Student(
                user_id=outsider.id,
                department_id=dept.id,
                stage=1,
                study_type=StudyType.MORNING,
                group_id=group.id,
                enrollment_year=2026,
                status=StudentStatus.ACTIVE,
            )
        )

        admin = user("ADMIN-9", "مدير الكلية", UserRole.COLLEGE_ADMIN)

        offering = CourseOffering(
            course_id=course.id,
            term_id=term.id,
            group_id=group.id,
            instructor_id=instructor.id,
            session_kind=SessionKind.THEORY,
        )
        db.add(offering)
        db.flush()
        db.add(
            Enrollment(
                student_id=student.id,
                offering_id=offering.id,
                status=EnrollmentStatus.ACTIVE,
            )
        )
        db.add(
            Enrollment(
                student_id=other.id,
                offering_id=offering.id,
                status=EnrollmentStatus.ACTIVE,
            )
        )

        room = Room(name="قاعة 101", lat=31.99, lng=44.92, radius_m=100)
        db.add(room)
        db.flush()

        starts = now + timedelta(minutes=start_offset_minutes)
        ends = starts + timedelta(minutes=duration_minutes)
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
        session = LectureSession(
            offering_id=offering.id,
            slot_id=slot.id,
            date=local_now.date(),
            starts_at=starts,
            ends_at=ends,
            status=LectureSessionStatus.SCHEDULED,
            window_s=20,
        )
        db.add(session)
        db.commit()

        return {
            "student": str(student.id),
            "other": str(other.id),
            "outsider": str(outsider.id),
            "instructor": str(instructor.id),
            "admin": str(admin.id),
            "offering": str(offering.id),
            "session": str(session.id),
            "slot": str(slot.id),
            "room": str(room.id),
            "group": str(group.id),
            "course": str(course.id),
            "term": str(term.id),
            "department": str(dept.id),
        }


def login(client, university_id: str, fingerprint: str) -> dict:
    res = client.post(
        "/api/v1/auth/login",
        json={
            "university_id": university_id,
            "password": PASSWORD,
            "device": {"fingerprint": fingerprint, "model": "Test"},
        },
    )
    assert res.status_code == 200, res.text
    return res.json()


def auth_headers(login_body: dict) -> dict:
    return {"Authorization": f"Bearer {login_body['access_token']}"}
