# -*- coding: utf-8 -*-
"""اختبارات التنظيف الدوري: الطابور، الرموز، ومرفقات الأعذار القديمة."""
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import (
    AbsenceExcuse,
    Device,
    FcmToken,
    PushOutbox,
    RefreshToken,
    StoredFile,
)
from app.models.enums import DeviceStatus, ExcuseStatus
from scripts.cleanup import cleanup
from world import build_world

NOW = datetime.now(timezone.utc)


def _seed(world: dict) -> dict:
    with SessionLocal() as db:
        device = Device(
            user_id=uuid.UUID(world["student"]),
            device_fingerprint="cleanup-device-1",
            status=DeviceStatus.ACTIVE,
        )
        db.add(device)
        db.flush()

        old = NOW - timedelta(days=200)
        db.add(
            PushOutbox(
                user_id=uuid.UUID(world["student"]),
                title="قديم",
                body="b",
                status="sent",
                attempts=1,
                next_attempt_at=old,
                sent_at=old,
                updated_at=old,
            )
        )
        db.add(
            PushOutbox(
                user_id=uuid.UUID(world["student"]),
                title="حديث",
                body="b",
                status="sent",
                attempts=1,
                next_attempt_at=NOW,
                sent_at=NOW,
            )
        )
        db.add(
            FcmToken(
                user_id=uuid.UUID(world["student"]),
                device_id=device.id,
                token="dead-token-1",
                last_seen_at=old,
            )
        )
        db.add(
            FcmToken(
                user_id=uuid.UUID(world["student"]),
                device_id=device.id,
                token="live-token-1",
                last_seen_at=NOW,
            )
        )
        db.add(
            RefreshToken(
                user_id=uuid.UUID(world["student"]),
                device_id=device.id,
                token_hash="old-refresh-hash",
                expires_at=NOW - timedelta(days=1),
                revoked_at=NOW - timedelta(days=60),
            )
        )

        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"cleanup-{uuid.uuid4().hex}.bin"
        (upload_dir / stored_name).write_bytes(b"old excuse")
        file_row = StoredFile(
            storage_key=stored_name,
            original_name="old.pdf",
            mime="application/pdf",
            size=10,
            uploader_id=uuid.UUID(world["student"]),
        )
        db.add(file_row)
        db.flush()

        excuse = AbsenceExcuse(
            student_id=uuid.UUID(world["student"]),
            session_id=uuid.UUID(world["session"]),
            reason="عذر قديم",
            attachment_file_id=file_row.id,
            status=ExcuseStatus.APPROVED,
            reviewed_at=NOW - timedelta(days=400),
        )
        db.add(excuse)
        db.commit()
        return {"file_id": file_row.id, "stored_name": stored_name}


def test_dry_run_reports_without_deleting(client):
    world = build_world()
    _seed(world)
    with SessionLocal() as db:
        stats = cleanup(db, now=NOW, dry_run=True)
        assert stats == {
            "outbox": 1,
            "fcm_tokens": 1,
            "refresh_tokens": 1,
            "excuse_files": 1,
        }
        assert db.scalar(select(PushOutbox).where(PushOutbox.title == "قديم")) is not None


def test_cleanup_deletes_only_stale_rows(client):
    world = build_world()
    seeded = _seed(world)
    with SessionLocal() as db:
        stats = cleanup(db, now=NOW)
        assert stats["outbox"] == 1
        assert stats["fcm_tokens"] == 1
        assert stats["refresh_tokens"] == 1
        assert stats["excuse_files"] == 1

    with SessionLocal() as db:
        titles = {row.title for row in db.scalars(select(PushOutbox))}
        assert titles == {"حديث"}
        tokens = {row.token for row in db.scalars(select(FcmToken))}
        assert tokens == {"live-token-1"}
        assert db.scalar(select(RefreshToken)) is None
        excuse = db.scalar(select(AbsenceExcuse))
        assert excuse.attachment_file_id is None
        assert db.get(StoredFile, seeded["file_id"]) is None

    assert not (Path(settings.upload_dir) / seeded["stored_name"]).exists()
