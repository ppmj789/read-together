# adapter/web/api/v1/retrospective.py
# PRG-ID: PRG-09 (회고 관리)
# RQ: RQ-F-09
# Failure Categories:
#   Input — body 길이 제약 (Pydantic)
#   State Transition — 모임 미완료 접근 / 한 줄 회고 중복
#   Business Rule — 호스트 권한 / 본인 소유 / 미존재 리소스
#   Concurrency — UNIQUE(retro_id, participant_id)
#   Resource — SQLite I/O
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from backend.adapter.web.deps import get_retro_svc, get_token_payload, is_host_flag
from backend.common.responses import ok
from backend.infrastructure.auth import TokenPayload
from backend.usecase.retrospective.service import RetroSvc

router = APIRouter(tags=["회고"])


class InsightCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


class BookmarkCreate(BaseModel):
    answer_id: int


class NewQuestionCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=500)


class OneLineReviewCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=200)


class OneLineReviewUpdate(BaseModel):
    body: str = Field(..., min_length=1, max_length=200)


@router.get("/meetings/{meeting_id}/retro")
def get_retro(
    meeting_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: RetroSvc = Depends(get_retro_svc),
):
    """GET /api/v1/meetings/{meeting_id}/retro (PRG-09 #1).
    Failure Category: State Transition — RETRO_NOT_ACCESSIBLE (409)
    """
    return ok(svc.get_retro(meeting_id))


@router.post("/meetings/{meeting_id}/retro/insights", status_code=status.HTTP_201_CREATED)
def add_insight(
    meeting_id: int,
    body: InsightCreate,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RetroSvc = Depends(get_retro_svc),
):
    """POST /api/v1/meetings/{meeting_id}/retro/insights (PRG-09 #2). 모임장 전용."""
    return ok(svc.add_insight(meeting_id, body.body, payload.participant_id, host))


@router.post("/meetings/{meeting_id}/retro/bookmarks", status_code=status.HTTP_201_CREATED)
def add_bookmark(
    meeting_id: int,
    body: BookmarkCreate,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RetroSvc = Depends(get_retro_svc),
):
    """POST /api/v1/meetings/{meeting_id}/retro/bookmarks (PRG-09 #3). 모임장 전용."""
    return ok(svc.add_bookmark(meeting_id, body.answer_id, host))


@router.delete("/meetings/{meeting_id}/retro/bookmarks/{answer_id}",
               status_code=status.HTTP_204_NO_CONTENT)
def remove_bookmark(
    meeting_id: int,
    answer_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RetroSvc = Depends(get_retro_svc),
):
    """DELETE /api/v1/meetings/{meeting_id}/retro/bookmarks/{answer_id} (PRG-09 #4)."""
    svc.remove_bookmark(meeting_id, answer_id, host)


@router.post("/meetings/{meeting_id}/retro/new-questions", status_code=status.HTTP_201_CREATED)
def add_new_question(
    meeting_id: int,
    body: NewQuestionCreate,
    payload: TokenPayload = Depends(get_token_payload),
    svc: RetroSvc = Depends(get_retro_svc),
):
    """POST /api/v1/meetings/{meeting_id}/retro/new-questions (PRG-09 #5). 전원 가능."""
    return ok(svc.add_new_question(meeting_id, body.body, payload.participant_id))


@router.post("/meetings/{meeting_id}/retro/one-line-reviews", status_code=status.HTTP_201_CREATED)
def submit_one_line_review(
    meeting_id: int,
    body: OneLineReviewCreate,
    payload: TokenPayload = Depends(get_token_payload),
    svc: RetroSvc = Depends(get_retro_svc),
):
    """POST /api/v1/meetings/{meeting_id}/retro/one-line-reviews (PRG-09 #6).
    1인 1회고.
    Failure Categories: State Transition — ONE_LINE_REVIEW_DUPLICATE / Concurrency — UNIQUE 위반
    """
    return ok(svc.submit_one_line_review(meeting_id, body.body, payload.participant_id))


@router.put("/meetings/{meeting_id}/retro/one-line-reviews/{review_id}")
def update_one_line_review(
    meeting_id: int,
    review_id: int,
    body: OneLineReviewUpdate,
    payload: TokenPayload = Depends(get_token_payload),
    svc: RetroSvc = Depends(get_retro_svc),
):
    """PUT /api/v1/meetings/{meeting_id}/retro/one-line-reviews/{review_id} (PRG-09 #7). 본인 전용."""
    return ok(svc.update_one_line_review(meeting_id, review_id, body.body, payload.participant_id))
