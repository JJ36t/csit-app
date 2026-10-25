# -*- coding: utf-8 -*-
"""الاتصال بقاعدة البيانات وجلسات العمل."""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """تبعية FastAPI: جلسة قاعدة بيانات لكل طلب."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
