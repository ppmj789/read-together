# usecase/roadmap/service.py
# PRG-ID: PRG-01 (주제 관리), PRG-02 (책 관리)
# RQ: RQ-F-01, RQ-F-02
# Failure Categories:
#   Input — 길이 제약 (Pydantic)
#   Business Rule — 호스트 권한 / 미존재 리소스
#   State Transition — 답변 존재 책 삭제 시도
#   Concurrency — N/A (단건 CRUD)
#   Resource — SQLite I/O

from backend.common.errors import (
    BookHasAnswersError,
    HostRequiredError,
    NotFoundError,
)
from backend.domain.entities import Book, BookStep, Question, Step, Topic, TopicBook
from backend.usecase.ports import (
    IBookRepository, IQuestionRepository, ITopicBookRepository, ITopicRepository,
)


class RoadmapSvc:
    """PRG-01 + PRG-02: 로드맵(주제·단계·책) CRUD."""

    def __init__(self, topic_repo: ITopicRepository, book_repo: IBookRepository,
                 topic_book_repo: ITopicBookRepository | None = None,
                 question_repo: IQuestionRepository | None = None):
        self._topics = topic_repo
        self._books = book_repo
        self._topic_books = topic_book_repo
        self._questions = question_repo

    # ── Topic ─────────────────────────────────────────────────────────────────
    def list_topics(self, meeting_id: int) -> list[dict]:
        topics = self._topics.list_all(meeting_id)
        return [_topic_to_dict(t) for t in topics]

    def get_topic(self, topic_id: int) -> dict:
        topic = self._topics.get(topic_id)
        if topic is None:
            raise NotFoundError("TOPIC")
        steps = self._topics.list_steps(topic_id)
        d = _topic_to_dict(topic)
        d["steps"] = [_step_to_dict(s) for s in steps]
        return d

    def create_topic(self, title: str, description: str | None, created_by: int, is_host: bool) -> dict:
        # Guard: Business Rule — 호스트만 생성
        if not is_host:
            raise HostRequiredError()
        topic = self._topics.create(Topic(
            id=None, title=title, description=description,
            created_by=created_by, created_at="", updated_at="",
        ))
        return _topic_to_dict(topic)

    def update_topic(self, topic_id: int, title: str, description: str | None,
                     updated_by: int, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        topic = self._topics.get(topic_id)
        if topic is None:
            raise NotFoundError("TOPIC")
        topic.title = title
        topic.description = description
        topic.updated_by = updated_by
        return _topic_to_dict(self._topics.update(topic))

    def delete_topic(self, topic_id: int, is_host: bool) -> None:
        if not is_host:
            raise HostRequiredError()
        topic = self._topics.get(topic_id)
        if topic is None:
            raise NotFoundError("TOPIC")
        self._topics.delete(topic_id)

    # ── Step ──────────────────────────────────────────────────────────────────
    def list_steps(self, topic_id: int) -> list[dict]:
        topic = self._topics.get(topic_id)
        if topic is None:
            raise NotFoundError("TOPIC")
        return [_step_to_dict(s) for s in self._topics.list_steps(topic_id)]

    def create_step(self, topic_id: int, order_num: int, title: str,
                    perspective: str | None, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        topic = self._topics.get(topic_id)
        if topic is None:
            raise NotFoundError("TOPIC")
        step = self._topics.create_step(Step(
            id=None, topic_id=topic_id, order_num=order_num,
            title=title, perspective=perspective,
        ))
        return _step_to_dict(step)

    def update_step(self, topic_id: int, step_id: int, title: str,
                    perspective: str | None, order_num: int, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        step = self._topics.get_step(step_id)
        if step is None or step.topic_id != topic_id:
            raise NotFoundError("STEP")
        step.title = title; step.perspective = perspective; step.order_num = order_num
        return _step_to_dict(self._topics.update_step(step))

    def delete_step(self, topic_id: int, step_id: int, is_host: bool) -> None:
        if not is_host:
            raise HostRequiredError()
        step = self._topics.get_step(step_id)
        if step is None or step.topic_id != topic_id:
            raise NotFoundError("STEP")
        self._topics.delete_step(step_id)

    # ── BookStep ──────────────────────────────────────────────────────────────
    def assign_book(self, topic_id: int, step_id: int, book_id: int, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        step = self._topics.get_step(step_id)
        if step is None or step.topic_id != topic_id:
            raise NotFoundError("STEP")
        book = self._books.get(book_id)
        if book is None or book.is_deleted:
            raise NotFoundError("BOOK")
        bs = self._topics.assign_book_to_step(BookStep(id=None, book_id=book_id, step_id=step_id))
        return {"book_step_id": bs.id, "book_id": book_id, "step_id": step_id}

    def remove_book(self, topic_id: int, step_id: int, book_id: int, is_host: bool) -> None:
        if not is_host:
            raise HostRequiredError()
        self._topics.remove_book_from_step(book_id, step_id)

    # ── Book ──────────────────────────────────────────────────────────────────
    def list_books(self) -> list[dict]:
        return [_book_to_dict(b) for b in self._books.list_active()]

    def get_book(self, book_id: int) -> dict:
        book = self._books.get(book_id)
        if book is None or book.is_deleted:
            raise NotFoundError("BOOK")
        return _book_to_dict(book)

    def create_book(self, title: str, reason: str, role_desc: str | None,
                    created_by: int, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        book = self._books.create(Book(
            id=None, title=title, reason=reason, role_desc=role_desc,
            created_by=created_by, created_at="", updated_at="",
        ))
        return _book_to_dict(book)

    def update_book(self, book_id: int, title: str, reason: str,
                    role_desc: str | None, is_host: bool) -> dict:
        if not is_host:
            raise HostRequiredError()
        book = self._books.get(book_id)
        if book is None or book.is_deleted:
            raise NotFoundError("BOOK")
        book.title = title; book.reason = reason; book.role_desc = role_desc
        return _book_to_dict(self._books.update(book))

    def delete_book(self, book_id: int, is_host: bool) -> None:
        if not is_host:
            raise HostRequiredError()
        book = self._books.get(book_id)
        if book is None or book.is_deleted:
            raise NotFoundError("BOOK")
        # State Transition: 답변 존재 책은 soft-delete 경고
        if self._books.has_answers(book_id):
            raise BookHasAnswersError()
        self._books.soft_delete(book_id)


# ── 직렬화 헬퍼 ───────────────────────────────────────────────────────────────

    # ── TopicBook (주제-책 로드맵) ──────────────────────────────────────────────

    def list_topic_books(self, topic_id: int) -> list[dict]:
        """주제 내 책 목록 (topic_book + book 정보)."""
        topic = self._topics.get(topic_id)
        if topic is None:
            raise NotFoundError("TOPIC")
        tbs = self._topic_books.list_by_topic(topic_id)
        result = []
        for tb in tbs:
            book = self._books.get(tb.book_id)
            result.append({
                "topic_book_id": tb.id,
                "order_num": tb.order_num,
                "status": tb.status,
                "book": _book_to_dict(book) if book else None,
            })
        return result

    def get_topic_progress(self, topic_id: int) -> dict:
        """주제 진행률."""
        topic = self._topics.get(topic_id)
        if topic is None:
            raise NotFoundError("TOPIC")
        tbs = self._topic_books.list_by_topic(topic_id)
        completed = sum(1 for tb in tbs if tb.status == "completed")
        current = next((tb for tb in tbs if tb.status == "in_progress"), None)
        current_book = None
        if current:
            book = self._books.get(current.book_id)
            current_book = _book_to_dict(book) if book else None
        return {
            "topic": _topic_to_dict(topic),
            "total": len(tbs),
            "completed": completed,
            "current_book": current_book,
            "books": [{
                "order_num": tb.order_num, "status": tb.status,
                "book_id": tb.book_id,
            } for tb in tbs],
        }

    def complete_topic_book(self, topic_id: int, book_id: int, is_host: bool) -> dict:
        """책 완료 처리. 3권 모두 완료 시 주제도 완료."""
        if not is_host:
            raise HostRequiredError()
        tb = self._topic_books.get_by_topic_and_book(topic_id, book_id)
        if tb is None:
            raise NotFoundError("TOPIC_BOOK")
        self._topic_books.update_status(tb.id, "completed")
        # 3권 모두 완료?
        if self._topic_books.count_completed(topic_id) >= 3:
            topic = self._topics.get(topic_id)
            if topic:
                topic.status = "completed"
                self._topics.update(topic)
        return {"topic_id": topic_id, "book_id": book_id, "status": "completed"}

    def add_next_book(self, topic_id: int, book_title: str, book_reason: str,
                      book_role_desc: str | None, questions: list[dict],
                      created_by: int, is_host: bool) -> dict:
        """다음 책 등록 (모임장 전용)."""
        if not is_host:
            raise HostRequiredError()
        topic = self._topics.get(topic_id)
        if topic is None:
            raise NotFoundError("TOPIC")
        existing = self._topic_books.list_by_topic(topic_id)
        next_order = len(existing) + 1
        if next_order > 3:
            from backend.common.errors import AppError
            raise AppError("TOPIC_BOOK_LIMIT", "주제당 최대 3권까지 등록할 수 있습니다.", 400)
        book = self._books.create(Book(
            id=None, title=book_title, reason=book_reason,
            role_desc=book_role_desc, created_by=created_by,
            created_at="", updated_at="",
        ))
        self._topic_books.create(TopicBook(
            id=None, topic_id=topic_id, book_id=book.id,
            order_num=next_order, status="pending", created_at="",
        ))
        if self._questions:
            for q in questions:
                self._questions.create(Question(
                    id=None, book_id=book.id, body=q["body"],
                    q_type=q.get("q_type", "self_connection"),
                    created_by=created_by, created_at="",
                ))
        return {"topic_id": topic_id, "book": _book_to_dict(book), "order_num": next_order}


def _topic_to_dict(t: Topic) -> dict:
    return {"id": t.id, "title": t.title, "description": t.description,
            "created_by": t.created_by, "created_at": t.created_at,
            "status": t.status}


def _step_to_dict(s: Step) -> dict:
    return {"id": s.id, "topic_id": s.topic_id, "order_num": s.order_num,
            "title": s.title, "perspective": s.perspective}


def _book_to_dict(b: Book) -> dict:
    return {"id": b.id, "title": b.title, "reason": b.reason, "role_desc": b.role_desc,
            "created_by": b.created_by, "created_at": b.created_at,
            "updated_at": b.updated_at, "is_deleted": b.is_deleted}
