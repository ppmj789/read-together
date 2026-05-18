# adapter/web/deps.py
# FastAPI 의존성 주입 — 포트 바인딩 + 인증 Depends
# PRG-ID: PRG-10 (RBAC), 전체 공통
# Failure Categories:
#   Business Rule — 토큰 없음/위조/만료 → 401
#   Business Rule — 모임 ID 불일치 → 403
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from backend.adapter.persistence.repositories import (
    AnswerGroupRepository, AnswerRepository, AnswerVoteRepository,
    BookRepository, MeetingRepository, ParticipantRepository,
    PollRepository, QuestionRepository, ReadingLetterRepository,
    RetrospectiveRepository, SpeakerRepository, TimerRepository,
    TopicBookRepository, TopicRepository,
)
from backend.infrastructure.auth import TokenPayload, verify_token
from backend.infrastructure.db import get_db
from backend.usecase.auth.service import AuthSvc
from backend.usecase.discussion.service import DiscussionSvc
from backend.usecase.meeting.service import MeetingSvc
from backend.usecase.retrospective.service import RetroSvc
from backend.usecase.roadmap.service import RoadmapSvc
from backend.usecase.letter.service import LetterSvc
from backend.usecase.setup.service import SetupSvc


# ── 서비스 팩토리 ────────────────────────────────────────────────────────────

def get_auth_svc(db: Session = Depends(get_db)) -> AuthSvc:
    return AuthSvc(
        meeting_repo=MeetingRepository(db),
        participant_repo=ParticipantRepository(db),
    )


def get_roadmap_svc(db: Session = Depends(get_db)) -> RoadmapSvc:
    return RoadmapSvc(
        topic_repo=TopicRepository(db),
        book_repo=BookRepository(db),
        topic_book_repo=TopicBookRepository(db),
        question_repo=QuestionRepository(db),
    )


def get_discussion_svc(db: Session = Depends(get_db)) -> DiscussionSvc:
    return DiscussionSvc(
        question_repo=QuestionRepository(db),
        answer_repo=AnswerRepository(db),
        vote_repo=AnswerVoteRepository(db),
        group_repo=AnswerGroupRepository(db),
        poll_repo=PollRepository(db),
        meeting_repo=MeetingRepository(db),
    )


def get_meeting_svc(db: Session = Depends(get_db)) -> MeetingSvc:
    return MeetingSvc(
        meeting_repo=MeetingRepository(db),
        participant_repo=ParticipantRepository(db),
        timer_repo=TimerRepository(db),
        speaker_repo=SpeakerRepository(db),
        answer_repo=AnswerRepository(db),
        vote_repo=AnswerVoteRepository(db),
        poll_repo=PollRepository(db),
    )


def get_setup_svc(db: Session = Depends(get_db)) -> SetupSvc:
    return SetupSvc(
        topic_repo=TopicRepository(db),
        book_repo=BookRepository(db),
        topic_book_repo=TopicBookRepository(db),
        question_repo=QuestionRepository(db),
        meeting_repo=MeetingRepository(db),
        participant_repo=ParticipantRepository(db),
    )


def get_letter_svc(db: Session = Depends(get_db)) -> LetterSvc:
    return LetterSvc(
        letter_repo=ReadingLetterRepository(db),
        topic_book_repo=TopicBookRepository(db),
        topic_repo=TopicRepository(db),
        answer_repo=AnswerRepository(db),
        vote_repo=AnswerVoteRepository(db),
        participant_repo=ParticipantRepository(db),
        meeting_repo=MeetingRepository(db),
    )


def get_retro_svc(db: Session = Depends(get_db)) -> RetroSvc:
    return RetroSvc(
        retro_repo=RetrospectiveRepository(db),
        meeting_repo=MeetingRepository(db),
    )


# ── 인증 Depends ─────────────────────────────────────────────────────────────

def get_token_payload(authorization: Optional[str] = Header(default=None)) -> TokenPayload:
    """Bearer 토큰 추출·검증 → TokenPayload.
    Failure Category: Business Rule — AUTH_REQUIRED (401)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED",
                                                      "message": "인증이 필요합니다.", "details": []})
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED",
                                                      "message": str(e), "details": []})


def require_meeting_membership(
    meeting_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> TokenPayload:
    """토큰의 meeting_id가 경로 파라미터와 일치하는지 검증.
    Failure Category: Business Rule — RULE_MEETING_ID_MISMATCH (403)
    """
    if payload.meeting_id != meeting_id:
        raise HTTPException(status_code=403, detail={"code": "RULE_MEETING_ID_MISMATCH",
                                                      "message": "다른 모임에 접근할 수 없습니다.",
                                                      "details": []})
    return payload


def is_host_flag(
    payload: TokenPayload = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> bool:
    """현재 요청자가 호스트인지 확인."""
    participant_repo = ParticipantRepository(db)
    participant = participant_repo.get(payload.participant_id)
    return participant.is_host if participant else False
