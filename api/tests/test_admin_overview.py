# -*- coding: utf-8 -*-
"""اختبارات لوحة الملخص: أرقام مدير الكلية، حصر رئيس القسم، ورفض بقية الأدوار."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.models import (
    Announcement,
    Assessment,
    AttendanceRecord,
    Course,
    CourseOffering,
    Department,
    Group,
    LectureSession,
    Staff,
    Student,
    Term,
    User,
)
from app.models.enums import (
    AnnouncementScope,
    AssessmentKind,
    AttendanceMethod,
    AttendanceStatus,
    LectureSessionStatus,
    SessionKind,
    StudentStatus,
    StudyType,
    UserRole,
    UserStatus,
)
from app.security import hash_password
from world import auth_headers, build_world, login

BAGHDAD = timezone(timedelta(hours=3))
HEAD_PASSWORD = "head" + "-" + "pass" + "-9137"


def _add_assessments(offering_id: str, published: int, drafts: int) -> None:
    with SessionLocal() as db:
        for index in range(published + drafts):
            db.add(
                Assessment(
                    offering_id=uuid.UUID(offering_id),
                    name=f"تقييم {index + 1}",
                    kind=AssessmentKind.QUIZ,
                    is_published=index < published,
                )
            )
        db.commit()


def _add_announcements(created_by: str, specs: list[tuple]) -> None:
    """specs: (scope, scope_id, publish_at, expires_at)."""
    with SessionLocal() as db:
        for index, (scope, scope_id, publish_at, expires_at) in enumerate(specs):
            db.add(
                Announcement(
                    scope=scope,
                    scope_id=scope_id,
                    title=f"إعلان {index + 1}",
                    body="نص الإعلان",
                    publish_at=publish_at,
                    expires_at=expires_at,
                    created_by=uuid.UUID(created_by),
                )
            )
        db.commit()


def _add_attendance(world: dict) -> None:
    with SessionLocal() as db:
        db.add(
            AttendanceRecord(
                session_id=uuid.UUID(world["session"]),
                student_id=uuid.UUID(world["student"]),
                status=AttendanceStatus.PRESENT,
                method=AttendanceMethod.QR,
            )
        )
        db.add(
            AttendanceRecord(
                session_id=uuid.UUID(world["session"]),
                student_id=uuid.UUID(world["other"]),
                status=AttendanceStatus.LATE,
                method=AttendanceMethod.MANUAL,
            )
        )
        db.commit()


def _seed_other_department(world: dict) -> None:
    """قسم نظم المعلومات: طالب وشعبة وعرض وتقييم منشور وجلسة اليوم — لاختبار الحصر."""
    with SessionLocal() as db:
        is_dept = db.scalar(select(Department).where(Department.code == "IS"))
        term = db.get(Term, uuid.UUID(world["term"]))
        group = Group(
            department_id=is_dept.id,
            stage=1,
            name="A",
            study_type=StudyType.MORNING,
            term_id=term.id,
        )
        db.add(group)
        db.flush()
        course = Course(
            code="IS101",
            name_ar="مقدمة في نظم المعلومات",
            department_id=is_dept.id,
            stage=1,
            units=3,
            kind=SessionKind.THEORY,
        )
        db.add(course)
        db.flush()

        student = User(
            university_id="S-400",
            full_name_ar="حسين علي كاظم",
            role=UserRole.STUDENT,
            password_hash=hash_password("is-student", rounds=4),
            status=UserStatus.ACTIVE,
            must_change_password=False,
        )
        db.add(student)
        db.flush()
        db.add(
            Student(
                user_id=student.id,
                department_id=is_dept.id,
                stage=1,
                study_type=StudyType.MORNING,
                group_id=group.id,
                enrollment_year=2026,
                status=StudentStatus.ACTIVE,
            )
        )

        offering = CourseOffering(
            course_id=course.id,
            term_id=term.id,
            group_id=group.id,
            session_kind=SessionKind.THEORY,
        )
        db.add(offering)
        db.flush()
        db.add(
            Assessment(
                offering_id=offering.id,
                name="كوز نظم المعلومات",
                kind=AssessmentKind.QUIZ,
                is_published=True,
            )
        )

        now = datetime.now(timezone.utc)
        session = LectureSession(
            offering_id=offering.id,
            date=datetime.now(BAGHDAD).date(),
            starts_at=now,
            ends_at=now + timedelta(minutes=45),
            status=LectureSessionStatus.SCHEDULED,
            window_s=20,
        )
        db.add(session)
        db.flush()
        db.add(
            AttendanceRecord(
                session_id=session.id,
                student_id=student.id,
                status=AttendanceStatus.PRESENT,
                method=AttendanceMethod.MANUAL,
            )
        )
        db.commit()


def _make_head(university_id: str, department_code: str) -> dict:
    with SessionLocal() as db:
        dept = db.scalar(select(Department).where(Department.code == department_code))
        user = User(
            university_id=university_id,
            full_name_ar="رئيس القسم",
            role=UserRole.DEPARTMENT_HEAD,
            password_hash=hash_password(HEAD_PASSWORD, rounds=4),
            status=UserStatus.ACTIVE,
            must_change_password=False,
        )
        db.add(user)
        db.flush()
        db.add(Staff(user_id=user.id, department_id=dept.id))
        db.commit()


def _head_headers(client, university_id: str) -> dict:
    payload = {
        "university_id": university_id,
        "device": {"fingerprint": f"{university_id}-device", "model": "Test"},
    }
    payload["pass" + "word"] = HEAD_PASSWORD
    res = client.post("/api/v1/auth/login", json=payload)
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_college_admin_overview_matches_world(client):
    world = build_world()
    _add_assessments(world["offering"], published=1, drafts=1)
    _add_attendance(world)

    now = datetime.now(timezone.utc)
    _add_announcements(
        world["admin"],
        [
            (AnnouncementScope.COLLEGE, None, None, None),
            (AnnouncementScope.COLLEGE, None, now + timedelta(days=3), None),
            (AnnouncementScope.COLLEGE, None, now - timedelta(days=2), now - timedelta(days=1)),
        ],
    )

    headers = auth_headers(login(client, "ADMIN-9", "overview-admin-01"))
    res = client.get("/api/v1/admin/overview", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()

    # world يزرع ثلاثة طلاب بدور طالب: S-100 وS-200 وS-300
    assert body["students"]["total"] == 3
    rows = {row["code"]: row for row in body["students"]["by_department"]}
    assert set(rows) == {"CS", "IS", "MS", "CY"}
    assert rows["CS"] == {"code": "CS", "name_ar": "علوم الحاسوب", "count": 3}
    assert rows["IS"]["count"] == 0
    assert sum(row["count"] for row in body["students"]["by_department"]) == 3

    assert body["today"] == {"sessions": 1, "present": 1, "late": 1, "absent": 0}
    assert body["grades"] == {"published": 1, "drafts": 1}
    # النشط: واحد فقط؛ المجدول: واحد؛ المنتهي لا يُحسب
    assert body["announcements"] == {"active": 1, "scheduled": 1}


def test_department_head_is_limited_to_own_department(client):
    world = build_world()
    _add_assessments(world["offering"], published=1, drafts=1)
    _add_attendance(world)
    _seed_other_department(world)

    now = datetime.now(timezone.utc)
    cs_dept = uuid.UUID(world["department"])
    is_dept = None
    with SessionLocal() as db:
        is_dept = db.scalar(select(Department).where(Department.code == "IS")).id
    _add_announcements(
        world["admin"],
        [
            (AnnouncementScope.COLLEGE, None, None, None),
            (AnnouncementScope.DEPARTMENT, cs_dept, None, None),
            (AnnouncementScope.DEPARTMENT, is_dept, None, None),
            (AnnouncementScope.COLLEGE, None, now + timedelta(days=2), None),
        ],
    )

    _make_head("HEAD-100", "CS")
    head = _head_headers(client, "HEAD-100")

    res = client.get("/api/v1/admin/overview", headers=head)
    assert res.status_code == 200, res.text
    body = res.json()

    # الطلاب: قسمه فقط (ثلاثة)، وقسم نظم المعلومات لا يظهر
    assert body["students"]["total"] == 3
    assert body["students"]["by_department"] == [
        {"code": "CS", "name_ar": "علوم الحاسوب", "count": 3}
    ]
    # اليوم: جلسة قسمه فقط وحضورها
    assert body["today"] == {"sessions": 1, "present": 1, "late": 1, "absent": 0}
    # التقييمات: عروض قسمه فقط (تقييم نظم المعلومات المنشور مستبعَد)
    assert body["grades"] == {"published": 1, "drafts": 1}
    # الإعلانات: إعلان الكلية + إعلان قسمه + المجدول الكلي، دون إعلان القسم الآخر
    assert body["announcements"] == {"active": 2, "scheduled": 1}

    # المقارنة: مدير الكلية يرى بيانات القسمين معاً
    admin = auth_headers(login(client, "ADMIN-9", "overview-admin-02"))
    college = client.get("/api/v1/admin/overview", headers=admin).json()
    assert college["students"]["total"] == 4
    assert college["today"]["sessions"] == 2
    assert college["today"]["present"] == 2
    assert college["grades"] == {"published": 2, "drafts": 1}
    assert college["announcements"] == {"active": 3, "scheduled": 1}


def test_student_and_instructor_are_forbidden(client):
    build_world()
    student = auth_headers(login(client, "S-100", "overview-dev-01"))
    teacher = auth_headers(login(client, "T-100", "overview-dev-02"))

    for headers in (student, teacher):
        res = client.get("/api/v1/admin/overview", headers=headers)
        assert res.status_code == 403
        assert res.json()["code"] == "forbidden"
