# -*- coding: utf-8 -*-
"""اختبارات إدارة المستخدمين: إعادة ضبط الجهاز وكلمة المرور، نطاق رئيس القسم، وسجل التدقيق."""
from sqlalchemy import select

from app.db import SessionLocal
from app.models import AuditLog, Department, Staff, Student, User
from app.models.enums import StudentStatus, StudyType, UserRole, UserStatus
from app.security import hash_password

HEAD_PASSWORD = "Head#2026"
DEVICE_A = {"fingerprint": "student-device-aaaa", "model": "Pixel"}
DEVICE_B = {"fingerprint": "student-device-bbbb", "model": "Redmi"}


def _make_student(university_id: str, dept_code: str, name: str = "طالب اختبار") -> None:
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
                enrollment_year=2026,
                status=StudentStatus.ACTIVE,
            )
        )
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
