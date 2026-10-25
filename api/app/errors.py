# -*- coding: utf-8 -*-
"""أخطاء موحّدة بالشكل {code, message_ar, details} كما في القسم 9 من الخطة."""
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(StarletteHTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message_ar: str,
        details: Any = None,
    ) -> None:
        super().__init__(status_code=status_code)
        self.code = code
        self.message_ar = message_ar
        self.details = details if details is not None else {}


def _payload(code: str, message_ar: str, details: Any = None) -> dict[str, Any]:
    return {"code": code, "message_ar": message_ar, "details": details or {}}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(exc.code, exc.message_ar, exc.details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            return JSONResponse(status_code=exc.status_code, content=detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload("http_error", "حدث خطأ في الطلب", {"detail": str(detail)}),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "loc": ".".join(str(part) for part in err.get("loc", [])),
                "msg": err.get("msg", ""),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_payload("validation_error", "بيانات الطلب غير صحيحة", details),
        )
