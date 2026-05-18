# adapter/persistence/models.py
# SQLAlchemy ORM 모델 — TBL-01 물리 매핑
# PRG-ID: PRG-01~PRG-11 공통 (persistence 계층)
from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.infrastructure.db import Base


class TopicORM(Base):
    __tablename__ = "topic"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("participant.id"), nullable=False)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)
    updated_by = Column(Integer, ForeignKey("participant.id"))
    status = Column(Text, nullable=False, default="active")
    steps = relationship("StepORM", back_populates="topic", cascade="all, delete-orphan")
    topic_books = relationship("TopicBookORM", back_populates="topic", cascade="all, delete-orphan")


class StepORM(Base):
    __tablename__ = "step"
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("topic.id", ondelete="CASCADE"), nullable=False)
    order_num = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    perspective = Column(Text)
    topic = relationship("TopicORM", back_populates="steps")
    __table_args__ = (UniqueConstraint("topic_id", "order_num"),)


class BookORM(Base):
    __tablename__ = "book"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    role_desc = Column(Text)
    created_by = Column(Integer, ForeignKey("participant.id"), nullable=False)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)
    is_deleted = Column(Integer, nullable=False, default=0)


class BookStepORM(Base):
    __tablename__ = "book_step"
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("book.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(Integer, ForeignKey("step.id", ondelete="CASCADE"), nullable=False)
    __table_args__ = (UniqueConstraint("book_id", "step_id"),)


class MeetingORM(Base):
    __tablename__ = "meeting"
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("book.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topic.id"), nullable=False)
    code = Column(Text, nullable=False, unique=True)
    host_id = Column(Integer, nullable=False)  # DEFERRABLE — FK 선언 생략
    current_stage = Column(Integer, nullable=False, default=1)
    status = Column(Text, nullable=False, default="preparing")
    created_at = Column(Text, nullable=False)
    started_at = Column(Text)
    completed_at = Column(Text)
    participants = relationship("ParticipantORM", back_populates="meeting", cascade="all, delete-orphan")
    timer = relationship("TimerORM", back_populates="meeting", uselist=False, cascade="all, delete-orphan")


class ParticipantORM(Base):
    __tablename__ = "participant"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(Text, nullable=False)
    meeting_id = Column(Integer, ForeignKey("meeting.id", ondelete="CASCADE"), nullable=False)
    is_host = Column(Integer, nullable=False, default=0)
    joined_at = Column(Text, nullable=False)
    topic_id = Column(Integer, ForeignKey("topic.id"), nullable=True)
    meeting = relationship("MeetingORM", back_populates="participants")
    __table_args__ = (UniqueConstraint("meeting_id", "nickname"),)


class TimerORM(Base):
    __tablename__ = "timer"
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meeting.id", ondelete="CASCADE"), nullable=False, unique=True)
    duration_sec = Column(Integer, nullable=False, default=600)
    remaining_sec = Column(Integer, nullable=False, default=600)
    is_running = Column(Integer, nullable=False, default=0)
    mode = Column(Text, nullable=False, default="countdown")
    last_started_at = Column(Text)
    meeting = relationship("MeetingORM", back_populates="timer")


class QuestionORM(Base):
    __tablename__ = "question"
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("book.id"), nullable=False)
    body = Column(Text, nullable=False)
    q_type = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("participant.id"), nullable=False)
    created_at = Column(Text, nullable=False)
    is_deleted = Column(Integer, nullable=False, default=0)


class AnswerORM(Base):
    __tablename__ = "answer"
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("question.id"), nullable=False)
    participant_id = Column(Integer, ForeignKey("participant.id"), nullable=False)
    body = Column(Text, nullable=False)
    is_anonymous = Column(Integer, nullable=False, default=0)
    is_revealed = Column(Integer, nullable=False, default=0)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint("question_id", "participant_id"),)


class AnswerVoteORM(Base):
    __tablename__ = "answer_vote"
    id = Column(Integer, primary_key=True, autoincrement=True)
    answer_id = Column(Integer, ForeignKey("answer.id", ondelete="CASCADE"), nullable=False)
    participant_id = Column(Integer, ForeignKey("participant.id"), nullable=False)
    vote_type = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint("answer_id", "participant_id"),)


class AnswerGroupORM(Base):
    __tablename__ = "answer_group"
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meeting.id", ondelete="CASCADE"), nullable=False)
    label = Column(Text)
    created_by = Column(Integer, ForeignKey("participant.id"), nullable=False)
    created_at = Column(Text, nullable=False)
    items = relationship("AnswerGroupItemORM", cascade="all, delete-orphan")


class AnswerGroupItemORM(Base):
    __tablename__ = "answer_group_item"
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("answer_group.id", ondelete="CASCADE"), nullable=False)
    answer_id = Column(Integer, ForeignKey("answer.id", ondelete="CASCADE"), nullable=False)
    __table_args__ = (UniqueConstraint("group_id", "answer_id"),)


class PollORM(Base):
    __tablename__ = "poll"
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meeting.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    is_closed = Column(Integer, nullable=False, default=0)
    created_by = Column(Integer, ForeignKey("participant.id"), nullable=False)
    created_at = Column(Text, nullable=False)
    closed_at = Column(Text)
    options = relationship("PollOptionORM", cascade="all, delete-orphan", order_by="PollOptionORM.order_num")


class PollOptionORM(Base):
    __tablename__ = "poll_option"
    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_id = Column(Integer, ForeignKey("poll.id", ondelete="CASCADE"), nullable=False)
    label = Column(Text, nullable=False)
    order_num = Column(Integer, nullable=False)


class PollVoteORM(Base):
    __tablename__ = "poll_vote"
    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_option_id = Column(Integer, ForeignKey("poll_option.id", ondelete="CASCADE"), nullable=False)
    poll_id = Column(Integer, ForeignKey("poll.id", ondelete="CASCADE"), nullable=False)
    participant_id = Column(Integer, ForeignKey("participant.id"), nullable=False)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint("poll_id", "participant_id"),)


class SpeakerSelectionORM(Base):
    __tablename__ = "speaker_selection"
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meeting.id", ondelete="CASCADE"), nullable=False)
    card_type = Column(Text, nullable=False)
    selected_id = Column(Integer, ForeignKey("participant.id"))
    question_id = Column(Integer, ForeignKey("question.id"))
    created_at = Column(Text, nullable=False)


class RetrospectiveORM(Base):
    __tablename__ = "retrospective"
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meeting.id", ondelete="CASCADE"), nullable=False, unique=True)
    created_at = Column(Text, nullable=False)
    insights = relationship("InsightORM", cascade="all, delete-orphan")
    bookmarks = relationship("BookmarkAnswerORM", cascade="all, delete-orphan")
    new_questions = relationship("NewQuestionORM", cascade="all, delete-orphan")
    one_line_reviews = relationship("OneLineReviewORM", cascade="all, delete-orphan")


class InsightORM(Base):
    __tablename__ = "insight"
    id = Column(Integer, primary_key=True, autoincrement=True)
    retro_id = Column(Integer, ForeignKey("retrospective.id", ondelete="CASCADE"), nullable=False)
    body = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("participant.id"), nullable=False)
    created_at = Column(Text, nullable=False)


class BookmarkAnswerORM(Base):
    __tablename__ = "bookmark_answer"
    id = Column(Integer, primary_key=True, autoincrement=True)
    retro_id = Column(Integer, ForeignKey("retrospective.id", ondelete="CASCADE"), nullable=False)
    answer_id = Column(Integer, ForeignKey("answer.id"), nullable=False)
    created_at = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint("retro_id", "answer_id"),)


class NewQuestionORM(Base):
    __tablename__ = "new_question"
    id = Column(Integer, primary_key=True, autoincrement=True)
    retro_id = Column(Integer, ForeignKey("retrospective.id", ondelete="CASCADE"), nullable=False)
    body = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("participant.id"), nullable=False)
    created_at = Column(Text, nullable=False)


class OneLineReviewORM(Base):
    __tablename__ = "one_line_review"
    id = Column(Integer, primary_key=True, autoincrement=True)
    retro_id = Column(Integer, ForeignKey("retrospective.id", ondelete="CASCADE"), nullable=False)
    participant_id = Column(Integer, ForeignKey("participant.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint("retro_id", "participant_id"),)


class TopicBookORM(Base):
    __tablename__ = "topic_book"
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("topic.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("book.id"), nullable=False)
    order_num = Column(Integer, nullable=False)
    status = Column(Text, nullable=False, default="pending")
    created_at = Column(Text, nullable=False)
    topic = relationship("TopicORM", back_populates="topic_books")
    __table_args__ = (UniqueConstraint("topic_id", "order_num"),
                      UniqueConstraint("topic_id", "book_id"))


class ReadingLetterORM(Base):
    __tablename__ = "reading_letter"
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("topic.id"), nullable=False)
    participant_id = Column(Integer, ForeignKey("participant.id"), nullable=False)
    body = Column(Text, nullable=False)
    stats_json = Column(Text)
    generated_at = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint("topic_id", "participant_id"),)
