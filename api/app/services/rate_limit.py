# -*- coding: utf-8 -*-
"""حدّ معدل قابل لإعادة الاستخدام (دخول، مسح حضور…).

تخزينان: Redis عند ضبط `REDIS_URL` (نافذة ثابتة بعدّاد INCR + EXPIRE)،
وذاكرة محلية (نافذة منزلقة) عند غياب الإعداد أو تعذّر الاتصال بـRedis.
أي عطل في Redis لا يُسقط الطلب: يُسجَّل تحذير واحد ثم يعمل العدّاد في الذاكرة.

الواجهة العامة ثابتة: guard / record / clear.
"""
import logging
import math
import time
from collections import defaultdict, deque

from app.config import settings

logger = logging.getLogger(__name__)

_KEY_PREFIX = "ratelimit:"
_TIMEOUT_S = 1.0

# عدّاد الذاكرة (نسخة خدمة واحدة، أو بديل مؤقت عند تعذّر Redis)
_windows: dict[str, deque[float]] = defaultdict(deque)

# حالة عميل Redis — يُنشأ مرة واحدة لكل رابط
_client = None
_client_url = ""
_redis_down = False
_warned = False


def _rkey(key: str) -> str:
    return f"{_KEY_PREFIX}{key}"


def _prune(key: str, window_s: float) -> deque[float]:
    now = time.monotonic()
    bucket = _windows[key]
    while bucket and now - bucket[0] > window_s:
        bucket.popleft()
    return bucket


def _disable_redis(exc: Exception) -> None:
    """يوقف استخدام Redis لهذه العملية ويحذّر مرة واحدة فقط."""
    global _client, _client_url, _redis_down, _warned
    _client = None
    _client_url = ""
    _redis_down = True
    if not _warned:
        _warned = True
        logger.warning("Redis غير متاح (%s) — الرجوع إلى عدّاد الذاكرة", exc)


def _get_client():
    """يعيد عميل Redis جاهزاً، أو None إن غاب الإعداد أو تعذّر الاتصال."""
    global _client, _client_url
    if _redis_down or not settings.redis_url:
        return None
    if _client is not None and _client_url == settings.redis_url:
        return _client
    try:
        import redis
    except ImportError as exc:  # الحزمة غير مثبّتة على هذه النسخة
        _disable_redis(exc)
        return None
    try:
        client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=_TIMEOUT_S,
            socket_timeout=_TIMEOUT_S,
        )
        client.ping()
    except Exception as exc:  # أي عطل في الإعداد أو الاتصال
        _disable_redis(exc)
        return None
    _client, _client_url = client, settings.redis_url
    return client


def _reset_backend() -> None:
    """للاختبارات: يصفّر عميل Redis وحالة الفشل والعدّادات المحلية."""
    global _client, _client_url, _redis_down, _warned
    _client = None
    _client_url = ""
    _redis_down = False
    _warned = False
    _windows.clear()


def guard(key: str, *, limit: int, window_s: float = 60.0) -> bool:
    """يعيد True إن كان الطلب مسموحاً (دون تسجيله)، وFalse إن تجاوز الحد."""
    if not settings.rate_limit_enabled:
        return True
    client = _get_client()
    if client is None:
        return len(_prune(key, window_s)) < limit
    try:
        rkey = _rkey(key)
        used = int(client.get(rkey) or 0)
        if used >= limit and int(client.ttl(rkey) or -1) < 0:
            # مفتاح بلا TTL (انقطاع بين INCR وEXPIRE): لا نُبقيه محجوباً للأبد
            client.expire(rkey, max(1, math.ceil(window_s)))
    except Exception as exc:  # تعذّر Redis أثناء الطلب
        _disable_redis(exc)
        return len(_prune(key, window_s)) < limit
    return used < limit


def record(key: str, *, window_s: float = 60.0) -> None:
    """يسجّل محاولة واحدة. `window_s` يحدد عمر العدّاد في Redis (افتراضياً دقيقة)."""
    if not settings.rate_limit_enabled:
        return
    client = _get_client()
    if client is None:
        _windows[key].append(time.monotonic())
        return
    try:
        rkey = _rkey(key)
        count = int(client.incr(rkey))
        if count == 1:
            client.expire(rkey, max(1, math.ceil(window_s)))
    except Exception as exc:
        _disable_redis(exc)
        _windows[key].append(time.monotonic())


def clear(key: str) -> None:
    """يصفّر العدّاد بعد نجاح المحاولة (في التخزينين معاً)."""
    _windows.pop(key, None)
    client = _get_client()
    if client is None:
        return
    try:
        client.delete(_rkey(key))
    except Exception as exc:
        _disable_redis(exc)
