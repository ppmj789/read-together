# usecase/discussion/service.py
# PRG-ID: PRG-03 (질문), PRG-04 (답변), PRG-05 (익명카드), PRG-06 (투표)
# RQ: RQ-F-03, RQ-F-04, RQ-F-05, RQ-F-06
# Failure Categories:
#   Input — 길이 / enum 제약
#   State Transition — is_revealed 비가역 / 투표 마감
#   Business Rule — 호스트 권한 / 본인 소유 / 미존재 리소스
#   Concurrency — UPSERT 경합 (UNIQUE 처리)
#   Resource — SQLite I/O
from datetime import datetime, timezone
from typing import Optional

from backend.common.errors import (
    AnswerAlreadyRevealedError,
    AnswerRevealNotAllowedError,
    HostRequiredError,
    NotFoundError,
    OwnerRequiredError,
    PollClosedError,
)
from backend.domain.entities import (
    Answer, AnswerGroup, AnswerGroupItem, AnswerVote,
    Poll, PollOption, PollVote, Question,
)
from backend.usecase.ports import (
    IAnswerGroupRepository, IAnswerRepository, IAnswerVoteRepository,
    IMeetingRepository, IPollRepository, IQuestionRepository,
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class DiscussionSvc:
    """PRG-03~06: 질문·답변·익명카드·투표 관리."""

    def __init__(
        self,
        question_repo: IQuestionRepository,
        answer_repo: IAnswerRepository,
        vote_repo: IAnswerVoteRepository,
        group_repo: IAnswerGroupRepository,
        poll_repo: IPollRepository,
        meeting_repo: IMeetingRepository,
    ):
        self._questions = question_repo
        self._answers = answer_repo
        self._votes = vote_repo
        self._groups = group_repo
        self._polls = poll_repo
        self._meetings = meeting_repo

    # ── PRG-03: 질문 ─────────────────────────────────────────────────────────
    def list_questions(self, book_id: int) -> list[dict]:
        qs = self._questions.list_by_book(book_id)
        return [_q_to_dict(q) for q in qs]

    def get_question(self, question_id: int) -> dict:
        q = self._questions.get(question_id)
        if q is None or q.is_deleted:
            raise NotFoundError("QUESTION")
        return _q_to_dict(q)

    def create_question(self, book_id: int, body: str, q_type: str,
                        created_by: int, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        q = self._questions.create(Question(
            id=None, book_id=book_id, body=body, q_type=q_type,
            created_by=created_by, created_at="",
        ))
        return _q_to_dict(q)

    def update_question(self, question_id: int, body: str, q_type: str, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        q = self._questions.get(question_id)
        if q is None or q.is_deleted:
            raise NotFoundError("QUESTION")
        q.body = body; q.q_type = q_type
        return _q_to_dict(self._questions.update(q))

    def delete_question(self, question_id: int, is_host: bool) -> None:
        if not is_host:
            raise HostRequiredError()
        q = self._questions.get(question_id)
        if q is None or q.is_deleted:
            raise NotFoundError("QUESTION")
        self._questions.soft_delete(question_id)

    # ── PRG-04: 답변 ─────────────────────────────────────────────────────────
    def submit_answer(self, question_id: int, body: str, is_anonymous: bool,
                      participant_id: int) -> dict:
        q = self._questions.get(question_id)
        if q is None or q.is_deleted:
            raise NotFoundError("QUESTION")
        answer = self._answers.create(Answer(
            id=None, question_id=question_id, participant_id=participant_id,
            body=body, is_anonymous=is_anonymous, is_revealed=False,
            created_at="", updated_at="",
        ))
        return _answer_to_dict(answer, participant_id)

    def update_answer(self, answer_id: int, body: str, participant_id: int) -> dict:
        answer = self._answers.get(answer_id)
        if answer is None:
            raise NotFoundError("ANSWER")
        # Business Rule: 본인 답변만 수정
        if answer.participant_id != participant_id:
            raise OwnerRequiredError()
        answer.body = body
        return _answer_to_dict(self._answers.update(answer), participant_id)

    def get_answer(self, answer_id: int, participant_id: int) -> dict:
        answer = self._answers.get(answer_id)
        if answer is None:
            raise NotFoundError("ANSWER")
        return _answer_to_dict(answer, participant_id)

    def list_answers(self, question_id: int, participant_id: int) -> list[dict]:
        answers = self._answers.list_by_question(question_id)
        result = []
        for a in answers:
            vote_counts = self._votes.count_by_answer(a.id)
            d = _answer_to_dict(a, participant_id)
            d["vote_counts"] = vote_counts
            result.append(d)
        return result

    # ── PRG-05: 익명카드 ──────────────────────────────────────────────────────
    def reveal_answer(self, answer_id: int, participant_id: int) -> dict:
        answer = self._answers.get(answer_id)
        if answer is None:
            raise NotFoundError("ANSWER")
        # Business Rule: 본인 답변만 공개
        if answer.participant_id != participant_id:
            raise AnswerRevealNotAllowedError()
        # State Transition: is_revealed 비가역 (도메인 불변식)
        answer.reveal()
        self._answers.update(answer)
        return {"answer_id": answer.id, "is_revealed": True}

    def vote_answer(self, answer_id: int, vote_type: str, participant_id: int) -> dict:
        answer = self._answers.get(answer_id)
        if answer is None:
            raise NotFoundError("ANSWER")
        vote = self._votes.upsert(AnswerVote(
            id=None, answer_id=answer_id, participant_id=participant_id,
            vote_type=vote_type, created_at="",
        ))
        return {"answer_id": answer_id, "participant_id": participant_id, "vote_type": vote.vote_type}

    def delete_vote(self, answer_id: int, participant_id: int) -> None:
        self._votes.delete(answer_id, participant_id)

    def list_answer_groups(self, meeting_id: int) -> list[dict]:
        groups = self._groups.list_by_meeting(meeting_id)
        result = []
        for g in groups:
            items = self._groups.list_items(g.id)
            result.append({
                "id": g.id, "meeting_id": g.meeting_id, "label": g.label,
                "created_by": g.created_by, "created_at": g.created_at,
                "answer_ids": [i.answer_id for i in items],
            })
        return result

    def create_answer_group(self, meeting_id: int, label: Optional[str],
                            created_by: int, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        group = self._groups.create(AnswerGroup(
            id=None, meeting_id=meeting_id, label=label,
            created_by=created_by, created_at="",
        ))
        return {"id": group.id, "meeting_id": group.meeting_id, "label": group.label,
                "created_by": group.created_by, "answer_ids": []}

    def add_group_item(self, group_id: int, answer_id: int, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        item = self._groups.add_item(AnswerGroupItem(id=None, group_id=group_id, answer_id=answer_id))
        return {"group_id": item.group_id, "answer_id": item.answer_id}

    def remove_group_item(self, group_id: int, answer_id: int, is_host: bool) -> None:
        if not is_host:
            raise HostRequiredError()
        self._groups.remove_item(group_id, answer_id)

    # ── PRG-06: 투표 ─────────────────────────────────────────────────────────
    def create_poll(self, meeting_id: int, question: str, options_raw: list[dict],
                    created_by: int, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        poll = Poll(id=None, meeting_id=meeting_id, question=question,
                    is_closed=False, created_by=created_by, created_at="")
        options = [PollOption(id=None, poll_id=0, label=o["label"],
                              order_num=o["order_num"]) for o in options_raw]
        created = self._polls.create(poll, options)
        return _poll_to_dict(created)

    def list_polls(self, meeting_id: int) -> list[dict]:
        polls = self._polls.list_by_meeting(meeting_id)
        return [_poll_to_dict(p) for p in polls]

    def get_poll(self, poll_id: int) -> dict:
        p = self._polls.get(poll_id)
        if p is None:
            raise NotFoundError("POLL")
        return _poll_to_dict(p)

    def vote_poll(self, poll_id: int, poll_option_id: int, participant_id: int) -> dict:
        poll = self._polls.get(poll_id)
        if poll is None:
            raise NotFoundError("POLL")
        # State Transition: 마감된 투표
        if poll.is_closed:
            raise PollClosedError()
        vote = self._polls.vote(PollVote(
            id=None, poll_option_id=poll_option_id, poll_id=poll_id,
            participant_id=participant_id, created_at="", updated_at="",
        ))
        return {"poll_id": poll_id, "participant_id": participant_id,
                "poll_option_id": vote.poll_option_id}

    def close_poll(self, poll_id: int, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        poll = self._polls.get(poll_id)
        if poll is None:
            raise NotFoundError("POLL")
        if poll.is_closed:
            raise PollClosedError()
        closed = self._polls.close(poll_id, _now())
        return _poll_to_dict(closed)


# ── 직렬화 헬퍼 ───────────────────────────────────────────────────────────────

def _q_to_dict(q: Question) -> dict:
    return {"id": q.id, "book_id": q.book_id, "body": q.body, "q_type": q.q_type,
            "created_by": q.created_by, "created_at": q.created_at, "is_deleted": q.is_deleted}


def _answer_to_dict(a: Answer, requester_id: int) -> dict:
    # 익명 필터링: is_anonymous=True && is_revealed=False 이면 작성자 숨김
    hide_author = a.is_anonymous and not a.is_revealed
    return {
        "id": a.id,
        "question_id": a.question_id,
        "participant_id": a.participant_id if not hide_author else None,
        "body": a.body,
        "is_anonymous": a.is_anonymous,
        "is_revealed": a.is_revealed,
        "created_at": a.created_at,
        "updated_at": a.updated_at,
    }


def _poll_to_dict(p: Poll) -> dict:
    return {
        "id": p.id, "meeting_id": p.meeting_id, "question": p.question,
        "is_closed": p.is_closed, "created_by": p.created_by,
        "created_at": p.created_at, "closed_at": p.closed_at,
        "options": [{"id": o.id, "label": o.label, "order_num": o.order_num,
                     "vote_count": o.vote_count} for o in p.options],
    }
