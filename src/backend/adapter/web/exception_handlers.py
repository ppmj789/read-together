# adapter/web/exception_handlers.py
# 전역 예외 핸들러 — AppError → JSON 응답
from fastapi import Request
from fastapi.responses import JSONResponse

from backend.common.errors import AppError
from backend.common.responses import error_body


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content=error_body(exc.code, exc.message, exc.details),
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_body("INTERNAL_ERROR", "서버 내부 오류가 발생했습니다."),
    )
