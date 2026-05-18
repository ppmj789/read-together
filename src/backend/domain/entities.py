# domain/entities.py
# PRG-ID: PRG-01~PRG-11 (도메인 엔티티)
# 외부 의존 없음 — Clean Architecture domain 계층 규칙
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Topic:
    id: Optional[int]
    title: str
    description: Optional[str]
    created_by: int
    created_at: str
    updated_at: str
    updated_by: Optional[int] = None
    status: str = "active"  # active | completed


@dataclass
class Step:
    id: Optional[int]
    topic_id: int
    order_num: int
    title: str
    perspective: Optional[str] = None


@dataclass
class Book:
    id: Optional[int]
    title: str
    reason: str
    created_by: int
    created_at: str
    updated_at: str
    role_desc: Optional[str] = None
    is_deleted: bool = False


@dataclass
class BookStep:
    id: Optional[int]
    book_id: int
    step_id: int


@dataclass
class Meeting:
    id: Optional[int]
    book_id: int
    topic_id: int
    code: str
    host_id: int
    current_stage: int
    status: str  # preparing | in_progress | completed
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class Participant:
    id: Optional[int]
    nickname: str
    meeting_id: int
    is_host: bool
    joined_at: str
    topic_id: Optional[int] = None


@dataclass
class Timer:
    id: Optional[int]
    meeting_id: int
    duration_sec: int
    remaining_sec: int
    is_running: bool
    mode: str  # countdown | countup
    last_started_at: Optional[str] = None


@dataclass
class Question:
    id: Optional[int]
    book_id: int
    body: str
    q_type: str  # understanding | self_connection | debate | application
    created_by: int
    created_at: str
    is_deleted: bool = False


@dataclass
class Answer:
    id: Optional[int]
    question_id: int
    participant_id: int
    body: str
    is_anonymous: bool
    is_revealed: bool
    created_at: str
    updated_at: str

    def reveal(self) -> None:
        """is_revealed 비가역 전환 — 도메인 불변식."""
        if self.is_revealed:
            from backend.common.errors import AnswerAlreadyRevealedError
            raise AnswerAlreadyRevealedError()
        self.is_revealed = True


@dataclass
class AnswerVote:
    id: Optional[int]
    answer_id: int
    participant_id: int
    vote_type: str  # empathy | rebut
    created_at: str


@dataclass
class AnswerGroup:
    id: Optional[int]
    meeting_id: int
    created_by: int
    created_at: str
    label: Optional[str] = None


@dataclass
class AnswerGroupItem:
    id: Optional[int]
    group_id: int
    answer_id: int


@dataclass
class Poll:
    id: Optional[int]
    meeting_id: int
    question: str
    is_closed: bool
    created_by: int
    created_at: str
    closed_at: Optional[str] = None
    options: list = field(default_factory=list)


@dataclass
class PollOption:
    id: Optional[int]
    poll_id: int
    label: str
    order_num: int
    vote_count: int = 0


@dataclass
class PollVote:
    id: Optional[int]
    poll_option_id: int
    poll_id: int
    participant_id: int
    created_at: str
    updated_at: str


@dataclass
class SpeakerSelection:
    id: Optional[int]
    meeting_id: int
    card_type: str
    created_at: str
    selected_id: Optional[int] = None
    question_id: Optional[int] = None


@dataclass
class Retrospective:
    id: Optional[int]
    meeting_id: int
    created_at: str
    insights: list = field(default_factory=list)
    bookmarked_answers: list = field(default_factory=list)
    new_questions: list = field(default_factory=list)
    one_line_reviews: list = field(default_factory=list)


@dataclass
class Insight:
    id: Optional[int]
    retro_id: int
    body: str
    created_by: int
    created_at: str


@dataclass
class BookmarkAnswer:
    id: Optional[int]
    retro_id: int
    answer_id: int
    created_at: str


@dataclass
class NewQuestion:
    id: Optional[int]
    retro_id: int
    body: str
    created_by: int
    created_at: str


@dataclass
class OneLineReview:
    id: Optional[int]
    retro_id: int
    participant_id: int
    body: str
    created_at: str
    updated_at: str


@dataclass
class TopicBook:
    id: Optional[int]
    topic_id: int
    book_id: int
    order_num: int  # 1, 2, or 3
    status: str  # pending | in_progress | completed
    created_at: str


@dataclass
class ReadingLetter:
    id: Optional[int]
    topic_id: int
    participant_id: int
    body: str
    generated_at: str
    stats_json: Optional[str] = None
