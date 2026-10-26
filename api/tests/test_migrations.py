# -*- coding: utf-8 -*-
"""اختبار سلسلة الترحيل: upgrade ← downgrade ← upgrade + القيود الأساسية."""
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

API_DIR = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = 29  # كما في الخطة، القسم 8


def _run_alembic(db_url: str, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "DATABASE_URL": db_url}
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=API_DIR,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_upgrade_downgrade_upgrade(tmp_path):
    db = tmp_path / "mig.db"
    url = f"sqlite:///{db}"

    r = _run_alembic(url, "upgrade", "head")
    assert r.returncode == 0, r.stdout + r.stderr

    eng = create_engine(url)
    tables = set(inspect(eng).get_table_names()) - {"alembic_version"}
    assert len(tables) == EXPECTED_TABLES
    eng.dispose()

    r = _run_alembic(url, "downgrade", "base")
    assert r.returncode == 0, r.stdout + r.stderr

    eng = create_engine(url)
    remaining = set(inspect(eng).get_table_names()) - {"alembic_version"}
    assert remaining == set()
    eng.dispose()

    r = _run_alembic(url, "upgrade", "head")
    assert r.returncode == 0, r.stdout + r.stderr


def test_key_constraints(tmp_path):
    db = tmp_path / "cons.db"
    url = f"sqlite:///{db}"
    r = _run_alembic(url, "upgrade", "head")
    assert r.returncode == 0, r.stdout + r.stderr

    eng = create_engine(url)
    insp = inspect(eng)

    attendance_uqs = {uc["name"] for uc in insp.get_unique_constraints("attendance_records")}
    assert "uq_attendance_once" in attendance_uqs

    grades_uqs = {uc["name"] for uc in insp.get_unique_constraints("grades")}
    assert "uq_grade_once" in grades_uqs

    enrollments_uqs = {uc["name"] for uc in insp.get_unique_constraints("enrollments")}
    assert "uq_enrollment_once" in enrollments_uqs

    slot_indexes = {ix["name"] for ix in insp.get_indexes("timetable_slots")}
    assert "ix_timetable_slots_offering_weekday" in slot_indexes
    eng.dispose()


def test_upgrade_0004_with_existing_rows(tmp_path):
    """SQLite القديم: إضافة created_at إلى جدول فيه صفوف (كان يفشل قبل إصلاح batch)."""
    db = tmp_path / "existing.db"
    url = f"sqlite:///{db}"

    r = _run_alembic(url, "upgrade", "0003")
    assert r.returncode == 0, r.stdout + r.stderr

    eng = create_engine(url)
    with eng.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO audit_logs (id, action, entity, entity_id) "
                "VALUES ('seed0001', 'seed', 'table', 'x')"
            )
        )
    eng.dispose()

    r = _run_alembic(url, "upgrade", "head")
    assert r.returncode == 0, r.stdout + r.stderr

    eng = create_engine(url)
    columns = {col["name"] for col in inspect(eng).get_columns("audit_logs")}
    assert "created_at" in columns
    with eng.connect() as conn:
        value = conn.execute(text("SELECT created_at FROM audit_logs")).scalar()
    assert value is not None, "الصفوف القديمة يجب أن تحصل على وقت افتراضي"

    # الفهارس تبقى بعد إعادة بناء الجدول
    indexes = {ix["name"] for ix in inspect(eng).get_indexes("audit_logs")}
    assert "ix_audit_logs_action" in indexes and "ix_audit_logs_entity" in indexes
    eng.dispose()

    r = _run_alembic(url, "downgrade", "0003")
    assert r.returncode == 0, r.stdout + r.stderr

    eng = create_engine(url)
    columns = {col["name"] for col in inspect(eng).get_columns("audit_logs")}
    assert "created_at" not in columns
    eng.dispose()
