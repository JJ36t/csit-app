# -*- coding: utf-8 -*-
"""تنظيف دوري لبيانات تشغيلية لا تنمو بلا حد: الطابور، الرموز، والملفات القديمة.

    python scripts/cleanup.py --dry-run
    python scripts/cleanup.py

ما يُحذف (بحدود زمنية قابلة للضبط):
- `push_outbox` المنتهي (sent/failed/skipped) الأقدم من 14 يوماً.
- رموز FCM التي لم تُشاهد منذ 90 يوماً (جهاز مهجور/تطبيق أُزيل).
- رموز التجديد المنتهية أو الملغاة الأقدم من 30 يوماً.
- مرفقات الأعذار التي تمت مراجعتها قبل سنة (الملف وسجلّه، ويبقى نص العذر).

التشغيل المجدول: `deploy/systemd/csit-cleanup.timer` أسبوعياً.
كل تشغيل يُسجَّل في `audit_logs` بالإحصاءات — لا حذف صامت.
"""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    AbsenceExcuse,
    FcmToken,
    PushOutbox,
    RefreshToken,
    StoredFile,
)
from app.services.audit import log_action  # noqa: E402
from app.services.storage import delete_file  # noqa: E402

OUTBOX_DAYS = 14
TOKEN_DAYS = 90
REFRESH_DAYS = 30
EXCUSE_ATTACHMENT_DAYS = 365


def _cutoff(now: datetime, days: int) -> datetime:
    return now - timedelta(days=days)


def cleanup(
    db,
    *,
    now: datetime | None = None,
    dry_run: bool = False,
    outbox_days: int = OUTBOX_DAYS,
    token_days: int = TOKEN_DAYS,
    refresh_days: int = REFRESH_DAYS,
    excuse_days: int = EXCUSE_ATTACHMENT_DAYS,
) -> dict[str, int]:
    """ينفّذ التنظيف ويعيد الإحصاءات — دالة نقية كي تُختبر بلا سطر أوامر."""
    moment = now or datetime.now(timezone.utc)
    stats = {"outbox": 0, "fcm_tokens": 0, "refresh_tokens": 0, "excuse_files": 0}

    outbox_rows = list(
        db.scalars(
            select(PushOutbox).where(
                PushOutbox.status.in_(["sent", "failed", "skipped"]),
                PushOutbox.updated_at < _cutoff(moment, outbox_days),
            )
        )
    )
    stats["outbox"] = len(outbox_rows)

    dead_tokens = list(
        db.scalars(
            select(FcmToken).where(
                (FcmToken.last_seen_at.is_(None))
                | (FcmToken.last_seen_at < _cutoff(moment, token_days))
            )
        )
    )
    stats["fcm_tokens"] = len(dead_tokens)

    old_refresh = list(
        db.scalars(
            select(RefreshToken).where(
                (RefreshToken.expires_at < moment)
                | (
                    RefreshToken.revoked_at.is_not(None)
                    & (RefreshToken.revoked_at < _cutoff(moment, refresh_days))
                )
            )
        )
    )
    stats["refresh_tokens"] = len(old_refresh)

    old_excuses = list(
        db.scalars(
            select(AbsenceExcuse).where(
                AbsenceExcuse.status != "pending",
                AbsenceExcuse.attachment_file_id.is_not(None),
                AbsenceExcuse.reviewed_at.is_not(None),
                AbsenceExcuse.reviewed_at < _cutoff(moment, excuse_days),
            )
        )
    )
    stats["excuse_files"] = len(old_excuses)

    if dry_run:
        return stats

    for row in outbox_rows:
        db.delete(row)
    for token in dead_tokens:
        db.delete(token)
    for token in old_refresh:
        db.delete(token)

    for excuse in old_excuses:
        file_row = db.get(StoredFile, excuse.attachment_file_id)
        if file_row is not None:
            delete_file(file_row.storage_key)
            db.delete(file_row)
        excuse.attachment_file_id = None

    log_action(
        db,
        actor=None,
        action="cleanup_run",
        entity="system",
        entity_id="cleanup",
        after={
            **stats,
            "outbox_days": outbox_days,
            "token_days": token_days,
            "refresh_days": refresh_days,
            "excuse_days": excuse_days,
        },
    )
    db.commit()
    return stats


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="تنظيف البيانات التشغيلية القديمة")
    parser.add_argument("--dry-run", action="store_true", help="عرض الأثر بلا حذف")
    parser.add_argument("--outbox-days", type=int, default=OUTBOX_DAYS)
    parser.add_argument("--token-days", type=int, default=TOKEN_DAYS)
    parser.add_argument("--refresh-days", type=int, default=REFRESH_DAYS)
    parser.add_argument("--excuse-days", type=int, default=EXCUSE_ATTACHMENT_DAYS)
    args = parser.parse_args()

    with SessionLocal() as db:
        stats = cleanup(
            db,
            dry_run=args.dry_run,
            outbox_days=args.outbox_days,
            token_days=args.token_days,
            refresh_days=args.refresh_days,
            excuse_days=args.excuse_days,
        )

    print("معاينة (لم يُحذف شيء):" if args.dry_run else "تم التنظيف:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
