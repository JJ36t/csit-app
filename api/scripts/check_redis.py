# -*- coding: utf-8 -*-
"""فحص مسار Redis الحقيقي لحدّ المحاولات (يتطلب خدمة Redis تعمل).

    $env:REDIS_URL='redis://127.0.0.1:6379/0'; python scripts/check_redis.py

يفحص: الاتصال، INCR، TTL عند أول تسجيل، الحجب عند الحد، التصفير بعد النجاح.
يخرج برمز 1 مع رسالة عربية عند أي فشل — مفيد كفحص نشر قبل الاعتماد.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.services import rate_limit


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    url = os.environ.get("REDIS_URL") or settings.redis_url
    if not url:
        raise SystemExit("عيّن REDIS_URL أولاً، مثال: redis://127.0.0.1:6379/0")

    settings.redis_url = url
    settings.rate_limit_enabled = True
    rate_limit._reset_backend()

    client = rate_limit._get_client()
    if client is None:
        raise SystemExit(f"تعذّر الاتصال بـRedis على {url} — تأكد من تشغيل الخدمة والرابط")

    info = client.info("server")
    print("Redis:", info.get("redis_version"), "|", url)

    key = "check-redis"
    rkey = f"ratelimit:{key}"

    assert rate_limit.guard(key, limit=2) is True, "أول محاولة يجب أن تمر"
    rate_limit.record(key)
    rate_limit.record(key)

    stored = client.get(rkey)
    ttl = client.ttl(rkey)
    assert stored == "2", f"العدّاد في Redis يجب أن يكون 2، وجدنا {stored}"
    assert ttl and ttl > 0, f"المفتاح بلا TTL ({ttl}) — لن يُصفَّر أبداً"
    print("counter:", stored, "| ttl:", ttl, "s")

    assert rate_limit.guard(key, limit=2) is False, "الحد يجب أن يمنع المحاولة الثالثة"
    print("blocked at limit: ok")

    rate_limit.clear(key)
    assert client.get(rkey) is None, "التصفير بعد النجاح لم يحذف المفتاح"
    assert rate_limit.guard(key, limit=2) is True, "بعد التصفير يجب أن تمر المحاولة"
    print("clear: ok")

    print("\nRedis smoke: كل الخطوات نجحت")


if __name__ == "__main__":
    main()
