# -*- coding: utf-8 -*-
"""طابور إشعارات الدفع: كتابة داخل معاملة الإشعار، وإرسال خلفي مع إعادة محاولة.

لماذا طابور بدل الإرسال الفوري؟
- الإرسال الفوري داخل طلب HTTP يُبطئ النشر ويربط نجاح العملية بشبكة Google.
- فشل الإرسال بعد commit كان سيُفقد الإشعار بلا أثر.
- هنا: الإشعار داخل التطبيق (notifications) مضمون دائماً، والدفع يُعاد تلقائياً.

السياسة: حتى 5 محاولات بتراجع أُسّي (1، 2، 4، 8 دقائق… بحد أقصى ساعة)،
والرمز الذي يرفضه FCM نهائياً (UNREGISTERED) يُحذف من القاعدة فوراً.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import FcmToken, PushOutbox
from app.services.fcm import FcmClient

log = logging.getLogger("csit.push")

BACKOFF_BASE_SECONDS = 60
BACKOFF_MAX_SECONDS = 3600


def _now() -> datetime:
    return datetime.now(timezone.utc)


def enqueue_for_users(
    db: Session,
    user_ids: list[uuid.UUID],
    *,
    title: str,
    body: str,
    data: dict | None = None,
    now: datetime | None = None,
) -> int:
    """يضيف صفاً في الطابور لكل مستخدم يملك جهازاً مسجَّلاً برمز FCM.

    لا يفعل شيئاً إن كان الإرسال معطّلاً في الإعدادات — صندوق الإشعارات
    داخل التطبيق يبقى المصدر المضمون.
    """
    if not settings.fcm_enabled:
        return 0

    unique_ids = list(dict.fromkeys(user_ids))
    if not unique_ids:
        return 0

    with_tokens = set(
        db.scalars(
            select(FcmToken.user_id).where(FcmToken.user_id.in_(unique_ids)).distinct()
        )
    )
    moment = now or _now()
    created = 0
    for user_id in unique_ids:
        if user_id not in with_tokens:
            continue
        db.add(
            PushOutbox(
                user_id=user_id,
                title=title[:300],
                body=body,
                data=data,
                status="pending",
                attempts=0,
                next_attempt_at=moment,
            )
        )
        created += 1
    return created


def _backoff(attempts: int) -> timedelta:
    seconds = min(BACKOFF_BASE_SECONDS * (2 ** max(attempts - 1, 0)), BACKOFF_MAX_SECONDS)
    return timedelta(seconds=seconds)


def dispatch_pending(
    db: Session,
    sender: FcmClient,
    *,
    now: datetime | None = None,
    limit: int | None = None,
    max_attempts: int | None = None,
) -> dict[str, int]:
    """يُفرّغ دفعة من الطابور ويعيد إحصاءها — دالة نقية التبعية (sender محقون)."""
    moment = now or _now()
    batch = limit or settings.push_batch_size
    attempts_cap = max_attempts or settings.push_max_attempts

    rows = list(
        db.scalars(
            select(PushOutbox)
            .where(PushOutbox.status == "pending", PushOutbox.next_attempt_at <= moment)
            .order_by(PushOutbox.next_attempt_at)
            .limit(batch)
        )
    )

    stats = {"sent": 0, "retried": 0, "failed": 0, "skipped": 0}
    for row in rows:
        tokens = list(db.scalars(select(FcmToken).where(FcmToken.user_id == row.user_id)))
        if not tokens:
            row.status = "skipped"
            row.last_error = "no_device_token"
            stats["skipped"] += 1
            continue

        delivered = False
        alive_tokens = 0
        last_error: str | None = None
        for token_row in tokens:
            result = sender.send(
                token_row.token, title=row.title, body=row.body, data=row.data
            )
            if result.ok:
                delivered = True
                break
            last_error = result.error
            if result.permanent:
                # الجهاز أُعيد تثبيت التطبيق أو الرمز أُبطل — لا فائدة من إبقائه
                db.delete(token_row)
            else:
                alive_tokens += 1

        if delivered:
            row.status = "sent"
            row.sent_at = moment
            row.last_error = None
            stats["sent"] += 1
            continue

        row.attempts += 1
        row.last_error = (last_error or "unknown")[:300]
        if alive_tokens == 0 or row.attempts >= attempts_cap:
            row.status = "failed"
            stats["failed"] += 1
        else:
            row.next_attempt_at = moment + _backoff(row.attempts)
            stats["retried"] += 1

    db.commit()
    if any(stats.values()):
        log.info("push dispatch: %s", stats)
    return stats
