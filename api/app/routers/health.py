# -*- coding: utf-8 -*-
"""نقطة فحص الجهوزية — تراقبها Uptime Kuma بحسب الخطة."""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
