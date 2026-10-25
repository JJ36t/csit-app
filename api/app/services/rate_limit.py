# -*- coding: utf-8 -*-
"""حدّ معدل قابل لإعادة الاستخدام (دخول، مسح حضور…).

نسخة الذاكرة مناسبة لنسخة خدمة واحدة. عند التوسع يُستبدل التخزين بـRedis
دون تغيير الواجهة (نفس الدوال).
"""
import time
from collections import defaultdict, deque

from app.config import settings

_windows: dict[str, deque[float]] = defaultdict(deque)


def _prune(key: str, window_s: float) -> deque[float]:
    now = time.monotonic()
    bucket = _windows[key]
    while bucket and now - bucket[0] > window_s:
        bucket.popleft()
    return bucket


def guard(key: str, *, limit: int, window_s: float = 60.0) -> bool:
    """يعيد True إن كان الطلب مسموحاً (دون تسجيله)، وFalse إن تجاوز الحد."""
    if not settings.rate_limit_enabled:
        return True
    return len(_prune(key, window_s)) < limit


def record(key: str) -> None:
    if settings.rate_limit_enabled:
        _windows[key].append(time.monotonic())


def clear(key: str) -> None:
    _windows.pop(key, None)
