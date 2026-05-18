# common/responses.py
# 공통 응답 형식 (IF-REST-01 §공통 규약)
from typing import Any


def ok(data: Any) -> dict:
    return {"data": data}


def ok_list(data: list, total: int) -> dict:
    return {"data": data, "meta": {"total": total}}


def error_body(code: str, message: str, details: list = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or []}}
