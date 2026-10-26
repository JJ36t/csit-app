# -*- coding: utf-8 -*-
"""نسخة احتياطية لقاعدة PostgreSQL بصيغة pg_dump المخصّصة (-Fc).

    python scripts/backup_db.py
    python scripts/backup_db.py --out-dir D:\\csit-backups

يقرأ عنوان القاعدة من DATABASE_URL (أو ملف api/.env)، ويكتب الملف في
api/backups/csit-YYYYMMDD-HHMMSS.dump. لا تُكتب كلمة المرور في الكود:
تُؤخذ من عنوان القاعدة أو من PGPASSWORD في البيئة وتُمرَّر لعملية pg_dump.
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.engine import make_url  # noqa: E402

from app.config import settings  # noqa: E402

API_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = API_DIR / "backups"
PG_GLOBS = (
    r"C:\Program Files\PostgreSQL\*\bin",
    r"C:\Program Files (x86)\PostgreSQL\*\bin",
)


def _version_key(directory: str) -> tuple[int, ...]:
    """مفتاح ترتيب رقمي لنسخة PostgreSQL (18 أحدث من 9)."""
    return tuple(int(part) for part in re.findall(r"\d+", Path(directory).parent.name))


def pg_bin_dirs() -> list[Path]:
    """مجلدات bin المرشّحة من تثبيتات PostgreSQL، الأحدث أولاً."""
    dirs: list[Path] = []
    for pattern in PG_GLOBS:
        dirs += [Path(match) for match in sorted(glob.glob(pattern), key=_version_key, reverse=True)]
    return dirs


def find_pg_dump(explicit: str | None) -> Path:
    """يبحث عن pg_dump في --pg-dump ثم PG_DUMP ثم PATH ثم مجلدات PostgreSQL المعتادة."""
    candidate = explicit or os.environ.get("PG_DUMP")
    if candidate:
        path = Path(candidate)
        if path.is_file():
            return path
        raise SystemExit(f"لم أجد pg_dump في المسار المحدَّد: {path}")

    found = shutil.which("pg_dump")
    if found:
        return Path(found)

    for directory in pg_bin_dirs():
        path = directory / "pg_dump.exe"
        if path.is_file():
            return path

    raise SystemExit(
        "لم أجد pg_dump. ثبّت أدوات PostgreSQL أو مرّر مساره صراحةً:\n"
        "    python scripts/backup_db.py --pg-dump \"C:\\Program Files\\PostgreSQL\\18\\bin\\pg_dump.exe\"\n"
        "أو أضف مجلد bin إلى PATH أو اضبط PG_DUMP."
    )


def postgres_url(raw: str):
    """يتحقق أن العنوان PostgreSQL ويعيد أجزاءه (بلا طباعة كلمة المرور)."""
    try:
        url = make_url(raw)
    except Exception as exc:  # noqa: BLE001 — رسالة عربية بدل تتبّع SQLAlchemy
        raise SystemExit(f"DATABASE_URL غير صالح: {exc}") from exc

    if url.get_backend_name() != "postgresql":
        raise SystemExit(
            f"DATABASE_URL ليس عنوان PostgreSQL (النوع الحالي: {url.get_backend_name()}).\n"
            "هذا السكربت للنسخ الاحتياطي من PostgreSQL فقط؛ اضبط مثلاً:\n"
            "    DATABASE_URL=postgresql+psycopg://csit:PASSWORD@localhost:5432/csit"
        )
    if not url.database:
        raise SystemExit("DATABASE_URL لا يحدّد اسم قاعدة البيانات.")
    return url


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{num_bytes} B"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="نسخة احتياطية لقاعدة PostgreSQL (pg_dump -Fc) إلى api/backups/.",
        epilog="كلمة المرور تُقرأ من DATABASE_URL أو PGPASSWORD — لا تُكتب في الكود.",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="مجلد المخرجات (افتراضياً api/backups)")
    parser.add_argument("--database-url", help="عنوان القاعدة (افتراضياً DATABASE_URL أو api/.env)")
    parser.add_argument("--pg-dump", help="مسار pg_dump إن لم يكن على PATH")
    args = parser.parse_args()

    raw_url = args.database_url or os.environ.get("DATABASE_URL") or settings.database_url
    url = postgres_url(raw_url)
    pg_dump = find_pg_dump(args.pg_dump)

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"csit-{datetime.now():%Y%m%d-%H%M%S}.dump"

    command = [
        str(pg_dump),
        "--format=custom",
        "--no-password",
        "--file", str(target),
    ]
    if url.host:
        command += ["--host", url.host]
    if url.port:
        command += ["--port", str(url.port)]
    if url.username:
        command += ["--username", url.username]
    command += ["--dbname", url.database]

    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password

    print(f"pg_dump: {pg_dump}")
    print(f"المصدر: {url.username or '(مستخدم النظام)'}@{url.host or 'localhost'}:{url.port or 5432}/{url.database}")
    print(f"الهدف: {target}")

    started = time.perf_counter()
    result = subprocess.run(command, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    elapsed = time.perf_counter() - started

    if result.returncode != 0:
        # لا نُبقي ملفاً ناقصاً كي لا يلتقطه verify_restore كأحدث نسخة.
        target.unlink(missing_ok=True)
        detail = (result.stderr or result.stdout or "").strip()
        raise SystemExit(
            "فشل إنشاء النسخة الاحتياطية (pg_dump).\n"
            "تحقق من: تشغيل PostgreSQL، صحة DATABASE_URL، ووجود كلمة المرور في PGPASSWORD أو في العنوان.\n"
            f"الأمر: {pg_dump} --format=custom --dbname {url.database}\n"
            f"الخطأ: {detail or '(بلا تفاصيل من pg_dump)'}"
        )

    size = target.stat().st_size
    if size == 0:
        target.unlink(missing_ok=True)
        raise SystemExit("pg_dump انتهى بنجاح لكن الملف فارغ — حُذف. راجع إعدادات القاعدة.")

    print(f"تم إنشاء النسخة الاحتياطية: {target}")
    print(f"الحجم: {human_size(size)} ({size} بايت) | الزمن: {elapsed:.1f} ثانية")
    print("للتحقق التالي: python scripts/verify_restore.py")


if __name__ == "__main__":
    main()
