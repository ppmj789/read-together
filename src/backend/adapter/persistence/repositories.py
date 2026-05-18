# adapter/persistence/repositories.py
# Repository 구현체 — SQLAlchemy ↔ 도메인 엔티티 변환
# PRG-ID: PRG-01~PRG-11
# Failure Categories: Resource (DB I/O), Concurrency (UNIQUE 위반)
import random
import string
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.adapter.persistence.models import (
    AnswerGroupItemORM, AnswerGroupORM, AnswerORM, AnswerVoteORM,
    BookmarkAnswerORM, BookORM, BookStepORM, InsightORM, MeetingORM,
    NewQuestionORM, OneLineReviewORM, ParticipantORM, PollOptionORM,
    PollORM, PollVoteORM, QuestionORM, ReadingLetterORM,
    RetrospectiveORM, SpeakerSelectionORM, StepORM, TimerORM,
    TopicBookORM, TopicORM,
)
from backend.common.errors import (
    AnswerVoteDuplicateError, NicknameDuplicateError, ResourceError,
)
from backend.domain.entities import (
    Answer, AnswerGroup, AnswerGroupItem, AnswerVote,
    Book, BookStep, BookmarkAnswer, Insight, Meeting,
    NewQuestion, OneLineReview, Participant, Poll, PollOption,
    PollVote, Question, ReadingLetter, Retrospective,
    SpeakerSelection, Step, Timer, Topic, TopicBook,
)
from backend.usecase.ports import (
    IAnswerGroupRepository, IAnswerRepository, IAnswerVoteRepository,
    IBookRepository, IMeetingRepository, IParticipantRepository,
    IPollRepository, IQuestionRepository, IReadingLetterRepository,
    IRetrospectiveRepository, ISpeakerRepository, ITimerRepository,
    ITopicBookRepository, ITopicRepository,
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _gen_code(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ── 변환 헬퍼 ─────────────────────────────────────────────────────────────────

def _topic_to_entity(o: TopicORM) -> Topic:
    return Topic(id=o.id, title=o.title, description=o.description,
                 created_by=o.created_by, created_at=o.created_at,
                 updated_at=o.updated_at, updated_by=o.updated_by)


def _step_to_entity(o: StepORM) -> Step:
    return Step(id=o.id, topic_id=o.topic_id, order_num=o.order_num,
                title=o.title, perspective=o.perspective)


def _book_to_entity(o: BookORM) -> Book:
    return Book(id=o.id, title=o.title, reason=o.reason, role_desc=o.role_desc,
                created_by=o.created_by, created_at=o.created_at,
                updated_at=o.updated_at, is_deleted=bool(o.is_deleted))


def _meeting_to_entity(o: MeetingORM) -> Meeting:
    return Meeting(id=o.id, book_id=o.book_id, topic_id=o.topic_id,
                   code=o.code, host_id=o.host_id,
                   current_stage=o.current_stage, status=o.status,
                   created_at=o.created_at, started_at=o.started_at,
                   completed_at=o.completed_at)


def _participant_to_entity(o: ParticipantORM) -> Participant:
    return Participant(id=o.id, nickname=o.nickname, meeting_id=o.meeting_id,
                       is_host=bool(o.is_host), joined_at=o.joined_at)


def _timer_to_entity(o: TimerORM) -> Timer:
    return Timer(id=o.id, meeting_id=o.meeting_id, duration_sec=o.duration_sec,
                 remaining_sec=o.remaining_sec, is_running=bool(o.is_running),
                 mode=o.mode, last_started_at=o.last_started_at)


def _question_to_entity(o: QuestionORM) -> Question:
    return Question(id=o.id, book_id=o.book_id, body=o.body, q_type=o.q_type,
                    created_by=o.created_by, created_at=o.created_at,
                    is_deleted=bool(o.is_deleted))


def _answer_to_entity(o: AnswerORM) -> Answer:
    return Answer(id=o.id, question_id=o.question_id, participant_id=o.participant_id,
                  body=o.body, is_anonymous=bool(o.is_anonymous),
                  is_revealed=bool(o.is_revealed),
                  created_at=o.created_at, updated_at=o.updated_at)


def _vote_to_entity(o: AnswerVoteORM) -> AnswerVote:
    return AnswerVote(id=o.id, answer_id=o.answer_id, participant_id=o.participant_id,
                      vote_type=o.vote_type, created_at=o.created_at)


def _poll_to_entity(o: PollORM) -> Poll:
    options = [PollOption(id=opt.id, poll_id=opt.poll_id, label=opt.label,
                          order_num=opt.order_num) for opt in (o.options or [])]
    return Poll(id=o.id, meeting_id=o.meeting_id, question=o.question,
                is_closed=bool(o.is_closed), created_by=o.created_by,
                created_at=o.created_at, closed_at=o.closed_at, options=options)


def _speaker_to_entity(o: SpeakerSelectionORM) -> SpeakerSelection:
    return SpeakerSelection(id=o.id, meeting_id=o.meeting_id, card_type=o.card_type,
                            created_at=o.created_at, selected_id=o.selected_id,
                            question_id=o.question_id)


# ── Repository 구현체 ─────────────────────────────────────────────────────────

class TopicRepository(ITopicRepository):
    def __init__(self, session: Session): self._s = session

    def list_all(self, meeting_id: int) -> list[Topic]:
        # meeting_id 파라미터는 컨텍스트용 — topic은 meeting-agnostic (MVP)
        rows = self._s.query(TopicORM).all()
        return [_topic_to_entity(r) for r in rows]

    def get(self, topic_id: int) -> Optional[Topic]:
        o = self._s.get(TopicORM, topic_id)
        return _topic_to_entity(o) if o else None

    def create(self, topic: Topic) -> Topic:
        now = _now()
        o = TopicORM(title=topic.title, description=topic.description,
                     created_by=topic.created_by, created_at=now, updated_at=now)
        self._s.add(o); self._s.flush()
        return _topic_to_entity(o)

    def update(self, topic: Topic) -> Topic:
        o = self._s.get(TopicORM, topic.id)
        o.title = topic.title; o.description = topic.description
        o.updated_by = topic.updated_by
        self._s.flush()
        return _topic_to_entity(o)

    def delete(self, topic_id: int) -> None:
        o = self._s.get(TopicORM, topic_id)
        if o: self._s.delete(o)

    def list_steps(self, topic_id: int) -> list[Step]:
        rows = (self._s.query(StepORM)
                .filter(StepORM.topic_id == topic_id)
                .order_by(StepORM.order_num).all())
        return [_step_to_entity(r) for r in rows]

    def get_step(self, step_id: int) -> Optional[Step]:
        o = self._s.get(StepORM, step_id)
        return _step_to_entity(o) if o else None

    def create_step(self, step: Step) -> Step:
        o = StepORM(topic_id=step.topic_id, order_num=step.order_num,
                    title=step.title, perspective=step.perspective)
        self._s.add(o); self._s.flush()
        return _step_to_entity(o)

    def update_step(self, step: Step) -> Step:
        o = self._s.get(StepORM, step.id)
        o.title = step.title; o.perspective = step.perspective
        o.order_num = step.order_num
        self._s.flush()
        return _step_to_entity(o)

    def delete_step(self, step_id: int) -> None:
        o = self._s.get(StepORM, step_id)
        if o: self._s.delete(o)

    def assign_book_to_step(self, book_step: BookStep) -> BookStep:
        o = BookStepORM(book_id=book_step.book_id, step_id=book_step.step_id)
        self._s.add(o); self._s.flush()
        return BookStep(id=o.id, book_id=o.book_id, step_id=o.step_id)

    def remove_book_from_step(self, book_id: int, step_id: int) -> None:
        o = (self._s.query(BookStepORM)
             .filter(BookStepORM.book_id == book_id, BookStepORM.step_id == step_id)
             .first())
        if o: self._s.delete(o)


class BookRepository(IBookRepository):
    def __init__(self, session: Session): self._s = session

    def list_active(self) -> list[Book]:
        rows = self._s.query(BookORM).filter(BookORM.is_deleted == 0).all()
        return [_book_to_entity(r) for r in rows]

    def get(self, book_id: int) -> Optional[Book]:
        o = self._s.get(BookORM, book_id)
        return _book_to_entity(o) if o else None

    def create(self, book: Book) -> Book:
        now = _now()
        o = BookORM(title=book.title, reason=book.reason, role_desc=book.role_desc,
                    created_by=book.created_by, created_at=now, updated_at=now)
        self._s.add(o); self._s.flush()
        return _book_to_entity(o)

    def update(self, book: Book) -> Book:
        o = self._s.get(BookORM, book.id)
        o.title = book.title; o.reason = book.reason; o.role_desc = book.role_desc
        self._s.flush()
        return _book_to_entity(o)

    def soft_delete(self, book_id: int) -> None:
        o = self._s.get(BookORM, book_id)
        if o: o.is_deleted = 1; self._s.flush()

    def has_answers(self, book_id: int) -> bool:
        cnt = (self._s.query(func.count(AnswerORM.id))
               .join(QuestionORM, AnswerORM.question_id == QuestionORM.id)
               .filter(QuestionORM.book_id == book_id).scalar())
        return cnt > 0


class QuestionRepository(IQuestionRepository):
    def __init__(self, session: Session): self._s = session

    def list_by_book(self, book_id: int) -> list[Question]:
        rows = (self._s.query(QuestionORM)
                .filter(QuestionORM.book_id == book_id, QuestionORM.is_deleted == 0).all())
        return [_question_to_entity(r) for r in rows]

    def get(self, question_id: int) -> Optional[Question]:
        o = self._s.get(QuestionORM, question_id)
        return _question_to_entity(o) if o else None

    def create(self, question: Question) -> Question:
        now = _now()
        o = QuestionORM(book_id=question.book_id, body=question.body,
                        q_type=question.q_type, created_by=question.created_by,
                        created_at=now, is_deleted=0)
        self._s.add(o); self._s.flush()
        return _question_to_entity(o)

    def update(self, question: Question) -> Question:
        o = self._s.get(QuestionORM, question.id)
        o.body = question.body; o.q_type = question.q_type
        self._s.flush()
        return _question_to_entity(o)

    def soft_delete(self, question_id: int) -> None:
        o = self._s.get(QuestionORM, question_id)
        if o: o.is_deleted = 1; self._s.flush()


class AnswerRepository(IAnswerRepository):
    def __init__(self, session: Session): self._s = session

    def get(self, answer_id: int) -> Optional[Answer]:
        o = self._s.get(AnswerORM, answer_id)
        return _answer_to_entity(o) if o else None

    def get_by_question_participant(self, question_id: int, participant_id: int) -> Optional[Answer]:
        o = (self._s.query(AnswerORM)
             .filter(AnswerORM.question_id == question_id,
                     AnswerORM.participant_id == participant_id).first())
        return _answer_to_entity(o) if o else None

    def list_by_question(self, question_id: int) -> list[Answer]:
        rows = self._s.query(AnswerORM).filter(AnswerORM.question_id == question_id).all()
        return [_answer_to_entity(r) for r in rows]

    def create(self, answer: Answer) -> Answer:
        now = _now()
        o = AnswerORM(question_id=answer.question_id, participant_id=answer.participant_id,
                      body=answer.body, is_anonymous=int(answer.is_anonymous),
                      is_revealed=0, created_at=now, updated_at=now)
        self._s.add(o); self._s.flush()
        return _answer_to_entity(o)

    def update(self, answer: Answer) -> Answer:
        o = self._s.get(AnswerORM, answer.id)
        o.body = answer.body
        o.is_anonymous = int(answer.is_anonymous)
        o.is_revealed = int(answer.is_revealed)
        self._s.flush()
        return _answer_to_entity(o)

    def count_by_book(self, book_id: int) -> int:
        return (self._s.query(func.count(AnswerORM.id))
                .join(QuestionORM, AnswerORM.question_id == QuestionORM.id)
                .filter(QuestionORM.book_id == book_id).scalar())


class AnswerVoteRepository(IAnswerVoteRepository):
    def __init__(self, session: Session): self._s = session

    def get(self, answer_id: int, participant_id: int) -> Optional[AnswerVote]:
        o = (self._s.query(AnswerVoteORM)
             .filter(AnswerVoteORM.answer_id == answer_id,
                     AnswerVoteORM.participant_id == participant_id).first())
        return _vote_to_entity(o) if o else None

    def upsert(self, vote: AnswerVote) -> AnswerVote:
        now = _now()
        existing = self.get(vote.answer_id, vote.participant_id)
        if existing:
            o = self._s.get(AnswerVoteORM, existing.id)
            o.vote_type = vote.vote_type
        else:
            o = AnswerVoteORM(answer_id=vote.answer_id, participant_id=vote.participant_id,
                              vote_type=vote.vote_type, created_at=now)
            self._s.add(o)
        self._s.flush()
        return _vote_to_entity(o)

    def delete(self, answer_id: int, participant_id: int) -> None:
        o = (self._s.query(AnswerVoteORM)
             .filter(AnswerVoteORM.answer_id == answer_id,
                     AnswerVoteORM.participant_id == participant_id).first())
        if o: self._s.delete(o)

    def count_by_answer(self, answer_id: int) -> dict[str, int]:
        rows = (self._s.query(AnswerVoteORM.vote_type, func.count(AnswerVoteORM.id))
                .filter(AnswerVoteORM.answer_id == answer_id)
                .group_by(AnswerVoteORM.vote_type).all())
        result = {"empathy": 0, "rebut": 0}
        for vtype, cnt in rows:
            result[vtype] = cnt
        return result


class AnswerGroupRepository(IAnswerGroupRepository):
    def __init__(self, session: Session): self._s = session

    def list_by_meeting(self, meeting_id: int) -> list[AnswerGroup]:
        rows = self._s.query(AnswerGroupORM).filter(AnswerGroupORM.meeting_id == meeting_id).all()
        return [AnswerGroup(id=r.id, meeting_id=r.meeting_id, label=r.label,
                            created_by=r.created_by, created_at=r.created_at) for r in rows]

    def create(self, group: AnswerGroup) -> AnswerGroup:
        now = _now()
        o = AnswerGroupORM(meeting_id=group.meeting_id, label=group.label,
                           created_by=group.created_by, created_at=now)
        self._s.add(o); self._s.flush()
        return AnswerGroup(id=o.id, meeting_id=o.meeting_id, label=o.label,
                           created_by=o.created_by, created_at=o.created_at)

    def add_item(self, item: AnswerGroupItem) -> AnswerGroupItem:
        o = AnswerGroupItemORM(group_id=item.group_id, answer_id=item.answer_id)
        self._s.add(o); self._s.flush()
        return AnswerGroupItem(id=o.id, group_id=o.group_id, answer_id=o.answer_id)

    def remove_item(self, group_id: int, answer_id: int) -> None:
        o = (self._s.query(AnswerGroupItemORM)
             .filter(AnswerGroupItemORM.group_id == group_id,
                     AnswerGroupItemORM.answer_id == answer_id).first())
        if o: self._s.delete(o)

    def list_items(self, group_id: int) -> list[AnswerGroupItem]:
        rows = self._s.query(AnswerGroupItemORM).filter(AnswerGroupItemORM.group_id == group_id).all()
        return [AnswerGroupItem(id=r.id, group_id=r.group_id, answer_id=r.answer_id) for r in rows]


class MeetingRepository(IMeetingRepository):
    def __init__(self, session: Session): self._s = session

    def get(self, meeting_id: int) -> Optional[Meeting]:
        o = self._s.get(MeetingORM, meeting_id)
        return _meeting_to_entity(o) if o else None

    def get_by_code(self, code: str) -> Optional[Meeting]:
        o = self._s.query(MeetingORM).filter(MeetingORM.code == code).first()
        return _meeting_to_entity(o) if o else None

    def create(self, meeting: Meeting) -> Meeting:
        now = _now()
        code = _gen_code()
        o = MeetingORM(book_id=meeting.book_id, topic_id=meeting.topic_id,
                       code=code, host_id=meeting.host_id,
                       current_stage=1, status="preparing", created_at=now)
        self._s.add(o); self._s.flush()
        return _meeting_to_entity(o)

    def update(self, meeting: Meeting) -> Meeting:
        o = self._s.get(MeetingORM, meeting.id)
        o.current_stage = meeting.current_stage
        o.status = meeting.status
        o.started_at = meeting.started_at
        o.completed_at = meeting.completed_at
        o.host_id = meeting.host_id
        self._s.flush()
        return _meeting_to_entity(o)


class ParticipantRepository(IParticipantRepository):
    def __init__(self, session: Session): self._s = session

    def get(self, participant_id: int) -> Optional[Participant]:
        o = self._s.get(ParticipantORM, participant_id)
        return _participant_to_entity(o) if o else None

    def get_by_meeting_nickname(self, meeting_id: int, nickname: str) -> Optional[Participant]:
        o = (self._s.query(ParticipantORM)
             .filter(ParticipantORM.meeting_id == meeting_id,
                     ParticipantORM.nickname == nickname).first())
        return _participant_to_entity(o) if o else None

    def list_by_meeting(self, meeting_id: int) -> list[Participant]:
        rows = self._s.query(ParticipantORM).filter(ParticipantORM.meeting_id == meeting_id).all()
        return [_participant_to_entity(r) for r in rows]

    def create(self, participant: Participant) -> Participant:
        now = _now()
        try:
            o = ParticipantORM(nickname=participant.nickname, meeting_id=participant.meeting_id,
                               is_host=int(participant.is_host), joined_at=now)
            self._s.add(o); self._s.flush()
            return _participant_to_entity(o)
        except IntegrityError:
            self._s.rollback()
            raise NicknameDuplicateError()

    def count_by_meeting(self, meeting_id: int) -> int:
        return (self._s.query(func.count(ParticipantORM.id))
                .filter(ParticipantORM.meeting_id == meeting_id).scalar())


class TimerRepository(ITimerRepository):
    def __init__(self, session: Session): self._s = session

    def get_by_meeting(self, meeting_id: int) -> Optional[Timer]:
        o = self._s.query(TimerORM).filter(TimerORM.meeting_id == meeting_id).first()
        return _timer_to_entity(o) if o else None

    def create(self, timer: Timer) -> Timer:
        o = TimerORM(meeting_id=timer.meeting_id, duration_sec=timer.duration_sec,
                     remaining_sec=timer.remaining_sec, is_running=0, mode=timer.mode)
        self._s.add(o); self._s.flush()
        return _timer_to_entity(o)

    def update(self, timer: Timer) -> Timer:
        o = self._s.query(TimerORM).filter(TimerORM.meeting_id == timer.meeting_id).first()
        o.duration_sec = timer.duration_sec
        o.remaining_sec = timer.remaining_sec
        o.is_running = int(timer.is_running)
        o.mode = timer.mode
        o.last_started_at = timer.last_started_at
        self._s.flush()
        return _timer_to_entity(o)


class PollRepository(IPollRepository):
    def __init__(self, session: Session): self._s = session

    def get(self, poll_id: int) -> Optional[Poll]:
        o = self._s.get(PollORM, poll_id)
        return _poll_to_entity(o) if o else None

    def list_by_meeting(self, meeting_id: int) -> list[Poll]:
        rows = self._s.query(PollORM).filter(PollORM.meeting_id == meeting_id).all()
        return [_poll_to_entity(r) for r in rows]

    def create(self, poll: Poll, options: list[PollOption]) -> Poll:
        now = _now()
        o = PollORM(meeting_id=poll.meeting_id, question=poll.question,
                    is_closed=0, created_by=poll.created_by, created_at=now)
        self._s.add(o); self._s.flush()
        for opt in options:
            oo = PollOptionORM(poll_id=o.id, label=opt.label, order_num=opt.order_num)
            self._s.add(oo)
        self._s.flush()
        self._s.refresh(o)
        return _poll_to_entity(o)

    def close(self, poll_id: int, closed_at: str) -> Poll:
        o = self._s.get(PollORM, poll_id)
        o.is_closed = 1; o.closed_at = closed_at
        self._s.flush()
        return _poll_to_entity(o)

    def vote(self, vote: PollVote) -> PollVote:
        now = _now()
        existing = self.get_vote(vote.poll_id, vote.participant_id)
        if existing:
            o = self._s.get(PollVoteORM, existing.id)
            o.poll_option_id = vote.poll_option_id; o.updated_at = now
        else:
            o = PollVoteORM(poll_option_id=vote.poll_option_id, poll_id=vote.poll_id,
                            participant_id=vote.participant_id, created_at=now, updated_at=now)
            self._s.add(o)
        self._s.flush()
        return PollVote(id=o.id, poll_option_id=o.poll_option_id, poll_id=o.poll_id,
                        participant_id=o.participant_id, created_at=o.created_at, updated_at=o.updated_at)

    def get_vote(self, poll_id: int, participant_id: int) -> Optional[PollVote]:
        o = (self._s.query(PollVoteORM)
             .filter(PollVoteORM.poll_id == poll_id,
                     PollVoteORM.participant_id == participant_id).first())
        if not o: return None
        return PollVote(id=o.id, poll_option_id=o.poll_option_id, poll_id=o.poll_id,
                        participant_id=o.participant_id, created_at=o.created_at, updated_at=o.updated_at)

    def list_active_polls_state(self, meeting_id: int) -> list[dict]:
        polls = self._s.query(PollORM).filter(PollORM.meeting_id == meeting_id,
                                               PollORM.is_closed == 0).all()
        result = []
        for p in polls:
            vote_counts = {}
            for opt in p.options:
                cnt = (self._s.query(func.count(PollVoteORM.id))
                       .filter(PollVoteORM.poll_option_id == opt.id).scalar())
                vote_counts[str(opt.id)] = cnt
            result.append({"poll_id": p.id, "question": p.question,
                           "vote_counts": vote_counts, "is_closed": False})
        return result


class SpeakerRepository(ISpeakerRepository):
    def __init__(self, session: Session): self._s = session

    def list_by_meeting(self, meeting_id: int) -> list[SpeakerSelection]:
        rows = (self._s.query(SpeakerSelectionORM)
                .filter(SpeakerSelectionORM.meeting_id == meeting_id)
                .order_by(SpeakerSelectionORM.created_at.desc()).all())
        return [_speaker_to_entity(r) for r in rows]

    def create(self, selection: SpeakerSelection) -> SpeakerSelection:
        now = _now()
        o = SpeakerSelectionORM(meeting_id=selection.meeting_id, card_type=selection.card_type,
                                selected_id=selection.selected_id,
                                question_id=selection.question_id, created_at=now)
        self._s.add(o); self._s.flush()
        return _speaker_to_entity(o)

    def get_latest(self, meeting_id: int) -> Optional[SpeakerSelection]:
        o = (self._s.query(SpeakerSelectionORM)
             .filter(SpeakerSelectionORM.meeting_id == meeting_id)
             .order_by(SpeakerSelectionORM.created_at.desc()).first())
        return _speaker_to_entity(o) if o else None


class RetrospectiveRepository(IRetrospectiveRepository):
    def __init__(self, session: Session): self._s = session

    def get_by_meeting(self, meeting_id: int) -> Optional[Retrospective]:
        o = self._s.query(RetrospectiveORM).filter(RetrospectiveORM.meeting_id == meeting_id).first()
        return Retrospective(id=o.id, meeting_id=o.meeting_id, created_at=o.created_at) if o else None

    def create(self, retro: Retrospective) -> Retrospective:
        now = _now()
        o = RetrospectiveORM(meeting_id=retro.meeting_id, created_at=now)
        self._s.add(o); self._s.flush()
        return Retrospective(id=o.id, meeting_id=o.meeting_id, created_at=o.created_at)

    def add_insight(self, insight: Insight) -> Insight:
        now = _now()
        o = InsightORM(retro_id=insight.retro_id, body=insight.body,
                       created_by=insight.created_by, created_at=now)
        self._s.add(o); self._s.flush()
        return Insight(id=o.id, retro_id=o.retro_id, body=o.body,
                       created_by=o.created_by, created_at=o.created_at)

    def add_bookmark(self, bookmark: BookmarkAnswer) -> BookmarkAnswer:
        now = _now()
        o = BookmarkAnswerORM(retro_id=bookmark.retro_id, answer_id=bookmark.answer_id, created_at=now)
        self._s.add(o); self._s.flush()
        return BookmarkAnswer(id=o.id, retro_id=o.retro_id, answer_id=o.answer_id, created_at=o.created_at)

    def remove_bookmark(self, retro_id: int, answer_id: int) -> None:
        o = (self._s.query(BookmarkAnswerORM)
             .filter(BookmarkAnswerORM.retro_id == retro_id,
                     BookmarkAnswerORM.answer_id == answer_id).first())
        if o: self._s.delete(o)

    def add_new_question(self, nq: NewQuestion) -> NewQuestion:
        now = _now()
        o = NewQuestionORM(retro_id=nq.retro_id, body=nq.body, created_by=nq.created_by, created_at=now)
        self._s.add(o); self._s.flush()
        return NewQuestion(id=o.id, retro_id=o.retro_id, body=o.body,
                           created_by=o.created_by, created_at=o.created_at)

    def get_one_line_review(self, retro_id: int, participant_id: int) -> Optional[OneLineReview]:
        o = (self._s.query(OneLineReviewORM)
             .filter(OneLineReviewORM.retro_id == retro_id,
                     OneLineReviewORM.participant_id == participant_id).first())
        if not o: return None
        return OneLineReview(id=o.id, retro_id=o.retro_id, participant_id=o.participant_id,
                             body=o.body, created_at=o.created_at, updated_at=o.updated_at)

    def add_one_line_review(self, review: OneLineReview) -> OneLineReview:
        now = _now()
        try:
            o = OneLineReviewORM(retro_id=review.retro_id, participant_id=review.participant_id,
                                 body=review.body, created_at=now, updated_at=now)
            self._s.add(o); self._s.flush()
            return OneLineReview(id=o.id, retro_id=o.retro_id, participant_id=o.participant_id,
                                 body=o.body, created_at=o.created_at, updated_at=o.updated_at)
        except IntegrityError:
            self._s.rollback()
            from backend.common.errors import OneLineReviewDuplicateError
            raise OneLineReviewDuplicateError()

    def update_one_line_review(self, review: OneLineReview) -> OneLineReview:
        o = self._s.get(OneLineReviewORM, review.id)
        o.body = review.body
        self._s.flush()
        return OneLineReview(id=o.id, retro_id=o.retro_id, participant_id=o.participant_id,
                             body=o.body, created_at=o.created_at, updated_at=o.updated_at)

    def get_full(self, meeting_id: int) -> Optional[Retrospective]:
        o = self._s.query(RetrospectiveORM).filter(RetrospectiveORM.meeting_id == meeting_id).first()
        if not o: return None
        retro = Retrospective(id=o.id, meeting_id=o.meeting_id, created_at=o.created_at)
        retro.insights = [Insight(id=i.id, retro_id=i.retro_id, body=i.body,
                                  created_by=i.created_by, created_at=i.created_at)
                          for i in o.insights]
        retro.bookmarked_answers = [BookmarkAnswer(id=b.id, retro_id=b.retro_id,
                                                   answer_id=b.answer_id, created_at=b.created_at)
                                    for b in o.bookmarks]
        retro.new_questions = [NewQuestion(id=nq.id, retro_id=nq.retro_id, body=nq.body,
                                           created_by=nq.created_by, created_at=nq.created_at)
                               for nq in o.new_questions]
        retro.one_line_reviews = [OneLineReview(id=r.id, retro_id=r.retro_id,
                                                participant_id=r.participant_id, body=r.body,
                                                created_at=r.created_at, updated_at=r.updated_at)
                                  for r in o.one_line_reviews]
        return retro


# ── TopicBookRepository ──────────────────────────────────────────────────────

class TopicBookRepository(ITopicBookRepository):
    def __init__(self, session: Session):
        self._s = session

    def _to_entity(self, o: TopicBookORM) -> TopicBook:
        return TopicBook(id=o.id, topic_id=o.topic_id, book_id=o.book_id,
                         order_num=o.order_num, status=o.status, created_at=o.created_at)

    def list_by_topic(self, topic_id: int) -> list[TopicBook]:
        rows = self._s.query(TopicBookORM).filter_by(topic_id=topic_id)\
            .order_by(TopicBookORM.order_num).all()
        return [self._to_entity(r) for r in rows]

    def get(self, topic_book_id: int) -> Optional[TopicBook]:
        o = self._s.get(TopicBookORM, topic_book_id)
        return self._to_entity(o) if o else None

    def get_by_topic_and_order(self, topic_id: int, order_num: int) -> Optional[TopicBook]:
        o = self._s.query(TopicBookORM).filter_by(topic_id=topic_id, order_num=order_num).first()
        return self._to_entity(o) if o else None

    def get_by_topic_and_book(self, topic_id: int, book_id: int) -> Optional[TopicBook]:
        o = self._s.query(TopicBookORM).filter_by(topic_id=topic_id, book_id=book_id).first()
        return self._to_entity(o) if o else None

    def create(self, tb: TopicBook) -> TopicBook:
        o = TopicBookORM(topic_id=tb.topic_id, book_id=tb.book_id,
                         order_num=tb.order_num, status=tb.status,
                         created_at=_now())
        self._s.add(o)
        self._s.flush()
        return self._to_entity(o)

    def update_status(self, topic_book_id: int, status: str) -> TopicBook:
        o = self._s.get(TopicBookORM, topic_book_id)
        if o is None:
            raise ResourceError("topic_book not found")
        o.status = status
        self._s.flush()
        return self._to_entity(o)

    def count_completed(self, topic_id: int) -> int:
        return self._s.query(func.count(TopicBookORM.id))\
            .filter_by(topic_id=topic_id, status="completed").scalar() or 0


# ── ReadingLetterRepository ──────────────────────────────────────────────────

class ReadingLetterRepository(IReadingLetterRepository):
    def __init__(self, session: Session):
        self._s = session

    def _to_entity(self, o: ReadingLetterORM) -> ReadingLetter:
        return ReadingLetter(id=o.id, topic_id=o.topic_id,
                             participant_id=o.participant_id, body=o.body,
                             stats_json=o.stats_json, generated_at=o.generated_at)

    def get(self, topic_id: int, participant_id: int) -> Optional[ReadingLetter]:
        o = self._s.query(ReadingLetterORM).filter_by(
            topic_id=topic_id, participant_id=participant_id).first()
        return self._to_entity(o) if o else None

    def create(self, letter: ReadingLetter) -> ReadingLetter:
        o = ReadingLetterORM(topic_id=letter.topic_id,
                             participant_id=letter.participant_id,
                             body=letter.body, stats_json=letter.stats_json,
                             generated_at=_now())
        self._s.add(o)
        self._s.flush()
        return self._to_entity(o)

    def list_by_topic(self, topic_id: int) -> list[ReadingLetter]:
        rows = self._s.query(ReadingLetterORM).filter_by(topic_id=topic_id).all()
        return [self._to_entity(r) for r in rows]
