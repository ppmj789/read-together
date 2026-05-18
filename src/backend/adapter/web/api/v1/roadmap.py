# adapter/web/api/v1/roadmap.py
# PRG-ID: PRG-01 (주제 관리), PRG-02 (책 관리)
# RQ: RQ-F-01, RQ-F-02
# Failure Categories:
#   Input — 길이/필드 제약 (Pydantic)
#   Business Rule — 호스트 권한 / 미존재 리소스
#   State Transition — 답변 존재 책 삭제
#   Resource — SQLite I/O
from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from backend.adapter.web.deps import (
    get_roadmap_svc, get_token_payload, is_host_flag,
)
from backend.common.responses import ok, ok_list
from backend.infrastructure.auth import TokenPayload
from backend.usecase.roadmap.service import RoadmapSvc

router = APIRouter(tags=["로드맵"])


# ── 요청 스키마 ───────────────────────────────────────────────────────────────

class TopicCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class TopicUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class StepCreate(BaseModel):
    order_num: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=100)
    perspective: Optional[str] = Field(None, max_length=300)


class StepUpdate(BaseModel):
    order_num: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=100)
    perspective: Optional[str] = Field(None, max_length=300)


class BookAssign(BaseModel):
    book_id: int


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    reason: str = Field(..., min_length=1, max_length=500)
    role_desc: Optional[str] = Field(None, max_length=300)


class BookUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    reason: str = Field(..., min_length=1, max_length=500)
    role_desc: Optional[str] = Field(None, max_length=300)


# ── Topic 엔드포인트 ──────────────────────────────────────────────────────────

@router.get("/topics")
def list_topics(
    payload: TokenPayload = Depends(get_token_payload),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """GET /api/v1/topics (PRG-01 #1)."""
    topics = svc.list_topics(payload.meeting_id)
    return ok_list(topics, len(topics))


@router.post("/topics", status_code=status.HTTP_201_CREATED)
def create_topic(
    body: TopicCreate,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """POST /api/v1/topics (PRG-01 #2). 모임장 전용."""
    return ok(svc.create_topic(body.title, body.description, payload.participant_id, host))


@router.get("/topics/{topic_id}")
def get_topic(
    topic_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """GET /api/v1/topics/{topic_id} (PRG-01 #3)."""
    return ok(svc.get_topic(topic_id))


@router.put("/topics/{topic_id}")
def update_topic(
    topic_id: int,
    body: TopicUpdate,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """PUT /api/v1/topics/{topic_id} (PRG-01 #4). 모임장 전용."""
    return ok(svc.update_topic(topic_id, body.title, body.description, payload.participant_id, host))


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(
    topic_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """DELETE /api/v1/topics/{topic_id} (PRG-01 #5). 모임장 전용."""
    svc.delete_topic(topic_id, host)


# ── Step 엔드포인트 ───────────────────────────────────────────────────────────

@router.get("/topics/{topic_id}/steps")
def list_steps(
    topic_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """GET /api/v1/topics/{topic_id}/steps (PRG-01 #6)."""
    steps = svc.list_steps(topic_id)
    return ok_list(steps, len(steps))


@router.post("/topics/{topic_id}/steps", status_code=status.HTTP_201_CREATED)
def create_step(
    topic_id: int,
    body: StepCreate,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """POST /api/v1/topics/{topic_id}/steps (PRG-01 #7). 모임장 전용."""
    return ok(svc.create_step(topic_id, body.order_num, body.title, body.perspective, host))


@router.put("/topics/{topic_id}/steps/{step_id}")
def update_step(
    topic_id: int,
    step_id: int,
    body: StepUpdate,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """PUT /api/v1/topics/{topic_id}/steps/{step_id} (PRG-01 #8)."""
    return ok(svc.update_step(topic_id, step_id, body.title, body.perspective, body.order_num, host))


@router.delete("/topics/{topic_id}/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_step(
    topic_id: int,
    step_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """DELETE /api/v1/topics/{topic_id}/steps/{step_id} (PRG-01 #9)."""
    svc.delete_step(topic_id, step_id, host)


@router.post("/topics/{topic_id}/steps/{step_id}/books", status_code=status.HTTP_201_CREATED)
def assign_book(
    topic_id: int,
    step_id: int,
    body: BookAssign,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """POST /api/v1/topics/{topic_id}/steps/{step_id}/books (PRG-01 #10)."""
    return ok(svc.assign_book(topic_id, step_id, body.book_id, host))


@router.delete("/topics/{topic_id}/steps/{step_id}/books/{book_id}",
               status_code=status.HTTP_204_NO_CONTENT)
def remove_book_from_step(
    topic_id: int,
    step_id: int,
    book_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """DELETE /api/v1/topics/{topic_id}/steps/{step_id}/books/{book_id} (PRG-01 #11)."""
    svc.remove_book(topic_id, step_id, book_id, host)


# ── Book 엔드포인트 ───────────────────────────────────────────────────────────

@router.get("/books")
def list_books(
    payload: TokenPayload = Depends(get_token_payload),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """GET /api/v1/books (PRG-02 #1)."""
    books = svc.list_books()
    return ok_list(books, len(books))


@router.post("/books", status_code=status.HTTP_201_CREATED)
def create_book(
    body: BookCreate,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """POST /api/v1/books (PRG-02 #2). 모임장 전용."""
    return ok(svc.create_book(body.title, body.reason, body.role_desc, payload.participant_id, host))


@router.get("/books/{book_id}")
def get_book(
    book_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """GET /api/v1/books/{book_id} (PRG-02 #3)."""
    return ok(svc.get_book(book_id))


@router.put("/books/{book_id}")
def update_book(
    book_id: int,
    body: BookUpdate,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """PUT /api/v1/books/{book_id} (PRG-02 #4)."""
    return ok(svc.update_book(book_id, body.title, body.reason, body.role_desc, host))


@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """DELETE /api/v1/books/{book_id} (PRG-02 #5) — soft-delete.
    Failure Category: State Transition — BOOK_HAS_ANSWERS (409)
    """
    svc.delete_book(book_id, host)


# ── 주제-책 로드맵 (topic_book) ──────────────────────────────────────────────

@router.get("/topics/{topic_id}/books")
def list_topic_books(
    topic_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """GET /api/v1/topics/{topic_id}/books — 주제 내 책 목록."""
    books = svc.list_topic_books(topic_id)
    return ok_list(books, len(books))


@router.get("/topics/{topic_id}/progress")
def get_topic_progress(
    topic_id: int,
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """GET /api/v1/topics/{topic_id}/progress — 주제 진행률 (public)."""
    return ok(svc.get_topic_progress(topic_id))


@router.post("/topics/{topic_id}/books/{book_id}/complete")
def complete_topic_book(
    topic_id: int,
    book_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """POST /api/v1/topics/{topic_id}/books/{book_id}/complete — 책 완료 (host)."""
    return ok(svc.complete_topic_book(topic_id, book_id, host))


class NextBookRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    reason: str = Field(..., min_length=1, max_length=500)
    role_desc: Optional[str] = None
    questions: list[dict] = Field(default_factory=list)


@router.post("/topics/{topic_id}/next-book", status_code=status.HTTP_201_CREATED)
def add_next_book(
    topic_id: int,
    body: NextBookRequest,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: RoadmapSvc = Depends(get_roadmap_svc),
):
    """POST /api/v1/topics/{topic_id}/next-book — 다음 책 등록 (host)."""
    return ok(svc.add_next_book(
        topic_id, body.title, body.reason, body.role_desc,
        body.questions, payload.participant_id, host,
    ))
