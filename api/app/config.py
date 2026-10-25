# -*- coding: utf-8 -*-
"""إعدادات الخدمة — تُقرأ من متغيرات البيئة أو ملف ‎.env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CSIT College App API"
    # محلياً SQLite افتراضياً؛ وعلى السيرفر الجامعي:
    # DATABASE_URL=postgresql+psycopg://csit:PASSWORD@localhost:5432/csit
    database_url: str = "sqlite:///./csit_dev.db"
    api_v1_prefix: str = "/api/v1"

    # المصادقة (القسم 9 من الخطة)
    jwt_secret: str = "dev-only-secret-change-me-0123456789abcdef"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    rate_limit_enabled: bool = True
    login_attempts_per_minute: int = 5

    # الحضور (القسم 6 و9 من الخطة)
    qr_rotation_seconds: int = 20
    qr_tolerance_windows: int = 1
    attendance_grace_minutes: int = 10
    attendance_window_before_min: int = 20
    attendance_window_after_min: int = 30
    # نطاق الحرم الجامعي الافتراضي (يُستخدم إن لم يكن للقاعة إحداثيات)
    campus_lat: float | None = None
    campus_lng: float | None = None
    campus_radius_m: int = 150

    # الاستيراد من Excel
    initial_password_mode: str = "university_id"  # university_id | random
    max_import_bytes: int = 5 * 1024 * 1024
    # كلفة bcrypt لكلمات المرور الأولية في الاستيراد الجماعي (تُغيَّر إجبارياً عند أول دخول)
    import_bcrypt_rounds: int = 10

    # المواد والملفات (N3)
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 25 * 1024 * 1024  # 25MB
    file_link_ttl_minutes: int = 10  # عمر رابط التنزيل الموقّع

    # CORS لتطوير الويب المحلي (Flutter web / لوحة التحكم)
    cors_origin_regex: str = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
