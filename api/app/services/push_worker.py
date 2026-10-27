# -*- coding: utf-8 -*-
"""المهمة الخلفية التي تُفرّغ طابور إشعارات الدفع.

تعمل داخل عملية الـAPI (asyncio) بلا وسيط خارجي: لا حاجة إلى Celery/Redis
في نشر جامعي صغير. كل دورة تفتح جلسة قاعدة مستقلة وتستدعي `dispatch_pending`
في خيط منفصل (SQLAlchemy متزامن) حتى لا تُحجب حلقة الأحداث.

تشغيل يدوي لمرة واحدة (للاختبار أو من cron):
    python -m app.services.push_worker
"""
from __future__ import annotations

import asyncio
import logging

from app.config import settings
from app.db import SessionLocal
from app.services.fcm import FcmClient, get_sender
from app.services.push import dispatch_pending

log = logging.getLogger("csit.push.worker")


def dispatch_once(sender: FcmClient | None = None) -> dict[str, int]:
    """دورة واحدة — تُستخدم من الاختبارات وسطر الأوامر."""
    client = sender or get_sender()
    if client is None:
        return {"sent": 0, "retried": 0, "failed": 0, "skipped": 0}
    with SessionLocal() as db:
        return dispatch_pending(db, client)


async def run_forever() -> None:
    sender = get_sender()
    if sender is None:
        log.info("push worker: FCM غير مفعّل أو بيانات الحساب ناقصة — لا إرسال")
        return

    interval = max(settings.push_dispatch_interval_seconds, 5)
    log.info("push worker: بدأ بدورة كل %s ثانية", interval)
    while True:
        try:
            await asyncio.to_thread(dispatch_pending_once, sender)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 — المهمة الخلفية لا تسقط الخدمة
            log.exception("push worker: فشل دورة الإرسال")
        await asyncio.sleep(interval)


def dispatch_pending_once(sender: FcmClient) -> dict[str, int]:
    with SessionLocal() as db:
        return dispatch_pending(db, sender)


if __name__ == "__main__":  # pragma: no cover - تشغيل يدوي
    logging.basicConfig(level=logging.INFO)
    print(dispatch_once())
