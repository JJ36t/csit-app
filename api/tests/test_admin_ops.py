# -*- coding: utf-8 -*-
"""اختبارات إدارة المستخدمين: القائمة والترشيح، إعادة ضبط الجهاز وكلمة المرور، نطاق رئيس القسم، وسجل التدقيق."""
from datetime import datetime, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.models import (
    AcademicYear,
    AuditLog,
    Department,
    Group,
    Staff,
    Student,
    Term,
    User,
)
from app.models.enums import StudentStatus, StudyType, UserRole, UserStatus
from app.security import hash_password

HEAD_PASSWORD = "Head#2026"
DEVICE_A = {"fingerprint": "student-device-aaaa", "model": "Pixel"}
DEVICE_B = {"fingerprint": "student-device-bbbb", "model": "Redmi"}


def _make_student(
    university_id: str,
    dept_code: str,
    name: str = "طالب اختبار",
    group_id=None,
) -> None:
    with SessionLocal() as db:
        dept = db.scalar(select(Department).where(Department.code == dept_code))
        user = User(
            university_id=university_id,
            full_name_ar=name,
            role=UserRole.STUDENT,
            password_hash=hash_password(university_id, rounds=4),
            status=UserStatus.ACTIVE,
            must_change_password=True,
        )
        db.add(user)
        db.flush()
        db.add(
            Student(
                user_id=user.id,
                department_id=dept.id,
                stage=1,
                study_type=StudyType.MORNING,
                group_id=group_id,
                enrollment_year=2026,
                status=StudentStatus.ACTIVE,
            )
        )
        db.commit()


def _make_group(dept_code: str, name: str = "A"):
    """شعبة ضمن القسم (والفصل الحالي) لإظهار عمود الشعبة في القائمة."""
    with SessionLocal() as db:
        dept = db.scalar(select(Department).where(Department.code == dept_code))
        year = db.scalar(select(AcademicYear).where(AcademicYear.label == "2026-2027"))
        if year is None:
            year = AcademicYear(label="2026-2027", is_current=True)
            db.add(year)
            db.flush()
        term = db.scalar(select(Term).where(Term.academic_year_id == year.id))
        if term is None:
            term = Term(academic_year_id=year.id, name="الفصل الأول", is_current=True)
            db.add(term)
            db.flush()
        group = Group(
            department_id=dept.id,
            stage=1,
            name=name,
            study_type=StudyType.MORNING,
            term_id=term.id,
        )
        db.add(group)
        db.commit()
        return group.id


def _make_instructor(university_id: str, dept_code: str) -> None:
    with SessionLocal() as db:
        dept = db.scalar(select(Department).where(Department.code == dept_code))
        user = User(
            university_id=university_id,
            full_name_ar="تدريسي اختبار",
            role=UserRole.INSTRUCTOR,
            password_hash=hash_password(university_id, rounds=4),
            status=UserStatus.ACTIVE,
            must_change_password=False,
        )
        db.add(user)
        db.flush()
        db.add(Staff(user_id=user.id, department_id=dept.id, academic_title="مدرس"))
        db.commit()


def _make_head(university_id: str, dept_code: str) -> None:
    with SessionLocal() as db:
        dept = db.scalar(select(Department).where(Department.code == dept_code))
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
        db.add(Staff(user_id=user.id, department_id=dept.id, academic_title="أستاذ"))
        db.commit()


def _login(client, university_id: str, password: str, device=DEVICE_A):
    return client.post(
        "/api/v1/auth/login",
        json={"university_id": university_id, "password": password, "device": device},
    )


def _head_client(client, university_id: str):
    _make_head(university_id, "CS")
    res = _login(client, university_id, HEAD_PASSWORD, {"fingerprint": f"{university_id}-dev"})
    assert res.status_code == 200, res.text
    return {**client.headers, "Authorization": f"Bearer {res.json()['access_token']}"}


def test_device_reset_allows_new_device(client, admin_client):
    _make_student("20260001", "CS")
    assert _login(client, "20260001", "20260001").status_code == 200

    blocked = _login(client, "20260001", "20260001", DEVICE_B)
    assert blocked.status_code == 403
    assert blocked.json()["code"] == "device_change_requires_approval"

    reset = admin_client.post("/api/v1/admin/users/20260001/device/reset")
    assert reset.status_code == 200, reset.text
    assert reset.json()["devices_revoked"] == 1
    assert reset.json()["sessions_revoked"] >= 1

    after = _login(client, "20260001", "20260001", DEVICE_B)
    assert after.status_code == 200, after.text


def test_department_head_scope(client):
    _make_student("20260002", "CS")
    _make_student("20260003", "IS")
    headers = _head_client(client, "HEAD-CS")

    own = client.post(
        "/api/v1/admin/users/20260002/device/reset", headers=headers
    )
    assert own.status_code == 200

    other = client.post(
        "/api/v1/admin/users/20260003/device/reset", headers=headers
    )
    assert other.status_code == 403
    assert other.json()["code"] == "outside_your_department"


def test_password_reset_returns_working_temporary_password(client, admin_client):
    _make_student("20260004", "CS")
    assert _login(client, "20260004", "20260004").status_code == 200

    res = admin_client.post("/api/v1/admin/users/20260004/reset-password")
    assert res.status_code == 200, res.text
    temp = res.json()["temporary_password"]
    assert len(temp) >= 8

    # القديمة لم تعد تعمل
    assert _login(client, "20260004", "20260004").status_code == 401

    # المؤقتة تعمل وتُجبر التغيير
    ok = _login(client, "20260004", temp)
    assert ok.status_code == 200, ok.text
    assert ok.json()["user"]["must_change_password"] is True


def test_audit_log_records_sensitive_actions(client, admin_client):
    _make_student("20260005", "CS")
    _login(client, "20260005", "20260005")
    admin_client.post("/api/v1/admin/users/20260005/device/reset")
    admin_client.post("/api/v1/admin/users/20260005/reset-password")

    with SessionLocal() as db:
        actions = {
            row.action
            for row in db.scalars(
                select(AuditLog).where(AuditLog.entity_id == "20260005")
            )
        }
    assert {"login_success", "device_reset", "password_reset"} <= actions


def test_login_failure_is_audited(client):
    _make_student("20260006", "CS")
    res = _login(client, "20260006", "wrong-password")
    assert res.status_code == 401

    with SessionLocal() as db:
        rows = list(
            db.scalars(
                select(AuditLog).where(
                    AuditLog.entity_id == "20260006",
                    AuditLog.action == "login_failed",
                )
            )
        )
    assert len(rows) == 1
    assert rows[0].actor_id is None


def test_list_users_college_admin_sees_all(client, admin_client):
    group = _make_group("CS", "A")
    _make_student("20260101", "CS", "علي حسن", group_id=group)
    _make_student("20260102", "IS", "زينب كريم")
    _make_instructor("T-200", "IS")

    # محذوف حذفاً ناعماً — لا يظهر في القائمة
    _make_student("20260103", "CS", "طالب محذوف")
    with SessionLocal() as db:
        gone = db.scalar(select(User).where(User.university_id == "20260103"))
        gone.deleted_at = datetime.now(timezone.utc)
        db.commit()

    res = admin_client.get("/api/v1/admin/users")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total"] == 4  # مدير الكلية + طالبان + تدريسي
    assert body["page"] == 1
    assert body["limit"] == 50

    rows = {row["university_id"]: row for row in body["items"]}
    assert set(rows) == {"ADMIN-001", "20260101", "20260102", "T-200"}
    assert "20260103" not in rows

    student = rows["20260101"]
    assert student["full_name_ar"] == "علي حسن"
    assert student["role"] == "student"
    assert student["status"] == "active"
    assert student["must_change_password"] is True
    assert student["department_code"] == "CS"
    assert student["department_name_ar"] == "علوم الحاسوب"
    assert student["group_name"] == "A"
    assert student["device_status"] == "none"

    # التدريسي: قسمه من بطاقة staff، وبلا شعبة ولا جهاز
    teacher = rows["T-200"]
    assert teacher["role"] == "instructor"
    assert teacher["department_code"] == "IS"
    assert teacher["group_name"] is None
    assert teacher["device_status"] == "none"

    # مدير الكلية بلا بطاقة طالب/تدريسي، وجهازه نشط لأنه سجّل الدخول للتو
    assert rows["ADMIN-001"]["department_code"] is None
    assert rows["ADMIN-001"]["device_status"] == "active"

    # لا حقول سرّية في الاستجابة
    for row in body["items"]:
        assert set(row) == {
            "user_id",
            "university_id",
            "full_name_ar",
            "role",
            "status",
            "must_change_password",
            "department_code",
            "department_name_ar",
            "group_name",
            "device_status",
        }


def test_list_users_department_head_sees_only_own_students(client):
    _make_student("20260201", "CS", "طالب قسم الحاسوب")
    _make_student("20260202", "IS", "طالب قسم النظم")
    _make_instructor("T-300", "CS")
    headers = _head_client(client, "HEAD-CS")

    body = client.get("/api/v1/admin/users", headers=headers).json()
    assert body["total"] == 1
    assert [row["university_id"] for row in body["items"]] == ["20260201"]
    assert body["items"][0]["department_code"] == "CS"

    # التدريسي في القسم نفسه ليس طالباً — لا يظهر في نطاق رئيس القسم
    assert "T-300" not in {row["university_id"] for row in body["items"]}

    # ولا يظهر طالب قسم آخر حتى مع بحث صريح
    other = client.get(
        "/api/v1/admin/users", headers=headers, params={"q": "20260202"}
    ).json()
    assert other["total"] == 0
    assert other["items"] == []


def test_list_users_pagination_and_filters(client, admin_client):
    for index in range(5):
        _make_student(f"2026030{index}", "CS", f"طالب حاسوب {index}")
    _make_student("20260310", "IS", "طالب نظم")

    first = admin_client.get("/api/v1/admin/users", params={"page": 1, "limit": 2}).json()
    assert first["total"] == 7  # خمسة طلاب CS + طالب IS + مدير الكلية
    assert len(first["items"]) == 2

    last = admin_client.get("/api/v1/admin/users", params={"page": 4, "limit": 2}).json()
    assert len(last["items"]) == 1
    assert last["page"] == 4

    # البحث بالرقم الجامعي وبالاسم
    by_id = admin_client.get("/api/v1/admin/users", params={"q": "20260310"}).json()
    assert [row["university_id"] for row in by_id["items"]] == ["20260310"]

    by_name = admin_client.get("/api/v1/admin/users", params={"q": "طالب نظم"}).json()
    assert by_name["total"] == 1

    partial = admin_client.get("/api/v1/admin/users", params={"q": "حاسوب"}).json()
    assert partial["total"] == 5

    # ترشيح الدور والقسم
    students = admin_client.get("/api/v1/admin/users", params={"role": "student"}).json()
    assert students["total"] == 6
    assert {row["role"] for row in students["items"]} == {"student"}

    cs = admin_client.get(
        "/api/v1/admin/users", params={"department_code": "is"}
    ).json()
    assert [row["university_id"] for row in cs["items"]] == ["20260310"]
    assert cs["items"][0]["department_name_ar"] == "نظم المعلومات"

    # قيود المعاملات: دور غير معروف أو حد أكبر من 200
    assert client.get("/api/v1/admin/users", params={"role": "teacher"}).status_code == 422
    assert client.get("/api/v1/admin/users", params={"limit": 201}).status_code == 422
