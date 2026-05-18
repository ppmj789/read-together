# usecase/auth/service.py
# PRG-ID: PRG-10 (인증·세션 관리)
# RQ: RQ-NFR-SEC, RQ-F-08
# Failure Categories:
#   Input — 닉네임 형식 오류 / 모임 코드 형식 오류
#   State Transition — 모임 완료 후 참가 시도
#   Business Rule — 모임 코드 미존재 / HMAC 위조
#   Concurrency — 닉네임 중복

from backend.common.errors import (
    MeetingAlreadyCompletedError,
    MeetingCodeInvalidError,
    NotFoundError,
)
from backend.domain.entities import Participant
from backend.infrastructure.auth import create_token, verify_token, TokenPayload
from backend.usecase.ports import IMeetingRepository, IParticipantRepository


class AuthSvc:
    """PRG-10: 닉네임+모임코드 기반 참가 + HMAC 세션 토큰."""

    def __init__(
        self,
        meeting_repo: IMeetingRepository,
        participant_repo: IParticipantRepository,
    ):
        self._meetings = meeting_repo
        self._participants = participant_repo

    # ── Precondition guard chain ──────────────────────────────────────────────
    def join(self, meeting_code: str, nickname: str) -> dict:
        """POST /meetings/join.
        Guard chain:
          1. Input — 코드 6자 이상 영숫자 (router에서 Pydantic 검증)
          2. Business Rule — 모임 코드 미존재
          3. State Transition — 모임 completed 상태
          4. Concurrency — 닉네임 중복 (ParticipantRepository.create 에서 처리)
        """
        # Guard 1: Business Rule — 모임 코드 미존재
        meeting = self._meetings.get_by_code(meeting_code)
        if meeting is None:
            raise MeetingCodeInvalidError()

        # Guard 2: State Transition — 종료된 모임
        if meeting.status == "completed":
            raise MeetingAlreadyCompletedError()

        # 첫 참가자인지 확인 (호스트 여부 결정)
        participant_count = self._participants.count_by_meeting(meeting.id)
        is_host = participant_count == 0

        # Concurrency 위반은 ParticipantRepository.create 에서 NicknameDuplicateError 발생
        participant = self._participants.create(
            Participant(
                id=None,
                nickname=nickname,
                meeting_id=meeting.id,
                is_host=is_host,
                joined_at="",  # repository에서 설정
            )
        )

        # 호스트면 meeting.host_id 업데이트
        if is_host:
            meeting.host_id = participant.id
            self._meetings.update(meeting)

        token = create_token(participant.id, meeting.id)
        return {
            "session_token": token,
            "participant_id": participant.id,
            "meeting_id": meeting.id,
            "is_host": participant.is_host,
            "nickname": participant.nickname,
        }

    def get_me(self, payload: TokenPayload) -> dict:
        """GET /auth/me."""
        participant = self._participants.get(payload.participant_id)
        if participant is None:
            raise NotFoundError("participant")
        return {
            "participant_id": participant.id,
            "meeting_id": participant.meeting_id,
            "nickname": participant.nickname,
            "is_host": participant.is_host,
        }
