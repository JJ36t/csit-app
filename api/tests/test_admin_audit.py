# -*- coding: utf-8 -*-
"""اختبارات سجل التدقيق: تخزين created_at، صلاحية مدير الكلية، والترشيح.

الترشيح بالتاريخ يُفحص على حدود توقيت بغداد (+3) لا على UTC، لأن النقطة تحوّل
اليوم المحلي إلى نافذة UTC قبل المقارنة.
"""
from datetime import datetime, timezone

from sqlalchemy import delete, select

from app.db import SessionLocal
from app.models import AuditLog, Department, Staff, Student, User
from app.models.enums import StudentStatus, StudyType, UserRole, UserStatus
from app.security import hash_password
from app.services.audit import log_action

AUDIT_URL = "/api/v1/admin/audit"
HEAD_PASSWORD = "Head#Pass123"
STUDENT_PASSWORD = "Student#Pass123"


def _make_head(university_id: str) -> None:
    with SessionLocal() as db:
        dept = db.scalar(select(Department).where(Department.code == "CS"))
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


def _make_student(university_id: str) -> None:
    with SessionLocal() as db:
        dept = db.scalar(select(Department).where(Department.code == "CS"))
        user = User(
            university_id=university_id,
            full_name_ar="طالب اختبار",
            role=UserRole.STUDENT,
            password_hash=hash_password(STUDENT_PASSWORD, rounds=4),
            status=UserStatus.ACTIVE,
            must_change_password=False,
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


def _headers(client, university_id: str, password: str) -> dict:
    res = client.post(
        "/api/v1/auth/login",
        json={
            "university_id": university_id,
            "password": password,
            "device": {"fingerprint": f"{university_id}-dev", "model": "Test"},
        },
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _admin(db) -> User:
    return db.scalar(select(User).where(User.role == UserRole.COLLEGE_ADMIN))


def _clear(db) -> None:
    """دخول مدير اللوحة نفسه يُسجَّل في التدقيق — نمسحه لعزل ما تزرعه كل حالة."""
    db.execute(delete(AuditLog))


def _seed(db, rows: list[tuple[str, str, datetime]]) -> None:
    """يُدخل سجلات تدقيق بأوقات محدّدة (UTC) لفحص الترتيب والترشيح."""
    _clear(db)
    actor = _admin(db)
    for action, entity_id, when in rows:
        row = log_action(db, actor=actor, action=action, entity="user", entity_id=entity_id)
        row.created_at = when
    db.commit()


def test_audit_log_stores_created_at(client, admin_client):
    with SessionLocal() as db:
        row = log_action(
            db,
            actor=_admin(db),
            action="grades_update",
            entity="grade",
            entity_id="G-1",
            before={"score": 10},
            after={"score": 12},
            ip="127.0.0.1",
            commit=True,
        )
        audit_id = row.id

    with SessionLocal() as db:
        stored = db.get(AuditLog, audit_id)
        assert stored is not None
        # العمود يُملأ تلقائياً من الخادم (server_default) لا من التطبيق
        assert stored.created_at is not None
        assert stored.before == {"score": 10}
        assert stored.after == {"score": 12}


def test_admin_lists_audit_rows_newest_first(client, admin_client):
    with SessionLocal() as db:
        _seed(
            db,
            [
                ("device_reset", "20260001", datetime(2026, 10, 20, 9, 0, tzinfo=timezone.utc)),
                ("password_reset", "20260001", datetime(2026, 10, 21, 9, 0, tzinfo=timezone.utc)),
            ],
        )
        actor_university_id = _admin(db).university_id

    res = admin_client.get(AUDIT_URL)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total"] == 2
    assert body["page"] == 1 and body["limit"] == 50
    assert [item["action"] for item in body["items"]] == ["password_reset", "device_reset"]

    newest = body["items"][0]
    # عقد الواجهة: هذه الحقول بالضبط يعرضها جدول لوحة التحكم
    assert set(newest) == {
        "audit_id",
        "created_at",
        "actor_university_id",
        "actor_name_ar",
        "action",
        "entity",
        "entity_id",
        "ip",
        "before",
        "after",
    }
    assert newest["actor_university_id"] == actor_university_id
    assert newest["actor_name_ar"] == "مدير الكلية"
    assert newest["entity"] == "user"
    assert newest["entity_id"] == "20260001"
    assert newest["created_at"] is not None and newest["created_at"].endswith("+00:00")


def test_audit_is_forbidden_for_head_and_student(client):
    _make_head("HEAD-CS")
    assert client.get(AUDIT_URL, headers=_headers(client, "HEAD-CS", HEAD_PASSWORD)).status_code == 403

    _make_student("20260010")
    res = client.get(AUDIT_URL, headers=_headers(client, "20260010", STUDENT_PASSWORD))
    assert res.status_code == 403
    assert res.json()["code"] == "forbidden"


def test_filters_by_action_and_baghdad_date_range(client, admin_client):
    with SessionLocal() as db:
        _seed(
            db,
            [
                ("device_reset", "20260001", datetime(2026, 1, 5, 10, 0, tzinfo=timezone.utc)),
                ("password_reset", "20260001", datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)),
                # 22:00 UTC = 01:00 بغداد يوم 6 كانون الثاني — يجب ألا يظهر في سجلات يوم 5
                ("login_success", "20260003", datetime(2026, 1, 5, 22, 0, tzinfo=timezone.utc)),
                ("device_reset", "20260002", datetime(2026, 1, 9, 10, 0, tzinfo=timezone.utc)),
            ],
        )

    res = admin_client.get(AUDIT_URL, params={"action": "device_reset"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total"] == 2
    assert {item["entity_id"] for item in body["items"]} == {"20260001", "20260002"}

    res = admin_client.get(AUDIT_URL, params={"date_from": "2026-01-05", "date_to": "2026-01-05"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total"] == 2
    assert {(item["action"], item["entity_id"]) for item in body["items"]} == {
        ("device_reset", "20260001"),
        ("password_reset", "20260001"),
    }

    # اليوم التالي يلتقط السجل الذي وقع بعد منتصف ليل بغداد
    res = admin_client.get(AUDIT_URL, params={"date_from": "2026-01-06", "date_to": "2026-01-06"})
    assert res.status_code == 200, res.text
    assert [item["action"] for item in res.json()["items"]] == ["login_success"]


def test_filters_by_query_and_actor(client, admin_client):
    with SessionLocal() as db:
        _clear(db)
        actor = _admin(db)
        mine = log_action(db, actor=actor, action="device_reset", entity="user", entity_id="20260001")
        mine.created_at = datetime(2026, 2, 1, 9, 0, tzinfo=timezone.utc)
        anonymous = log_action(db, actor=None, action="login_failed", entity="user", entity_id="20260099")
        anonymous.created_at = datetime(2026, 2, 1, 10, 0, tzinfo=timezone.utc)
        db.commit()
        actor_university_id = actor.university_id

    res = admin_client.get(AUDIT_URL, params={"actor": actor_university_id})
    assert res.status_code == 200, res.text
    assert [item["entity_id"] for item in res.json()["items"]] == ["20260001"]

    # سجل فاشل الدخول بلا فاعل: يظهر في البحث بالكيان مع حقول فاعل فارغة
    res = admin_client.get(AUDIT_URL, params={"q": "20260099"})
    assert res.status_code == 200, res.text
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["actor_university_id"] is None
    assert items[0]["action"] == "login_failed"
