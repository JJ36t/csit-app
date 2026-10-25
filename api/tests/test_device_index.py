# -*- coding: utf-8 -*-
"""اختبار الفهرس الفريد الجزئي: جهاز نشط واحد لكل مستخدم (ترحيل 0002)."""
import os
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]


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


def _insert_user(con: sqlite3.Connection) -> str:
    user_id = str(uuid.uuid4())
    con.execute(
        "insert into users (id, university_id, full_name_ar, role, password_hash, "
        "status, must_change_password) values (?,?,?,?,?,?,?)",
        (user_id, f"U-{user_id[:8]}", "مستخدم اختبار", "student", "hash", "active", 0),
    )
    return user_id


def test_one_active_device_per_user(tmp_path):
    db = tmp_path / "index.db"
    url = f"sqlite:///{db}"
    result = _run_alembic(url, "upgrade", "head")
    assert result.returncode == 0, result.stdout + result.stderr

    con = sqlite3.connect(db)
    try:
        user_id = _insert_user(con)
        con.execute(
            "insert into devices (id, user_id, device_fingerprint, status) "
            "values (?,?,?,?)",
            (str(uuid.uuid4()), user_id, "fingerprint-one", "active"),
        )
        # جهاز ثانٍ نشط لنفس المستخدم → يجب أن يرفضه الفهرس الجزئي
        try:
            con.execute(
                "insert into devices (id, user_id, device_fingerprint, status) "
                "values (?,?,?,?)",
                (str(uuid.uuid4()), user_id, "fingerprint-two", "active"),
            )
            con.commit()
            raise AssertionError("الفهرس الفريد الجزئي لم يمنع جهازاً نشطاً ثانياً")
        except sqlite3.IntegrityError:
            pass

        # جهاز ملغى مسموح (الجزئي يستثنيه)
        con.execute(
            "insert into devices (id, user_id, device_fingerprint, status) "
            "values (?,?,?,?)",
            (str(uuid.uuid4()), user_id, "fingerprint-three", "revoked"),
        )
        con.commit()
    finally:
        con.close()

    downgrade = _run_alembic(url, "downgrade", "0001")
    assert downgrade.returncode == 0, downgrade.stdout + downgrade.stderr
