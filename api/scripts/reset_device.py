# -*- coding: utf-8 -*-
"""إعادة ضبط ربط الجهاز لمستخدم (يُستخدم بعد موافقة القسم على تغيير الجهاز).

    python scripts/reset_device.py 20240001
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import Device, RefreshToken, User  # noqa: E402
from app.models.enums import DeviceStatus  # noqa: E402


def main() -> None:
    args = sys.argv[1:]
    if not args:
        raise SystemExit("الاستخدام: python scripts/reset_device.py <الرقم الجامعي>")

    university_id = args[0]
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.university_id == university_id))
        if user is None:
            raise SystemExit(f"لا يوجد مستخدم بالرقم: {university_id}")

        now = datetime.now(timezone.utc)
        devices = list(db.scalars(select(Device).where(Device.user_id == user.id)))
        for device in devices:
            device.status = DeviceStatus.REVOKED
        for token in db.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
            )
        ):
            token.revoked_at = now
        db.commit()

    print(f"reset devices for {university_id}: {len(devices)} device(s) revoked, sessions closed")
    print("next login from the new device will bind it automatically")


if __name__ == "__main__":
    main()
