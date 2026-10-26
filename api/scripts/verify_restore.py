# -*- coding: utf-8 -*-
"""فحص استرجاع شهري: يسترجع أحدث نسخة احتياطية إلى قاعدة مؤقتة ويقارن الأعداد.

    python scripts/verify_restore.py
    python scripts/verify_restore.py --file backups/csit-20261026-120000.dump
    python scripts/verify_restore.py --keep      # يبقي csit_restore_check للمعاينة

يُنشئ قاعدة csit_restore_check على نفس الخادم، يسترجع إليها بـpg_restore،
يقارن users/attendance_records/grades مع قاعدة المصدر، يطبع alembic current
للنسخة المسترجعة، ثم يحذف القاعدة المؤقتة. أي فرق في الأعداد = خروج بالرمز 1.
قاعدة المصدر لا تُعدَّل إطلاقاً.
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg  # noqa: E402
from sqlalchemy.engine import URL, make_url  # noqa: E402

from app.config import settings  # noqa: E402

API_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BACKUP_DIR = API_DIR / "backups"
TEMP_DB = "csit_restore_check"
TABLES = ("users", "attendance_records", "grades")
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


def find_pg_restore(explicit: str | None) -> Path:
    """يبحث عن pg_restore في --pg-restore ثم PG_RESTORE ثم PATH ثم مجلدات PostgreSQL."""
    candidate = explicit or os.environ.get("PG_RESTORE")
    if candidate:
        path = Path(candidate)
        if path.is_file():
            return path
        raise SystemExit(f"لم أجد pg_restore في المسار المحدَّد: {path}")

    found = shutil.which("pg_restore")
    if found:
        return Path(found)

    for directory in pg_bin_dirs():
        path = directory / "pg_restore.exe"
        if path.is_file():
            return path

    raise SystemExit(
        "لم أجد pg_restore. ثبّت أدوات PostgreSQL أو مرّر مساره صراحةً:\n"
        "    python scripts/verify_restore.py --pg-restore \"C:\\Program Files\\PostgreSQL\\18\\bin\\pg_restore.exe\"\n"
        "أو أضف مجلد bin إلى PATH أو اضبط PG_RESTORE."
    )


def postgres_url(raw: str) -> URL:
    """يتحقق أن العنوان PostgreSQL ويعيده (بلا طباعة كلمة المرور)."""
    try:
        url = make_url(raw)
    except Exception as exc:  # noqa: BLE001 — رسالة عربية بدل تتبّع SQLAlchemy
        raise SystemExit(f"DATABASE_URL غير صالح: {exc}") from exc

    if url.get_backend_name() != "postgresql":
        raise SystemExit(
            f"DATABASE_URL ليس عنوان PostgreSQL (النوع الحالي: {url.get_backend_name()}).\n"
            "الفحص يحتاج قاعدة PostgreSQL مصدراً؛ اضبط مثلاً:\n"
            "    DATABASE_URL=postgresql+psycopg://csit:PASSWORD@localhost:5432/csit"
        )
    if not url.database:
        raise SystemExit("DATABASE_URL لا يحدّد اسم قاعدة البيانات.")
    if url.database == TEMP_DB:
        raise SystemExit(f"قاعدة المصدر لا يمكن أن تكون {TEMP_DB} — إنها قاعدة الفحص المؤقتة.")
    return url


def latest_dump(backup_dir: Path) -> Path:
    if not backup_dir.is_dir():
        raise SystemExit(f"مجلد النسخ الاحتياطية غير موجود: {backup_dir}\nشغّل أولاً: python scripts/backup_db.py")
    files = sorted(backup_dir.glob("*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise SystemExit(f"لا توجد نسخ احتياطية (*.dump) في {backup_dir}\nشغّل أولاً: python scripts/backup_db.py")
    return files[0]


def conn_kwargs(url: URL, dbname: str | None = None) -> dict:
    """وسائط psycopg من عنوان SQLAlchemy (كلمة المرور لا تُطبع)."""
    return {
        "host": url.host or "localhost",
        "port": url.port or 5432,
        "user": url.username,
        "password": url.password,
        "dbname": dbname or url.database,
        "connect_timeout": 10,
    }


def counts(url: URL, dbname: str | None = None) -> dict[str, int]:
    """أعداد الصفوف في الجداول الثلاثة لقاعدة محددة."""
    label = dbname or url.database
    result: dict[str, int] = {}
    try:
        with psycopg.connect(**conn_kwargs(url, dbname), autocommit=True) as conn:
            for table in TABLES:
                result[table] = conn.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
    except psycopg.OperationalError as exc:
        raise SystemExit(
            f"تعذّر الاتصال بقاعدة {label}.\n"
            "تحقق من: تشغيل PostgreSQL، صحة DATABASE_URL، وكلمة المرور في PGPASSWORD أو في العنوان.\n"
            f"الخطأ: {str(exc).strip()}"
        ) from exc
    except psycopg.Error as exc:
        raise SystemExit(f"تعذّر عدّ الصفوف في {label}: {str(exc).strip()}") from exc
    return result


def admin_exec(url: URL, statement: str) -> None:
    """تنفيذ أمر إداري (CREATE/DROP DATABASE) عبر قاعدة postgres — خارج معاملة."""
    try:
        conn = psycopg.connect(**conn_kwargs(url, "postgres"), autocommit=True)
    except psycopg.OperationalError as exc:
        raise SystemExit(
            "تعذّر الاتصال بخادم PostgreSQL (قاعدة postgres) لإدارة قاعدة الفحص.\n"
            "تحقق من: تشغيل PostgreSQL، صحة DATABASE_URL، وكلمة المرور في PGPASSWORD أو في العنوان.\n"
            f"الخطأ: {str(exc).strip()}"
        ) from exc
    try:
        conn.execute(statement)
    except psycopg.Error as exc:
        raise SystemExit(
            f"فشل أمر إداري على قاعدة الفحص: {statement}\n"
            "تحقق من صلاحية المستخدم لإنشاء/حذف قواعد البيانات.\n"
            f"الخطأ: {str(exc).strip()}"
        ) from exc
    finally:
        conn.close()


def alembic_current(url: URL, env: dict) -> str:
    """يطبع alembic current للنسخة المسترجعة (subprocess بعنوان مؤقت)."""
    command = [sys.executable, "-m", "alembic", "-c", "alembic.ini", "current"]
    result = subprocess.run(
        command,
        cwd=API_DIR,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    if result.returncode != 0:
        raise SystemExit(f"فشل «alembic current» على النسخة المسترجعة:\n{output or '(بلا مخرجات)'}")
    return output


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
        description="فحص استرجاع نسخة احتياطية إلى قاعدة مؤقتة ومقارنة الأعداد مع المصدر.",
        epilog=f"القاعدة المؤقتة: {TEMP_DB} (تُحذف في النهاية إلا مع --keep).",
    )
    parser.add_argument("--file", type=Path, help="ملف النسخة (افتراضياً أحدث ملف *.dump)")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR, help="مجلد النسخ (افتراضياً api/backups)")
    parser.add_argument("--database-url", help="عنوان قاعدة المصدر (افتراضياً DATABASE_URL أو api/.env)")
    parser.add_argument("--pg-restore", help="مسار pg_restore إن لم يكن على PATH")
    parser.add_argument("--keep", action="store_true", help=f"الإبقاء على {TEMP_DB} بعد الفحص")
    args = parser.parse_args()

    raw_url = args.database_url or os.environ.get("DATABASE_URL") or settings.database_url
    url = postgres_url(raw_url)
    dump = args.file or latest_dump(args.backup_dir)
    if not dump.is_file():
        raise SystemExit(f"ملف النسخة غير موجود: {dump}")
    pg_restore = find_pg_restore(args.pg_restore)

    created = False
    try:
        print(f"[1/5] النسخة: {dump}")
        print(f"      الحجم: {human_size(dump.stat().st_size)} | التاريخ: {datetime.fromtimestamp(dump.stat().st_mtime):%Y-%m-%d %H:%M:%S}")

        print(f"[2/5] قاعدة المصدر: {url.database} — أعداد مرجعية")
        before = counts(url)
        for table in TABLES:
            print(f"      {table}: {before[table]}")

        print(f"[3/5] إنشاء قاعدة مؤقتة {TEMP_DB}")
        admin_exec(url, f'DROP DATABASE IF EXISTS "{TEMP_DB}" WITH (FORCE)')
        admin_exec(url, f'CREATE DATABASE "{TEMP_DB}"')
        created = True

        restored_url = URL.create(
            drivername="postgresql+psycopg",
            username=url.username,
            password=url.password,
            host=url.host,
            port=url.port,
            database=TEMP_DB,
        )
        env = os.environ.copy()
        env["DATABASE_URL"] = restored_url.render_as_string(hide_password=False)
        if url.password:
            env["PGPASSWORD"] = url.password

        print(f"[4/5] استرجاع بـpg_restore إلى {TEMP_DB}")
        command = [str(pg_restore), "--no-owner", "--no-privileges", "--exit-on-error"]
        kwargs = conn_kwargs(url, TEMP_DB)
        command += ["--host", str(kwargs["host"]), "--port", str(kwargs["port"])]
        if kwargs["user"]:
            command += ["--username", str(kwargs["user"])]
        command += ["--dbname", TEMP_DB, str(dump)]
        result = subprocess.run(command, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise SystemExit(
                "فشل استرجاع النسخة الاحتياطية (pg_restore).\n"
                f"الملف: {dump}\n"
                f"الخطأ: {detail or '(بلا تفاصيل من pg_restore)'}"
            )
        print("      الاسترجاع تمّ بلا أخطاء")

        print("[5/5] مقارنة الأعداد مع المصدر")
        after = counts(url, TEMP_DB)
        mismatches = []
        for table in TABLES:
            mark = "✓" if before[table] == after[table] else "✗"
            print(f"      {mark} {table}: المصدر {before[table]} | المسترجعة {after[table]}")
            if before[table] != after[table]:
                mismatches.append(f"{table}: المصدر {before[table]} ≠ المسترجعة {after[table]}")

        print("      alembic current (المسترجعة):")
        for line in alembic_current(restored_url, env).splitlines():
            print(f"      {line}")

        if mismatches:
            raise SystemExit(
                "فحص الاسترجاع فشل — فرق في أعداد الصفوف:\n  "
                + "\n  ".join(mismatches)
                + "\nقد تكون النسخة قديمة أو ناقصة؛ أعد إنشاءها بـbackup_db.py."
            )

        print("\nفحص الاسترجاع نجح: الأعداد مطابقة والنسخة قابلة للاسترجاع.")
    finally:
        if created:
            if args.keep:
                print(f"أُبقيت القاعدة {TEMP_DB} (--keep). للحذف لاحقاً: DROP DATABASE \"{TEMP_DB}\";")
            else:
                admin_exec(url, f'DROP DATABASE IF EXISTS "{TEMP_DB}" WITH (FORCE)')
                print(f"حُذفت القاعدة المؤقتة {TEMP_DB}")


if __name__ == "__main__":
    main()
