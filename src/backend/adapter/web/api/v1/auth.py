# adapter/web/api/v1/auth.py
# PRG-ID: PRG-10 (인증·세션 관리)
# RQ: RQ-NFR-SEC, RQ-F-08
# Failure Categories:
#   Input — 닉네임/코드 형식 (Pydantic)
#   State Transition — 모임 완료 후 참가
#   Business Rule — 코드 미존재 / 토큰 위조
#   Concurrency — 닉네임 중복
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from backend.adapter.web.deps import get_auth_svc, get_token_payload
from backend.common.responses import ok
from backend.usecase.auth.service import AuthSvc
from backend.infrastructure.auth import TokenPayload

router = APIRouter(tags=["인증"])


class JoinRequest(BaseModel):
    meeting_code: str = Field(..., min_length=6, pattern=r"^[A-Za-z0-9]+$")
    nickname: str = Field(..., min_length=1, max_length=50)


@router.post("/meetings/join", status_code=status.HTTP_201_CREATED)
def join_meeting(body: JoinRequest, svc: AuthSvc = Depends(get_auth_svc)):
    """POST /api/v1/meetings/join — 공개 엔드포인트 (PRG-10).
    Failure Categories: Input / State Transition / Business Rule / Concurrency
    """
    result = svc.join(body.meeting_code, body.nickname)
    return ok(result)


@router.get("/auth/me")
def get_me(
    payload: TokenPayload = Depends(get_token_payload),
    svc: AuthSvc = Depends(get_auth_svc),
):
    """GET /api/v1/auth/me (PRG-10).
    Failure Category: Business Rule — AUTH_REQUIRED (401)
    """
    return ok(svc.get_me(payload))
