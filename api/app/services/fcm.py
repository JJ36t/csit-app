# -*- coding: utf-8 -*-
"""مُرسِل إشعارات Firebase Cloud Messaging عبر HTTP v1.

لا نستخدم حزمة firebase-admin (ثقيلة وتجرّ اعتماديات Google كاملة)؛ بل
ننفّذ الخطوتين المطلوبتين مباشرة:

1. توقيع JWT بمفتاح حساب الخدمة (RS256) واستبداله برمز وصول OAuth2 صالح ساعة.
2. إرسال `POST /v1/projects/{project}/messages:send` لكل جهاز.

النتيجة مُصنَّفة إلى: نجاح، خطأ دائم (الرمز لم يعد صالحاً فيُحذف من القاعدة)،
وخطأ مؤقت (شبكة/429/5xx) يُعاد بعده لاحقاً بتراجع أُسّي في `services/push.py`.

كل شيء قابل للحقن (`post=`) كي تُختبر الحالات بلا شبكة ولا مفاتيح حقيقية.
"""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import httpx
import jwt

from app.config import settings

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
# أخطاء تعني أن الرمز نفسه لم يعد صالحاً — يُحذف بدل إعادة المحاولة
_PERMANENT_STATUSES = {"UNREGISTERED", "INVALID_ARGUMENT", "SENDER_ID_MISMATCH"}

PostFn = Callable[[str, dict[str, str], dict[str, Any]], tuple[int, dict[str, Any]]]


@dataclass(slots=True)
class PushResult:
    """نتيجة إرسال لجهاز واحد."""

    ok: bool
    permanent: bool = False
    error: str | None = None


def _http_post(url: str, headers: dict[str, str], payload: dict[str, Any]) -> tuple[int, dict]:
    # نقطة OAuth تقبل form-encoded فقط، بينما FCM v1 يقبل JSON
    is_form = "application/x-www-form-urlencoded" in headers.get("Content-Type", "")
    with httpx.Client(timeout=10.0) as client:
        if is_form:
            response = client.post(url, data=payload)
        else:
            response = client.post(url, headers=headers, json=payload)
    try:
        body = response.json()
    except ValueError:
        body = {"raw": response.text[:200]}
    return response.status_code, body


def _error_status(body: dict[str, Any]) -> str:
    error = body.get("error")
    if isinstance(error, dict):
        return str(error.get("status") or "")
    return ""


class FcmClient:
    """عميل FCM لحساب خدمة واحد — يُنشأ مرة لكل عملية."""

    def __init__(
        self,
        *,
        project_id: str,
        client_email: str,
        private_key: str,
        post: PostFn | None = None,
    ) -> None:
        self.project_id = project_id
        self.client_email = client_email
        self._private_key = private_key.replace("\\n", "\n")
        self._post = post or _http_post
        self._lock = threading.Lock()
        self._access_token: str | None = None
        self._expires_at: float = 0.0

    # ----------------------------- OAuth -----------------------------

    def _fetch_access_token(self) -> tuple[str, float]:
        now = int(time.time())
        assertion = jwt.encode(
            {
                "iss": self.client_email,
                "scope": _FCM_SCOPE,
                "aud": _TOKEN_URL,
                "iat": now,
                "exp": now + 3600,
            },
            self._private_key,
            algorithm="RS256",
        )
        status, body = self._post(
            _TOKEN_URL,
            {"Content-Type": "application/x-www-form-urlencoded"},
            {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
        )
        if status != 200 or not body.get("access_token"):
            raise RuntimeError(f"oauth_failed:{status}:{_error_status(body) or body.get('error')}")
        return str(body["access_token"]), now + int(body.get("expires_in", 3600))

    def access_token(self, *, force: bool = False) -> str:
        with self._lock:
            if not force and self._access_token and time.time() < self._expires_at - 60:
                return self._access_token
            token, expires_at = self._fetch_access_token()
            self._access_token = token
            self._expires_at = float(expires_at)
            return token

    # ----------------------------- الإرسال -----------------------------

    def _payload(self, token: str, title: str, body: str, data: dict | None) -> dict[str, Any]:
        message: dict[str, Any] = {
            "token": token,
            "notification": {"title": title, "body": body},
            "android": {
                "priority": "high",
                "notification": {
                    "channel_id": "csit_general",
                    "sound": "default",
                    # الضغط على الإشعار يفتح التطبيق على صندوق الإشعارات
                    "click_action": "FLUTTER_NOTIFICATION_CLICK",
                },
            },
        }
        if data:
            # FCM v1 يرفض القيم غير النصية في data
            message["data"] = {str(key): str(value) for key, value in data.items()}
        return {"message": message}

    def send(
        self,
        token: str,
        *,
        title: str,
        body: str,
        data: dict | None = None,
    ) -> PushResult:
        url = f"https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send"
        for attempt in (1, 2):
            try:
                access = self.access_token(force=attempt == 2)
            except RuntimeError as exc:  # فشل OAuth — مؤقت
                return PushResult(False, False, str(exc)[:300])

            status, payload = self._post(
                url,
                {"Authorization": f"Bearer {access}", "Content-Type": "application/json"},
                self._payload(token, title, body, data),
            )
            if status == 200:
                return PushResult(True)
            if status == 401 and attempt == 1:
                continue  # رمز وصول منتهٍ — نجدد مرة واحدة
            error_status = _error_status(payload)
            permanent = status == 404 or error_status in _PERMANENT_STATUSES or status == 400
            return PushResult(
                False,
                permanent,
                f"{status}:{error_status or payload.get('raw', '')}"[:300],
            )
        return PushResult(False, False, "unauthorized")


def load_service_account() -> dict[str, str] | None:
    """يقرأ بيانات حساب الخدمة من الإعدادات أو من ملف JSON.

    الأولوية للمتغيرات المباشرة (أنسب لسيرفر لا يُخزَّن فيه الملف)، ثم للملف.
    """
    if settings.fcm_project_id and settings.fcm_client_email and settings.fcm_private_key:
        return {
            "project_id": settings.fcm_project_id,
            "client_email": settings.fcm_client_email,
            "private_key": settings.fcm_private_key,
        }

    path = settings.fcm_credentials_file.strip()
    if not path:
        return None
    file_path = Path(path)
    if not file_path.is_file():
        return None
    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not raw.get("project_id") or not raw.get("client_email") or not raw.get("private_key"):
        return None
    return {
        "project_id": raw["project_id"],
        "client_email": raw["client_email"],
        "private_key": raw["private_key"],
    }


def get_sender(post: PostFn | None = None) -> FcmClient | None:
    """يعيد عميلاً جاهزاً إن كان الإرسال مفعّلاً وبيانات الحساب مكتملة."""
    if not settings.fcm_enabled:
        return None
    account = load_service_account()
    if account is None:
        return None
    return FcmClient(
        project_id=account["project_id"],
        client_email=account["client_email"],
        private_key=account["private_key"],
        post=post,
    )
