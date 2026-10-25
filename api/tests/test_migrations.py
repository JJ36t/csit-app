# -*- coding: utf-8 -*-
"""اختبار سلسلة الترحيل: upgrade ← downgrade ← upgrade + القيود الأساسية."""
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

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
