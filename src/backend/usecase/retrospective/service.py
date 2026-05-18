# usecase/retrospective/service.py
# PRG-ID: PRG-09 (회고 관리)
# RQ: RQ-F-09
# Failure Categories:
#   Input — body 길이 제약 (Pydantic)
#   State Transition — 모임 미완료 시 회고 접근 / 한 줄 회고 중복
#   Business Rule — 호스트 권한 / 본인 소유 / 미존재 리소스
#   Concurrency — UNIQUE(retro_id, participant_id) 위반
#   Resource — SQLite I/O
from backend.common.errors import (
    HostRequiredError,
    NotFoundError,
    OneLineReviewDuplicateError,
    OwnerRequiredError,
    RetroNotAccessibleError,
)
from backend.domain.entities import (
    BookmarkAnswer, Insight, NewQuestion, OneLineReview, Retrospective,
)
from backend.usecase.ports import IMeetingRepository, IRetrospectiveRepository


class RetroSvc:
    """PRG-09: 회고 CRUD."""

    def __init__(self, retro_repo: IRetrospectiveRepository, meeting_repo: IMeetingRepository):
        self._retros = retro_repo
        self._meetings = meeting_repo

    def init_retro(self, meeting_id: int) -> Retrospective:
        """MeetingCompleted 이벤트 핸들러 (MeetingSvc.complete_meeting 에서 직접 호출)."""
        existing = self._retros.get_by_meeting(meeting_id)
        if existing:
            return existing
        return self._retros.create(Retrospective(id=None, meeting_id=meeting_id, created_at=""))

    def get_retro(self, meeting_id: int) -> dict:
        meeting = self._meetings.get(meeting_id)
        if meeting is None:
            raise NotFoundError("MEETING")
        # State Transition: 모임 미완료 접근 차단
        if meeting.status != "completed":
            raise RetroNotAccessibleError()
        retro = self._retros.get_full(meeting_id)
        if retro is None:
            raise NotFoundError("RETRO")
        return _retro_to_dict(retro)

    def add_insight(self, meeting_id: int, body: str, created_by: int, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        retro = self._get_retro_or_raise(meeting_id)
        insight = self._retros.add_insight(Insight(
            id=None, retro_id=retro.id, body=body, created_by=created_by, created_at="",
        ))
        return {"id": insight.id, "body": insight.body, "created_by": insight.created_by,
                "created_at": insight.created_at}

    def add_bookmark(self, meeting_id: int, answer_id: int, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        retro = self._get_retro_or_raise(meeting_id)
        bm = self._retros.add_bookmark(BookmarkAnswer(
            id=None, retro_id=retro.id, answer_id=answer_id, created_at="",
        ))
        return {"retro_id": bm.retro_id, "answer_id": bm.answer_id, "created_at": bm.created_at}

    def remove_bookmark(self, meeting_id: int, answer_id: int, is_host: bool) -> None:
        if not is_host:
            raise HostRequiredError()
        retro = self._get_retro_or_raise(meeting_id)
        self._retros.remove_bookmark(retro.id, answer_id)

    def add_new_question(self, meeting_id: int, body: str, created_by: int) -> dict:
        retro = self._get_retro_or_raise(meeting_id)
        nq = self._retros.add_new_question(NewQuestion(
            id=None, retro_id=retro.id, body=body, created_by=created_by, created_at="",
        ))
        return {"id": nq.id, "body": nq.body, "created_by": nq.created_by, "created_at": nq.created_at}

    def submit_one_line_review(self, meeting_id: int, body: str, participant_id: int) -> dict:
        retro = self._get_retro_or_raise(meeting_id)
        # Concurrency: UNIQUE 위반은 Repository.add_one_line_review 에서 처리
        review = self._retros.add_one_line_review(OneLineReview(
            id=None, retro_id=retro.id, participant_id=participant_id,
            body=body, created_at="", updated_at="",
        ))
        return {"id": review.id, "participant_id": review.participant_id,
                "body": review.body, "created_at": review.created_at}

    def update_one_line_review(self, meeting_id: int, review_id: int,
                                body: str, participant_id: int) -> dict:
        retro = self._get_retro_or_raise(meeting_id)
        existing = self._retros.get_one_line_review(retro.id, participant_id)
        if existing is None or existing.id != review_id:
            raise OwnerRequiredError()
        existing.body = body
        updated = self._retros.update_one_line_review(existing)
        return {"id": updated.id, "participant_id": updated.participant_id,
                "body": updated.body, "updated_at": updated.updated_at}

    def _get_retro_or_raise(self, meeting_id: int) -> Retrospective:
        meeting = self._meetings.get(meeting_id)
        if meeting is None:
            raise NotFoundError("MEETING")
        if meeting.status != "completed":
            raise RetroNotAccessibleError()
        retro = self._retros.get_by_meeting(meeting_id)
        if retro is None:
            raise NotFoundError("RETRO")
        return retro


def _retro_to_dict(retro: Retrospective) -> dict:
    return {
        "id": retro.id,
        "meeting_id": retro.meeting_id,
        "insights": [{"id": i.id, "body": i.body, "created_by": i.created_by,
                       "created_at": i.created_at} for i in retro.insights],
        "bookmarked_answers": [{"answer_id": b.answer_id, "created_at": b.created_at}
                                for b in retro.bookmarked_answers],
        "new_questions": [{"id": nq.id, "body": nq.body, "created_by": nq.created_by,
                           "created_at": nq.created_at} for nq in retro.new_questions],
        "one_line_reviews": [{"id": r.id, "participant_id": r.participant_id,
                              "body": r.body, "created_at": r.created_at,
                              "updated_at": r.updated_at}
                             for r in retro.one_line_reviews],
        "created_at": retro.created_at,
    }
