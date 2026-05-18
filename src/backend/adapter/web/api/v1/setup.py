# adapter/web/api/v1/setup.py
# 모임 만들기 원자적 API
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from backend.adapter.web.deps import get_setup_svc
from backend.common.responses import ok
from backend.usecase.setup.service import SetupSvc

router = APIRouter(tags=["모임 만들기"])


class QuestionInput(BaseModel):
    body: str = Field(..., min_length=1, max_length=500)
    q_type: str = Field(default="self_connection")


class TopicInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class BookInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    reason: str = Field(..., min_length=1, max_length=500)
    role_desc: str | None = None


class CreateWithSetupRequest(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=50)
    topic: TopicInput
    book: BookInput
    questions: list[QuestionInput] = Field(..., min_length=1, max_length=10)


@router.post("/meetings/create-with-setup", status_code=status.HTTP_201_CREATED)
def create_with_setup(
    body: CreateWithSetupRequest,
    svc: SetupSvc = Depends(get_setup_svc),
):
    """모임 만들기 — 주제 + 책 + 질문 + 모임 원자적 생성 (public)."""
    result = svc.create_meeting_with_setup(
        nickname=body.nickname,
        topic_title=body.topic.title,
        topic_desc=body.topic.description,
        book_title=body.book.title,
        book_reason=body.book.reason,
        book_role_desc=body.book.role_desc,
        questions=[q.model_dump() for q in body.questions],
    )
    return ok(result)
