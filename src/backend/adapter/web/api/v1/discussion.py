# adapter/web/api/v1/discussion.py
# PRG-ID: PRG-03 (질문), PRG-04 (답변), PRG-05 (익명카드), PRG-06 (투표)
# RQ: RQ-F-03, RQ-F-04, RQ-F-05, RQ-F-06
# Failure Categories:
#   Input — 길이/enum 제약 (Pydantic)
#   State Transition — is_revealed 비가역 / 투표 마감
#   Business Rule — 호스트/본인 권한 / 미존재 리소스
#   Concurrency — UPSERT 경합
#   Resource — SQLite I/O
from typing import Literal, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from backend.adapter.web.deps import (
    get_discussion_svc, get_token_payload, is_host_flag,
)
from backend.common.responses import ok, ok_list
from backend.infrastructure.auth import TokenPayload
from backend.usecase.discussion.service import DiscussionSvc

router = APIRouter(tags=["토론"])


# ── 요청 스키마 ───────────────────────────────────────────────────────────────

class QuestionCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=500)
    q_type: Literal["understanding", "self_connection", "debate", "application"]


class QuestionUpdate(BaseModel):
    body: str = Field(..., min_length=1, max_length=500)
    q_type: Literal["understanding", "self_connection", "debate", "application"]


class AnswerCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)
    is_anonymous: bool


class AnswerUpdate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


class VoteCreate(BaseModel):
    vote_type: Literal["empathy", "rebut"]


class GroupCreate(BaseModel):
    label: Optional[str] = Field(None, max_length=100)


class GroupItemAdd(BaseModel):
    answer_id: int


class PollOptionInput(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    order_num: int = Field(..., ge=1)


class PollCreate(BaseModel):
    question: str = Field(..., min_length=1, max_length=200)
    options: list[PollOptionInput] = Field(..., min_length=2, max_length=6)


class PollVoteInput(BaseModel):
    poll_option_id: int


# ── PRG-03: 질문 ─────────────────────────────────────────────────────────────

@router.get("/books/{book_id}/questions")
def list_questions(
    book_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """GET /api/v1/books/{book_id}/questions (PRG-03 #1)."""
    qs = svc.list_questions(book_id)
    return ok_list(qs, len(qs))


@router.post("/books/{book_id}/questions", status_code=status.HTTP_201_CREATED)
def create_question(
    book_id: int,
    body: QuestionCreate,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """POST /api/v1/books/{book_id}/questions (PRG-03 #2). 모임장 전용."""
    return ok(svc.create_question(book_id, body.body, body.q_type, payload.participant_id, host))


@router.get("/questions/{question_id}")
def get_question(
    question_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """GET /api/v1/questions/{question_id} (PRG-03 #3)."""
    return ok(svc.get_question(question_id))


@router.put("/questions/{question_id}")
def update_question(
    question_id: int,
    body: QuestionUpdate,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """PUT /api/v1/questions/{question_id} (PRG-03 #4)."""
    return ok(svc.update_question(question_id, body.body, body.q_type, host))


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """DELETE /api/v1/questions/{question_id} (PRG-03 #5)."""
    svc.delete_question(question_id, host)


# ── PRG-04: 답변 ─────────────────────────────────────────────────────────────

@router.post("/questions/{question_id}/answers", status_code=status.HTTP_201_CREATED)
def submit_answer(
    question_id: int,
    body: AnswerCreate,
    payload: TokenPayload = Depends(get_token_payload),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """POST /api/v1/questions/{question_id}/answers (PRG-04 #1). 1인 1답변."""
    return ok(svc.submit_answer(question_id, body.body, body.is_anonymous, payload.participant_id))


@router.put("/answers/{answer_id}")
def update_answer(
    answer_id: int,
    body: AnswerUpdate,
    payload: TokenPayload = Depends(get_token_payload),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """PUT /api/v1/answers/{answer_id} (PRG-04 #2). 본인 전용."""
    return ok(svc.update_answer(answer_id, body.body, payload.participant_id))


@router.get("/questions/{question_id}/answers")
def list_answers(
    question_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """GET /api/v1/questions/{question_id}/answers (PRG-04 #3). 익명 필터링 포함."""
    answers = svc.list_answers(question_id, payload.participant_id)
    return ok_list(answers, len(answers))


@router.get("/answers/{answer_id}")
def get_answer(
    answer_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """GET /api/v1/answers/{answer_id} (PRG-04 #4)."""
    return ok(svc.get_answer(answer_id, payload.participant_id))


# ── PRG-05: 익명카드 ──────────────────────────────────────────────────────────

@router.post("/answers/{answer_id}/reveal")
def reveal_answer(
    answer_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """POST /api/v1/answers/{answer_id}/reveal (PRG-05 #1). 비가역.
    Failure Category: State Transition — ANSWER_ALREADY_REVEALED
    """
    return ok(svc.reveal_answer(answer_id, payload.participant_id))


@router.post("/answers/{answer_id}/vote")
def vote_answer(
    answer_id: int,
    body: VoteCreate,
    payload: TokenPayload = Depends(get_token_payload),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """POST /api/v1/answers/{answer_id}/vote (PRG-05 #2). UPSERT."""
    return ok(svc.vote_answer(answer_id, body.vote_type, payload.participant_id))


@router.delete("/answers/{answer_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
def delete_vote(
    answer_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """DELETE /api/v1/answers/{answer_id}/vote (PRG-05 #3)."""
    svc.delete_vote(answer_id, payload.participant_id)


@router.get("/meetings/{meeting_id}/answer-groups")
def list_answer_groups(
    meeting_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """GET /api/v1/meetings/{meeting_id}/answer-groups (PRG-05 #4)."""
    groups = svc.list_answer_groups(meeting_id)
    return ok_list(groups, len(groups))


@router.post("/meetings/{meeting_id}/answer-groups", status_code=status.HTTP_201_CREATED)
def create_answer_group(
    meeting_id: int,
    body: GroupCreate,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """POST /api/v1/meetings/{meeting_id}/answer-groups (PRG-05 #5)."""
    return ok(svc.create_answer_group(meeting_id, body.label, payload.participant_id, host))


@router.post("/answer-groups/{group_id}/items", status_code=status.HTTP_201_CREATED)
def add_group_item(
    group_id: int,
    body: GroupItemAdd,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """POST /api/v1/answer-groups/{group_id}/items (PRG-05 #6)."""
    return ok(svc.add_group_item(group_id, body.answer_id, host))


@router.delete("/answer-groups/{group_id}/items/{answer_id}",
               status_code=status.HTTP_204_NO_CONTENT)
def remove_group_item(
    group_id: int,
    answer_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """DELETE /api/v1/answer-groups/{group_id}/items/{answer_id} (PRG-05 #7)."""
    svc.remove_group_item(group_id, answer_id, host)


# ── PRG-06: 투표 ─────────────────────────────────────────────────────────────

@router.post("/meetings/{meeting_id}/polls", status_code=status.HTTP_201_CREATED)
def create_poll(
    meeting_id: int,
    body: PollCreate,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """POST /api/v1/meetings/{meeting_id}/polls (PRG-06 #1). 선택지 2~6개."""
    options_raw = [{"label": o.label, "order_num": o.order_num} for o in body.options]
    return ok(svc.create_poll(meeting_id, body.question, options_raw, payload.participant_id, host))


@router.get("/meetings/{meeting_id}/polls")
def list_polls(
    meeting_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """GET /api/v1/meetings/{meeting_id}/polls (PRG-06 #2)."""
    polls = svc.list_polls(meeting_id)
    return ok_list(polls, len(polls))


@router.get("/polls/{poll_id}")
def get_poll(
    poll_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """GET /api/v1/polls/{poll_id} (PRG-06 #3)."""
    return ok(svc.get_poll(poll_id))


@router.post("/polls/{poll_id}/vote")
def vote_poll(
    poll_id: int,
    body: PollVoteInput,
    payload: TokenPayload = Depends(get_token_payload),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """POST /api/v1/polls/{poll_id}/vote (PRG-06 #4). UPSERT.
    Failure Category: State Transition — POLL_CLOSED (409)
    """
    return ok(svc.vote_poll(poll_id, body.poll_option_id, payload.participant_id))


@router.post("/polls/{poll_id}/close")
def close_poll(
    poll_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: DiscussionSvc = Depends(get_discussion_svc),
):
    """POST /api/v1/polls/{poll_id}/close (PRG-06 #5). 비가역."""
    return ok(svc.close_poll(poll_id, host))
