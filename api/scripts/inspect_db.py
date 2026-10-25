# -*- coding: utf-8 -*-
"""فحص سريع لقاعدة البيانات بعد الترحيل والتهيئة (لا يُشغَّل في الإنتاج)."""
import sqlite3
import sys
from pathlib import Path

DB = sys.argv[1] if len(sys.argv) > 1 else "autogen.db"
db_path = Path(DB)
if not db_path.exists():
    raise SystemExit(f"missing db: {DB}")

con = sqlite3.connect(db_path)
tables = [
    row[0]
    for row in con.execute(
        "select name from sqlite_master "
        "where type='table' and name != 'alembic_version' order by name"
    )
]
print("tables:", len(tables))
print("departments:", con.execute("select code, name_ar from departments order by code").fetchall())
print("year:", con.execute("select label, is_current from academic_years").fetchall())

ddl = con.execute("select sql from sqlite_master where name='attendance_records'").fetchone()[0]
print("attendance unique:", "uq_attendance_once" in ddl)

names = set(tables)
expected = {
    "users", "students", "staff", "devices", "refresh_tokens", "fcm_tokens",
    "departments", "academic_years", "terms", "groups", "courses",
    "course_offerings", "enrollments", "rooms", "timetable_slots",
    "timetable_changes", "lecture_sessions", "attendance_records",
    "absence_excuses", "files", "materials", "assessments", "grades",
    "announcements", "announcement_reads", "notifications", "requests",
    "request_messages", "audit_logs",
}
print("missing tables:", sorted(expected - names))
print("unexpected tables:", sorted(names - expected))
