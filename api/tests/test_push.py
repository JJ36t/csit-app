# -*- coding: utf-8 -*-
"""اختبارات إشعارات الدفع: الطابور، إعادة المحاولة، حذف الرموز الميتة، وعميل FCM."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import Device, FcmToken, Notification, PushOutbox
from app.models.enums import DeviceStatus
from app.services import push
from app.services.fcm import FcmClient, PushResult
from app.services.notifications import notify_users
from world import build_world


class FakeSender:
    def __init__(self, results: list[PushResult]):
        self.results = list(results)
        self.calls: list[str] = []

    def send(self, token, *, title, body, data=None) -> PushResult:
        self.calls.append(token)
        return self.results.pop(0)


def _bind_token(world: dict, token: str = "tok-1") -> uuid.UUID:
    with SessionLocal() as db:
        device = Device(
            user_id=uuid.UUID(world["student"]),
            device_fingerprint=f"push-{token}",
            status=DeviceStatus.ACTIVE,
        )
        db.add(device)
        db.flush()
        db.add(FcmToken(user_id=device.user_id, device_id=device.id, token=token))
        db.commit()
        return device.id


def _outbox() -> list[PushOutbox]:
    with SessionLocal() as db:
        return list(db.scalars(select(PushOutbox)))


def _aware(value: datetime) -> datetime:
    """SQLite يعيد التواريخ بلا منطقة زمنية — نوحّدها قبل المقارنة."""
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def test_enqueue_only_when_enabled_and_token_exists(client, monkeypatch):
    world = build_world()
    _bind_token(world)

    with SessionLocal() as db:
        assert push.enqueue_for_users(db, [uuid.UUID(world["student"])], title="t", body="b") == 0

    monkeypatch.setattr(settings, "fcm_enabled", True)
    with SessionLocal() as db:
        created = push.enqueue_for_users(
            db, [uuid.UUID(world["student"]), uuid.UUID(world["other"])], title="t", body="b"
        )
        db.commit()
    # الطالب الثاني بلا رمز FCM → لا صف له
    assert created == 1
    rows = _outbox()
    assert len(rows) == 1
    assert rows[0].status == "pending"
    assert rows[0].attempts == 0


def test_notify_users_writes_outbox_in_same_transaction(client, monkeypatch):
    world = build_world()
    _bind_token(world)
    monkeypatch.setattr(settings, "fcm_enabled", True)

    with SessionLocal() as db:
        notify_users(
            db,
            [uuid.UUID(world["student"])],
            type_="announcement",
            title="إعلان",
            body="نص",
            data={"x": 1},
        )
        db.commit()
        assert db.scalar(select(Notification).where(Notification.user_id == uuid.UUID(world["student"])))
        assert db.scalar(select(PushOutbox)) is not None


def test_dispatch_success_keeps_token(client, monkeypatch):
    world = build_world()
    _bind_token(world)
    monkeypatch.setattr(settings, "fcm_enabled", True)

    with SessionLocal() as db:
        push.enqueue_for_users(db, [uuid.UUID(world["student"])], title="عنوان", body="نص")
        db.commit()
        sender = FakeSender([PushResult(True)])
        stats = push.dispatch_pending(db, sender)

    assert stats == {"sent": 1, "retried": 0, "failed": 0, "skipped": 0}
    row = _outbox()[0]
    assert row.status == "sent"
    assert row.sent_at is not None
    with SessionLocal() as db:
        assert db.scalar(select(FcmToken)) is not None


def test_permanent_error_deletes_token_and_fails(client, monkeypatch):
    world = build_world()
    _bind_token(world)
    monkeypatch.setattr(settings, "fcm_enabled", True)

    with SessionLocal() as db:
        push.enqueue_for_users(db, [uuid.UUID(world["student"])], title="t", body="b")
        db.commit()
        sender = FakeSender([PushResult(False, True, "404:UNREGISTERED")])
        stats = push.dispatch_pending(db, sender)

    assert stats["failed"] == 1
    assert _outbox()[0].status == "failed"
    with SessionLocal() as db:
        assert db.scalar(select(FcmToken)) is None


def test_transient_error_retries_with_backoff_then_gives_up(client, monkeypatch):
    world = build_world()
    _bind_token(world)
    monkeypatch.setattr(settings, "fcm_enabled", True)

    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        push.enqueue_for_users(
            db, [uuid.UUID(world["student"])], title="t", body="b", now=now
        )
        db.commit()

        stats = push.dispatch_pending(
            db, FakeSender([PushResult(False, False, "503:UNAVAILABLE")]), now=now, max_attempts=3
        )
        assert stats["retried"] == 1
        row = _outbox()[0]
        assert row.attempts == 1
        assert _aware(row.next_attempt_at) > now

        # قبل موعد المحاولة لا شيء يُرسل
        early = push.dispatch_pending(db, FakeSender([]), now=now)
        assert early["retried"] == early["sent"] == 0

        later = now + timedelta(minutes=5)
        second = push.dispatch_pending(
            db, FakeSender([PushResult(False, False, "503")]), now=later, max_attempts=2
        )
        assert second["failed"] == 1
        assert _outbox()[0].status == "failed"


def test_no_token_marks_skipped(client, monkeypatch):
    world = build_world()
    monkeypatch.setattr(settings, "fcm_enabled", True)

    with SessionLocal() as db:
        # صف يدوي لمستخدم بلا رمز
        db.add(
            PushOutbox(
                user_id=uuid.UUID(world["other"]),
                title="t",
                body="b",
                status="pending",
                attempts=0,
                next_attempt_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        stats = push.dispatch_pending(db, FakeSender([]))

    assert stats["skipped"] == 1
    assert _outbox()[0].status == "skipped"


def _client_with(post):
    client = FcmClient(project_id="p", client_email="e@x", private_key="key", post=post)
    client.access_token = lambda force=False: "access-token"  # type: ignore[method-assign]
    return client


def test_fcm_client_success_payload_shape():
    calls = []

    def post(url, headers, payload):
        calls.append((url, headers, payload))
        return 200, {"name": "projects/p/messages/1"}

    client = _client_with(post)
    result = client.send("tok", title="عنوان", body="نص", data={"a": 1, "b": True})

    assert result.ok
    url, headers, payload = calls[0]
    assert url.endswith("/projects/p/messages:send")
    assert headers["Authorization"] == "Bearer access-token"
    assert payload["message"]["token"] == "tok"
    assert payload["message"]["notification"]["title"] == "عنوان"
    # قيم data نصية دائماً (شرط FCM v1)
    assert payload["message"]["data"] == {"a": "1", "b": "True"}


def test_fcm_client_404_is_permanent_and_401_refreshes():
    responses = [(401, {"error": {"status": "UNAUTHENTICATED"}}), (200, {})]
    calls = []

    def post(url, headers, payload):
        calls.append(url)
        return responses.pop(0)

    client = _client_with(post)
    assert client.send("tok", title="t", body="b").ok
    assert len(calls) == 2

    def post_404(url, headers, payload):
        return 404, {"error": {"status": "UNREGISTERED"}}

    dead = _client_with(post_404).send("tok", title="t", body="b")
    assert dead.ok is False
    assert dead.permanent is True
    assert "UNREGISTERED" in (dead.error or "")
