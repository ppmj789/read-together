# usecase/setup/service.py
# 모임 만들기 원자적 플로우: 닉네임 → 주제 → 책 → 질문 → 모임 생성
from backend.domain.entities import (
    Book, Meeting, Participant, Question, Topic, TopicBook,
)
from backend.infrastructure.auth import create_token
from backend.usecase.ports import (
    IBookRepository, IMeetingRepository, IParticipantRepository,
    IQuestionRepository, ITopicBookRepository, ITopicRepository,
)


class SetupSvc:
    def __init__(
        self,
        topic_repo: ITopicRepository,
        book_repo: IBookRepository,
        topic_book_repo: ITopicBookRepository,
        question_repo: IQuestionRepository,
        meeting_repo: IMeetingRepository,
        participant_repo: IParticipantRepository,
    ):
        self._topics = topic_repo
        self._books = book_repo
        self._topic_books = topic_book_repo
        self._questions = question_repo
        self._meetings = meeting_repo
        self._participants = participant_repo

    def create_meeting_with_setup(
        self,
        nickname: str,
        topic_title: str,
        topic_desc: str | None,
        book_title: str,
        book_reason: str,
        book_role_desc: str | None,
        questions: list[dict],
    ) -> dict:
        """원자적 모임 생성.

        순서 (FK 제약 만족):
        1. 더미 participant 없이 raw SQL로 meeting+participant 순환 참조 해결
           → SQLite DEFERRABLE INITIALLY DEFERRED FK 활용
        """
        # FK 순환 해결: FK 일시 해제 → 전체 INSERT → FK 재활성화
        session = self._participants._s
        session.execute(__import__('sqlalchemy').text("PRAGMA foreign_keys = OFF"))
        session.flush()

        # 1. topic 생성 (created_by=0 임시)
        topic = self._topics.create(Topic(
            id=None, title=topic_title, description=topic_desc,
            created_by=0, created_at="", updated_at="",
            status="active",
        ))

        # 2. book 생성 (created_by=0 임시)
        book = self._books.create(Book(
            id=None, title=book_title, reason=book_reason,
            role_desc=book_role_desc, created_by=0,
            created_at="", updated_at="",
        ))

        # 3. topic_book 연결
        self._topic_books.create(TopicBook(
            id=None, topic_id=topic.id, book_id=book.id,
            order_num=1, status="in_progress", created_at="",
        ))

        # 4. meeting 생성 (host_id=0 임시)
        meeting = self._meetings.create(Meeting(
            id=None, book_id=book.id, topic_id=topic.id,
            code="", host_id=0,
            current_stage=1, status="preparing",
            created_at="",
        ))

        # 5. participant (host) 생성
        participant = self._participants.create(Participant(
            id=None, nickname=nickname, meeting_id=meeting.id,
            is_host=True, joined_at="", topic_id=topic.id,
        ))

        # 6. 실제 값으로 업데이트
        meeting.host_id = participant.id
        self._meetings.update(meeting)
        topic.created_by = participant.id
        self._topics.update(topic)
        book.created_by = participant.id
        self._books.update(book)

        # FK 재활성화
        session.execute(__import__('sqlalchemy').text("PRAGMA foreign_keys = ON"))
        session.flush()

        # 8. question 생성
        for q in questions:
            self._questions.create(Question(
                id=None, book_id=book.id, body=q["body"],
                q_type=q.get("q_type", "self_connection"),
                created_by=participant.id, created_at="",
            ))

        # 9. 토큰 발급
        token = create_token(participant.id, meeting.id)

        return {
            "session_token": token,
            "meeting_code": meeting.code,
            "meeting_id": meeting.id,
            "participant_id": participant.id,
            "topic_id": topic.id,
            "book_id": book.id,
        }
