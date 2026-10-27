# -*- coding: utf-8 -*-
"""اختبارات إنشاء الشعب وعروض المواد والتقارير (حضور/درجات بصيغة JSON وCSV)."""
import uuid
from decimal import Decimal

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Assessment, AttendanceRecord, Course, Enrollment, Grade, LectureSession
from app.models.enums import (
    AssessmentKind,
    AttendanceMethod,
    AttendanceStatus,
    LectureSessionStatus,
    SessionKind,
)
from world import auth_headers, build_world, login


def _new_course(world: dict, *, code: str = "CS102", stage: int = 1) -> str:
    with SessionLocal() as db:
        course = Course(
            code=code,
            name_ar="هياكل البيانات",
            department_id=uuid.UUID(world["department"]),
            stage=stage,
            units=3,
            kind=SessionKind.THEORY,
        )
        db.add(course)
        db.commit()
        return str(course.id)


def test_admin_creates_group_and_rejects_duplicate(client):
    world = build_world()
    admin = auth_headers(login(client, "ADMIN-9", "acad-dev-01"))

    created = client.post(
        "/api/v1/admin/groups",
        json={
            "department_id": world["department"],
            "stage": 1,
            "name": "B",
            "study_type": "morning",
            "term_id": world["term"],
        },
        headers=admin,
    )
    assert created.status_code == 200, created.text
    assert created.json()["name"] == "B"
    assert created.json()["department_code"] == "CS"

    duplicate = client.post(
        "/api/v1/admin/groups",
        json={
            "department_id": world["department"],
            "stage": 1,
            "name": "B",
            "study_type": "morning",
            "term_id": world["term"],
        },
        headers=admin,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "group_exists"

    listed = client.get(
        f"/api/v1/admin/groups?department_id={world['department']}&stage=1", headers=admin
    ).json()["items"]
    assert {row["name"] for row in listed} == {"A", "B"}

    # طالب لا يرى قائمة الشعب الإدارية
    student = auth_headers(login(client, "S-100", "acad-dev-02"))
    assert client.get("/api/v1/admin/groups", headers=student).status_code == 403


def test_offering_creation_auto_enrolls_group_students(client):
    world = build_world()
    admin = auth_headers(login(client, "ADMIN-9", "acad-dev-03"))
    course_id = _new_course(world)

    created = client.post(
        "/api/v1/admin/offerings",
        json={
            "course_id": course_id,
            "group_id": world["group"],
            "instructor_id": world["instructor"],
            "session_kind": "theory",
        },
        headers=admin,
    )
    assert created.status_code == 200, created.text
    payload = created.json()
    assert payload["enrolled"] == 3  # S-100 وS-200 وS-300 في الشعبة A
    assert payload["course_code"] == "CS102"

    with SessionLocal() as db:
        rows = db.scalars(
            select(Enrollment).where(Enrollment.offering_id == uuid.UUID(payload["offering_id"]))
        ).all()
        assert len(rows) == 3
        assert all(row.source.value == "auto" for row in rows)

    duplicate = client.post(
        "/api/v1/admin/offerings",
        json={"course_id": course_id, "group_id": world["group"], "session_kind": "theory"},
        headers=admin,
    )
    assert duplicate.status_code == 409

    # مادة من مرحلة أخرى لا تصلح لشعبة المرحلة الأولى
    other_stage = _new_course(world, code="CS201", stage=2)
    mismatch = client.post(
        "/api/v1/admin/offerings",
        json={"course_id": other_stage, "group_id": world["group"]},
        headers=admin,
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["code"] == "course_group_mismatch"


def test_attendance_report_json_and_csv(client):
    world = build_world()
    teacher = auth_headers(login(client, "T-100", "acad-dev-04"))

    with SessionLocal() as db:
        session = db.get(LectureSession, uuid.UUID(world["session"]))
        session.status = LectureSessionStatus.CLOSED
        db.add_all(
            [
                AttendanceRecord(
                    session_id=session.id,
                    student_id=uuid.UUID(world["student"]),
                    status=AttendanceStatus.PRESENT,
                    method=AttendanceMethod.QR,
                ),
                AttendanceRecord(
                    session_id=session.id,
                    student_id=uuid.UUID(world["other"]),
                    status=AttendanceStatus.LATE,
                    method=AttendanceMethod.QR,
                    flagged=True,
                ),
            ]
        )
        db.commit()

    report = client.get(
        f"/api/v1/admin/reports/attendance?offering_id={world['offering']}", headers=teacher
    )
    assert report.status_code == 200, report.text
    body = report.json()
    assert body["offering"]["course_code"] == "CS101"
    assert body["totals"]["held"] == 1
    assert body["totals"]["present"] == 1
    assert body["totals"]["late"] == 1
    assert body["totals"]["attendance_rate"] == 100.0
    assert len(body["students"]) == 2

    csv_response = client.get(
        f"/api/v1/admin/reports/attendance?offering_id={world['offering']}&format=csv",
        headers=teacher,
    )
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in csv_response.headers["content-disposition"]
    text = csv_response.content.decode("utf-8-sig")
    assert "الرقم الجامعي" in text
    assert "S-100" in text and "S-200" in text

    # طالب لا يصل إلى التقارير
    student = auth_headers(login(client, "S-100", "acad-dev-05"))
    assert (
        client.get(
            f"/api/v1/admin/reports/attendance?offering_id={world['offering']}", headers=student
        ).status_code
        == 403
    )


def test_grades_report_weighted_total_and_csv(client):
    world = build_world()
    teacher = auth_headers(login(client, "T-100", "acad-dev-06"))

    with SessionLocal() as db:
        assessment = Assessment(
            offering_id=uuid.UUID(world["offering"]),
            name="كوز أول",
            kind=AssessmentKind.QUIZ,
            max_score=Decimal("10"),
            weight=Decimal("20"),
            is_published=True,
        )
        db.add(assessment)
        db.flush()
        db.add(
            Grade(
                assessment_id=assessment.id,
                student_id=uuid.UUID(world["student"]),
                score=Decimal("8"),
                entered_by=uuid.UUID(world["instructor"]),
            )
        )
        db.commit()

    report = client.get(
        f"/api/v1/admin/reports/grades?offering_id={world['offering']}", headers=teacher
    )
    assert report.status_code == 200, report.text
    body = report.json()
    assert body["total_weight"] == 20.0
    assert body["assessments"][0]["graded"] == 1
    assert body["assessments"][0]["average"] == 8.0
    assert body["assessments"][0]["contribution_average"] == 1.6

    student_row = next(row for row in body["students"] if row["university_id"] == "S-100")
    assert student_row["weighted_total"] == 1.6

    csv_response = client.get(
        f"/api/v1/admin/reports/grades?offering_id={world['offering']}&format=csv",
        headers=teacher,
    )
    assert csv_response.status_code == 200
    text = csv_response.content.decode("utf-8-sig")
    assert "كوز أول (10)" in text
    assert "المجموع الموزون" in text

def test_terms_endpoint_lists_current_term(client):
    world = build_world()
    admin = auth_headers(login(client, "ADMIN-9", "acad-dev-term-01"))
    listed = client.get("/api/v1/admin/terms", headers=admin)
    assert listed.status_code == 200, listed.text
    items = listed.json()["items"]
    assert items and items[0]["term_id"] == world["term"]
    assert items[0]["is_current"] is True

    student = auth_headers(login(client, "S-100", "acad-dev-term-02"))
    assert client.get("/api/v1/admin/terms", headers=student).status_code == 403