# -*- coding: utf-8 -*-
"""تصفير ربط الأجهزة للتطوير المحلي فقط — «كل حساب ارتبط بجهاز آخر».

المشكلة: النظام يسمح بجهاز نشط واحد لكل حساب (القسم 11 من الخطة)؛ أي متصفح/هاتف
جديد له بصمة مختلفة، فيُرفض الدخول بـ`device_change_requires_approval` حتى يُصفَّر الربط.

    python scripts/dev_reset_devices.py            # تصفير الجميع
    python scripts/dev_reset_devices.py S-100      # حساب واحد

⚠️ للتطوير فقط: لا تشغّله على قاعدة الإنتاج.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import Device, RefreshToken, User  # noqa: E402
from app.models.enums import DeviceStatus  # noqa: E402
from app.security import as_utc  # noqa: E402


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not str(Path.cwd()).lower().startswith(str(Path(__file__).resolve().parents[1]).lower()[:12]):
        pass  # لا يهم موقع التشغيل طالما قاعدة البيانات صحيحة

    only = sys.argv[1] if len(sys.argv) > 1 else None
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        query = select(Device).where(Device.status == DeviceStatus.ACTIVE)
        if only:
            user = db.scalar(select(User).where(User.university_id == only))
            if user is None:
                raise SystemExit(f"لا يوجد مستخدم بالرقم: {only}")
            query = query.where(Device.user_id == user.id)

        devices = list(db.scalars(query))
        for device in devices:
            device.status = DeviceStatus.REVOKED
            device.revoked_at = now

        tokens = list(
            db.scalars(select(RefreshToken).where(RefreshToken.revoked_at.is_(None)))
        )
        for token in tokens:
            if only:
                user = db.scalar(select(User).where(User.university_id == only))
                if token.user_id != user.id:
                    continue
            token.revoked_at = now

        db.commit()

    scope = only or "كل الحسابات"
    print(f"تم تصفير الربط: {scope}")
    print(f"  أجهزة أُلغيت: {len(devices)} | جلسات أُنهيت: {len(tokens)}")
    print("  الدخول التالي من أي متصفح/هاتف سيربطه تلقائياً.")


if __name__ == "__main__":
    main()
