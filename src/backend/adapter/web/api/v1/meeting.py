# adapter/web/api/v1/meeting.py
# PRG-ID: PRG-07 (발언자 선정), PRG-08 (모임 관리), PRG-11 (SSE)
# RQ: RQ-F-07, RQ-F-08, RQ-NFR-PERF
# Failure Categories:
#   Input — card_type 8종 외 / stage 범위 / duration 범위
#   State Transition — 완료 모임 단계 이동 / 타이머
#   Business Rule — 호스트 권한 / 미존재 리소스
#   Resource — SQLite I/O / SSE 스트림 유지
import asyncio
import json
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.adapter.web.deps import (
    get_meeting_svc, get_retro_svc, get_token_payload, is_host_flag,
)
from backend.common.responses import ok, ok_list
from backend.infrastructure.auth import TokenPayload
from backend.usecase.meeting.service import MeetingSvc
from backend.usecase.retrospective.service import RetroSvc

router = APIRouter(tags=["모임"])


# ── 요청 스키마 ───────────────────────────────────────────────────────────────

class MeetingCreate(BaseModel):
    book_id: int
    topic_id: int


class StageUpdate(BaseModel):
    stage: int = Field(..., ge=1, le=8)


class TimerSet(BaseModel):
    duration_sec: int = Field(..., ge=1, le=10800)
    mode: Literal["countdown", "countup"] = "countdown"


class SpeakerRequest(BaseModel):
    card_type: str
    question_id: Optional[int] = None


# ── PRG-08: 모임 생성/조회 ───────────────────────────────────────────────────

@router.post("/meetings", status_code=status.HTTP_201_CREATED)
def create_meeting(
    body: MeetingCreate,
    payload: TokenPayload = Depends(get_token_payload),
    svc: MeetingSvc = Depends(get_meeting_svc),
):
    """POST /api/v1/meetings (PRG-08 #1)."""
    return ok(svc.create_meeting(body.book_id, body.topic_id, payload.participant_id))


@router.get("/meetings/{meeting_id}")
def get_meeting(
    meeting_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: MeetingSvc = Depends(get_meeting_svc),
):
    """GET /api/v1/meetings/{meeting_id} (PRG-08 #2)."""
    return ok(svc.get_meeting(meeting_id))


@router.get("/meetings/{meeting_id}/state")
def get_meeting_state(
    meeting_id: int,
    request: Request,
    payload: TokenPayload = Depends(get_token_payload),
    svc: MeetingSvc = Depends(get_meeting_svc),
):
    """GET /api/v1/meetings/{meeting_id}/state (PRG-08 #3, PRG-11 #1).
    Accept: text/event-stream 시 SSE 분기 (ADR-AA-01).
    Failure Category: Resource — SSE 연결 유지
    """
    accept = request.headers.get("accept", "")
    if "text/event-stream" in accept:
        return _sse_stream(meeting_id, payload, svc)
    return ok(svc.get_state(meeting_id))


def _sse_stream(meeting_id: int, payload: TokenPayload, svc: MeetingSvc) -> StreamingResponse:
    """PRG-11 #2: SSE 이벤트 스트림 (ADR-AA-01 확장 예비)."""
    # Failure Category: Business Rule — 모임 ID 불일치
    if payload.meeting_id != meeting_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail={"code": "RULE_MEETING_ID_MISMATCH",
                                                      "message": "다른 모임 스트림에 접근할 수 없습니다.",
                                                      "details": []})

    async def event_generator():
        import time
        while True:
            try:
                state = svc.get_state(meeting_id)
                data = json.dumps(state, ensure_ascii=False)
                yield f"event: state\ndata: {data}\n\n"
                # heartbeat
                yield f"event: heartbeat\ndata: {{\"ts\": \"{_now_str()}\"}}\n\n"
                await asyncio.sleep(3)
            except Exception:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Meeting-Id": str(meeting_id),
        },
    )


def _now_str() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@router.patch("/meetings/{meeting_id}/stage")
def advance_stage(
    meeting_id: int,
    body: StageUpdate,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: MeetingSvc = Depends(get_meeting_svc),
):
    """PATCH /api/v1/meetings/{meeting_id}/stage (PRG-08 #4). 모임장 전용."""
    return ok(svc.advance_stage(meeting_id, body.stage, host))


@router.post("/meetings/{meeting_id}/complete")
def complete_meeting(
    meeting_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: MeetingSvc = Depends(get_meeting_svc),
    retro_svc: RetroSvc = Depends(get_retro_svc),
):
    """POST /api/v1/meetings/{meeting_id}/complete (PRG-08 #5).
    MeetingCompleted → RetroSvc.init_retro() 직접 호출.
    """
    result = svc.complete_meeting(meeting_id, host)
    # 도메인 이벤트: MeetingCompleted → 회고 자동 생성
    retro_svc.init_retro(meeting_id)
    return ok(result)


@router.get("/meetings/{meeting_id}/participants")
def list_participants(
    meeting_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: MeetingSvc = Depends(get_meeting_svc),
):
    """GET /api/v1/meetings/{meeting_id}/participants (PRG-08 #6)."""
    participants = svc.list_participants(meeting_id)
    return ok_list(participants, len(participants))


# ── PRG-08: 타이머 ───────────────────────────────────────────────────────────

@router.put("/meetings/{meeting_id}/timer")
def set_timer(
    meeting_id: int,
    body: TimerSet,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: MeetingSvc = Depends(get_meeting_svc),
):
    """PUT /api/v1/meetings/{meeting_id}/timer (PRG-08 #7). 모임장 전용."""
    return ok(svc.set_timer(meeting_id, body.duration_sec, body.mode, host))


@router.post("/meetings/{meeting_id}/timer/start")
def start_timer(
    meeting_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: MeetingSvc = Depends(get_meeting_svc),
):
    """POST /api/v1/meetings/{meeting_id}/timer/start (PRG-08 #8)."""
    return ok(svc.start_timer(meeting_id, host))


@router.post("/meetings/{meeting_id}/timer/stop")
def stop_timer(
    meeting_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: MeetingSvc = Depends(get_meeting_svc),
):
    """POST /api/v1/meetings/{meeting_id}/timer/stop (PRG-08 #9)."""
    return ok(svc.stop_timer(meeting_id, host))


@router.post("/meetings/{meeting_id}/timer/reset")
def reset_timer(
    meeting_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: MeetingSvc = Depends(get_meeting_svc),
):
    """POST /api/v1/meetings/{meeting_id}/timer/reset (PRG-08 #10)."""
    return ok(svc.reset_timer(meeting_id, host))


# ── PRG-07: 발언자 선정 ───────────────────────────────────────────────────────

@router.post("/meetings/{meeting_id}/speakers", status_code=status.HTTP_201_CREATED)
def select_speaker(
    meeting_id: int,
    body: SpeakerRequest,
    payload: TokenPayload = Depends(get_token_payload),
    host: bool = Depends(is_host_flag),
    svc: MeetingSvc = Depends(get_meeting_svc),
):
    """POST /api/v1/meetings/{meeting_id}/speakers (PRG-07 #1). 8종 카드 알고리즘.
    Failure Category: Input — CARD_TYPE_INVALID / Business Rule — VOTE_DATA_UNAVAILABLE
    """
    return ok(svc.select_speaker(meeting_id, body.card_type, body.question_id, host))


@router.get("/meetings/{meeting_id}/speakers")
def list_speakers(
    meeting_id: int,
    payload: TokenPayload = Depends(get_token_payload),
    svc: MeetingSvc = Depends(get_meeting_svc),
):
    """GET /api/v1/meetings/{meeting_id}/speakers (PRG-07 #2)."""
    speakers = svc.list_speakers(meeting_id)
    return ok_list(speakers, len(speakers))
