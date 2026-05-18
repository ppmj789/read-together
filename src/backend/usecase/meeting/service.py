# usecase/meeting/service.py
# PRG-ID: PRG-07 (발언자 선정), PRG-08 (모임 관리), PRG-11 (SSE 상태)
# RQ: RQ-F-07, RQ-F-08, RQ-NFR-PERF
# Failure Categories:
#   Input — card_type 8종 외 / stage 범위
#   State Transition — 모임 완료 후 단계 이동 / 타이머 이중 시작
#   Business Rule — 호스트 권한 / 발언자 선정 데이터 미존재
#   Resource — SQLite I/O
import random
from datetime import datetime, timezone
from typing import Optional

from backend.common.errors import (
    CardTypeInvalidError,
    HostRequiredError,
    MeetingAlreadyCompletedError,
    NotFoundError,
    VoteDataUnavailableError,
)
from backend.domain.entities import Meeting, Participant, SpeakerSelection, Timer
from backend.usecase.ports import (
    IAnswerRepository, IAnswerVoteRepository, IMeetingRepository,
    IParticipantRepository, IPollRepository, ISpeakerRepository,
    ITimerRepository,
)

VALID_CARD_TYPES = {
    "minority", "most_empathy", "opposite", "similar",
    "random", "question_king", "perspective_shift", "reveal",
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class MeetingSvc:
    """PRG-07 + PRG-08 + PRG-11."""

    def __init__(
        self,
        meeting_repo: IMeetingRepository,
        participant_repo: IParticipantRepository,
        timer_repo: ITimerRepository,
        speaker_repo: ISpeakerRepository,
        answer_repo: IAnswerRepository,
        vote_repo: IAnswerVoteRepository,
        poll_repo: IPollRepository,
    ):
        self._meetings = meeting_repo
        self._participants = participant_repo
        self._timers = timer_repo
        self._speakers = speaker_repo
        self._answers = answer_repo
        self._votes = vote_repo
        self._polls = poll_repo

    # ── PRG-08: 모임 생성/조회 ───────────────────────────────────────────────
    def create_meeting(self, book_id: int, topic_id: int, participant_id: int) -> dict:
        # host_id는 첫 참가자 생성 후 업데이트 (auth.join 에서 처리)
        # 여기서는 임시 host_id=0으로 meeting row 생성 후 join에서 갱신
        meeting = self._meetings.create(Meeting(
            id=None, book_id=book_id, topic_id=topic_id,
            code="", host_id=participant_id,
            current_stage=1, status="preparing",
            created_at="",
        ))
        return _meeting_to_dict(meeting)

    def get_meeting(self, meeting_id: int) -> dict:
        meeting = self._meetings.get(meeting_id)
        if meeting is None:
            raise NotFoundError("MEETING")
        return _meeting_to_dict(meeting)

    def get_state(self, meeting_id: int) -> dict:
        """PRG-08 + PRG-11: 모임 실시간 상태 스냅샷."""
        meeting = self._meetings.get(meeting_id)
        if meeting is None:
            raise NotFoundError("MEETING")
        timer = self._timers.get_by_meeting(meeting_id)
        active_polls = self._polls.list_active_polls_state(meeting_id)
        latest_speaker = self._speakers.get_latest(meeting_id)
        return {
            "current_stage": meeting.current_stage,
            "status": meeting.status,
            "active_polls": active_polls,
            "latest_speaker": _speaker_summary(latest_speaker, self._participants) if latest_speaker else None,
            "timer": _timer_to_dict(timer) if timer else None,
        }

    def advance_stage(self, meeting_id: int, stage: int, is_host: bool) -> dict:
        """PATCH /meetings/{id}/stage."""
        if not is_host:
            raise HostRequiredError()
        meeting = self._meetings.get(meeting_id)
        if meeting is None:
            raise NotFoundError("MEETING")
        # State Transition: completed 모임 단계 이동 차단
        if meeting.status == "completed":
            raise MeetingAlreadyCompletedError()
        # Input: stage 범위 1~8
        if not (1 <= stage <= 8):
            from backend.common.errors import InputValidationError
            raise InputValidationError("stage는 1~8 범위여야 합니다.")
        meeting.current_stage = stage
        if meeting.status == "preparing":
            meeting.status = "in_progress"
            meeting.started_at = _now()
        self._meetings.update(meeting)
        return {"meeting_id": meeting_id, "current_stage": stage, "status": meeting.status}

    def complete_meeting(self, meeting_id: int, is_host: bool) -> dict:
        """POST /meetings/{id}/complete → MeetingCompleted → RetroSvc.init_retro() 직접 호출."""
        if not is_host:
            raise HostRequiredError()
        meeting = self._meetings.get(meeting_id)
        if meeting is None:
            raise NotFoundError("MEETING")
        if meeting.status == "completed":
            raise MeetingAlreadyCompletedError()
        meeting.status = "completed"
        meeting.completed_at = _now()
        self._meetings.update(meeting)
        return {"meeting_id": meeting_id, "status": "completed"}

    def list_participants(self, meeting_id: int) -> list[dict]:
        participants = self._participants.list_by_meeting(meeting_id)
        return [_participant_to_dict(p) for p in participants]

    # ── PRG-08: 타이머 ───────────────────────────────────────────────────────
    def set_timer(self, meeting_id: int, duration_sec: int, mode: str, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        timer = self._timers.get_by_meeting(meeting_id)
        if timer is None:
            timer = self._timers.create(Timer(
                id=None, meeting_id=meeting_id, duration_sec=duration_sec,
                remaining_sec=duration_sec, is_running=False, mode=mode,
            ))
        else:
            timer.duration_sec = duration_sec
            timer.remaining_sec = duration_sec
            timer.mode = mode
            timer.is_running = False
            timer = self._timers.update(timer)
        return _timer_to_dict(timer)

    def start_timer(self, meeting_id: int, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        timer = self._timers.get_by_meeting(meeting_id)
        if timer is None:
            raise NotFoundError("TIMER")
        timer.is_running = True
        timer.last_started_at = _now()
        return _timer_to_dict(self._timers.update(timer))

    def stop_timer(self, meeting_id: int, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        timer = self._timers.get_by_meeting(meeting_id)
        if timer is None:
            raise NotFoundError("TIMER")
        timer.is_running = False
        return _timer_to_dict(self._timers.update(timer))

    def reset_timer(self, meeting_id: int, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        timer = self._timers.get_by_meeting(meeting_id)
        if timer is None:
            raise NotFoundError("TIMER")
        timer.is_running = False
        timer.remaining_sec = timer.duration_sec
        return _timer_to_dict(self._timers.update(timer))

    # ── PRG-07: 발언자 선정 ───────────────────────────────────────────────────
    def select_speaker(self, meeting_id: int, card_type: str,
                       question_id: Optional[int], is_host: bool) -> dict:
        # Input: card_type 검증
        if card_type not in VALID_CARD_TYPES:
            raise CardTypeInvalidError()
        if not is_host:
            raise HostRequiredError()
        meeting = self._meetings.get(meeting_id)
        if meeting is None:
            raise NotFoundError("MEETING")

        participants = self._participants.list_by_meeting(meeting_id)
        if not participants:
            raise VoteDataUnavailableError()

        selected = self._run_card_algorithm(card_type, participants, question_id, meeting_id)

        selection = self._speakers.create(SpeakerSelection(
            id=None, meeting_id=meeting_id, card_type=card_type,
            selected_id=selected.id if selected else None,
            question_id=question_id, created_at="",
        ))
        selected_info = None
        if selected:
            selected_info = {"id": selected.id, "nickname": selected.nickname}
        return {"id": selection.id, "meeting_id": meeting_id,
                "card_type": card_type, "selected_participant": selected_info,
                "created_at": selection.created_at}

    def list_speakers(self, meeting_id: int) -> list[dict]:
        selections = self._speakers.list_by_meeting(meeting_id)
        result = []
        for s in selections:
            p = self._participants.get(s.selected_id) if s.selected_id else None
            result.append({
                "id": s.id, "card_type": s.card_type,
                "selected_participant": {"id": p.id, "nickname": p.nickname} if p else None,
                "created_at": s.created_at,
            })
        return result

    # ── 발언자 선정 알고리즘 ──────────────────────────────────────────────────
    def _run_card_algorithm(self, card_type: str, participants: list[Participant],
                            question_id: Optional[int], meeting_id: int) -> Optional[Participant]:
        if card_type == "random":
            return random.choice(participants)

        if card_type == "perspective_shift":
            latest = self._speakers.get_latest(meeting_id)
            candidates = [p for p in participants
                          if latest is None or p.id != latest.selected_id]
            return random.choice(candidates) if candidates else random.choice(participants)

        if card_type in ("minority", "most_empathy", "opposite"):
            # 답변 투표 집계 기반
            answers = []
            if question_id:
                answers = self._answers.list_by_question(question_id)
            if not answers:
                raise VoteDataUnavailableError()

            vote_map: dict[int, dict] = {}  # answer_id → {participant_id, empathy, rebut}
            for a in answers:
                counts = self._votes.count_by_answer(a.id)
                vote_map[a.id] = {
                    "participant_id": a.participant_id,
                    "empathy": counts.get("empathy", 0),
                    "rebut": counts.get("rebut", 0),
                }

            if card_type == "minority":
                # 공감 최소 답변 작성자
                min_entry = min(vote_map.values(), key=lambda x: x["empathy"])
                pid = min_entry["participant_id"]
            elif card_type == "most_empathy":
                max_entry = max(vote_map.values(), key=lambda x: x["empathy"])
                pid = max_entry["participant_id"]
            else:  # opposite
                max_rebut = max(vote_map.values(), key=lambda x: x["rebut"])
                pid = max_rebut["participant_id"]

            return next((p for p in participants if p.id == pid), None)

        if card_type == "question_king":
            if question_id is None:
                raise VoteDataUnavailableError()
            # 해당 질문 답변 작성자 중 랜덤
            answers = self._answers.list_by_question(question_id)
            if not answers:
                raise VoteDataUnavailableError()
            pid = random.choice(answers).participant_id
            return next((p for p in participants if p.id == pid), None)

        if card_type == "reveal":
            # is_revealed 의사 있는 참가자 = is_anonymous=True인 답변 보유자 (MVP: 랜덤)
            return random.choice(participants)

        if card_type == "similar":
            return random.choice(participants)

        return random.choice(participants)


# ── 직렬화 헬퍼 ───────────────────────────────────────────────────────────────

def _meeting_to_dict(m: Meeting) -> dict:
    return {"id": m.id, "code": m.code, "book_id": m.book_id, "topic_id": m.topic_id,
            "host_id": m.host_id, "current_stage": m.current_stage, "status": m.status,
            "created_at": m.created_at, "started_at": m.started_at, "completed_at": m.completed_at}


def _participant_to_dict(p: Participant) -> dict:
    return {"id": p.id, "nickname": p.nickname, "meeting_id": p.meeting_id,
            "is_host": p.is_host, "joined_at": p.joined_at}


def _timer_to_dict(t: Timer) -> dict:
    return {"meeting_id": t.meeting_id, "duration_sec": t.duration_sec,
            "remaining_sec": t.remaining_sec, "is_running": t.is_running,
            "mode": t.mode, "last_started_at": t.last_started_at}


def _speaker_summary(s: SpeakerSelection, participant_repo: IParticipantRepository) -> Optional[dict]:
    if s is None or s.selected_id is None:
        return None
    p = participant_repo.get(s.selected_id)
    return {"participant_id": s.selected_id,
            "nickname": p.nickname if p else "알 수 없음",
            "card_type": s.card_type}
