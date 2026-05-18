# adapter/web/api/v1/letter.py
# 독서 편지 API
from fastapi import APIRouter, Depends

from backend.adapter.web.deps import get_letter_svc, get_token_payload
from backend.common.responses import ok
from backend.infrastructure.auth import TokenPayload
from backend.usecase.letter.service import LetterSvc

router = APIRouter(tags=["독서 편지"])


@router.post("/topics/{topic_id}/letters/generate")
def generate_letter(
    topic_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: LetterSvc = Depends(get_letter_svc),
):
    """POST /api/v1/topics/{topic_id}/letters/generate — 독서 편지 생성."""
    return ok(svc.generate_letter(topic_id, payload.participant_id))


@router.get("/topics/{topic_id}/letters/me")
def get_my_letter(
    topic_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: LetterSvc = Depends(get_letter_svc),
):
    """GET /api/v1/topics/{topic_id}/letters/me — 내 독서 편지 조회."""
    return ok(svc.get_letter(topic_id, payload.participant_id))
