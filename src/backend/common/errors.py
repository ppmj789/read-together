# common/errors.py
# PRG-ID: 전체 (공통 에러 계층)
# Failure Categories: 모든 7 카테고리에 대한 도메인 예외 정의
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppError(Exception):
    """애플리케이션 예외 기반 클래스."""
    code: str
    message: str
    http_status: int
    details: list[Any] = field(default_factory=list)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# ── Input Failure ────────────────────────────────────────────────────────────
class InputValidationError(AppError):
    def __init__(self, message: str = "입력 값이 유효하지 않습니다.", details: list = None):
        super().__init__(
            code="INPUT_VALIDATION_FAILED",
            message=message,
            http_status=400,
            details=details or [],
        )


# ── State Transition Failure ─────────────────────────────────────────────────
class StateTransitionError(AppError):
    def __init__(self, code: str, message: str):
        super().__init__(code=code, message=message, http_status=409)


class MeetingAlreadyCompletedError(StateTransitionError):
    def __init__(self):
        super().__init__("MEETING_ALREADY_COMPLETED", "이미 종료된 모임입니다.")


class AnswerAlreadyRevealedError(StateTransitionError):
    def __init__(self):
        super().__init__("ANSWER_ALREADY_REVEALED", "이미 공개된 답변입니다.")


class PollClosedError(StateTransitionError):
    def __init__(self):
        super().__init__("POLL_CLOSED", "이미 마감된 투표입니다.")


class RetroNotAccessibleError(StateTransitionError):
    def __init__(self):
        super().__init__("RETRO_NOT_ACCESSIBLE", "모임이 완료된 후에만 회고에 접근할 수 있습니다.")


class OneLineReviewDuplicateError(StateTransitionError):
    def __init__(self):
        super().__init__("ONE_LINE_REVIEW_DUPLICATE", "이미 한 줄 회고를 제출하셨습니다.")


# ── External Dependency Failure ──────────────────────────────────────────────
class ExternalDependencyError(AppError):
    def __init__(self, message: str = "외부 서비스 오류입니다."):
        super().__init__(code="EXTERNAL_DEPENDENCY_ERROR", message=message, http_status=502)


# ── Concurrency / Race Failure ───────────────────────────────────────────────
class ConcurrencyError(AppError):
    def __init__(self, code: str, message: str):
        super().__init__(code=code, message=message, http_status=409)


class NicknameDuplicateError(ConcurrencyError):
    def __init__(self):
        super().__init__("NICKNAME_DUPLICATE", "동일 모임 내 이미 사용 중인 닉네임입니다.")


class AnswerVoteDuplicateError(ConcurrencyError):
    def __init__(self):
        super().__init__("CONCURRENCY_ANSWER_VOTE", "이미 투표하셨습니다.")


# ── Partial Failure ──────────────────────────────────────────────────────────
class PartialFailureError(AppError):
    def __init__(self, message: str = "작업이 부분적으로 실패했습니다."):
        super().__init__(code="PARTIAL_FAILURE", message=message, http_status=500)


# ── Resource Failure ─────────────────────────────────────────────────────────
class ResourceError(AppError):
    def __init__(self, message: str = "데이터베이스 오류가 발생했습니다."):
        super().__init__(code="RESOURCE_DB_ERROR", message=message, http_status=503)


# ── Business Rule Violation ──────────────────────────────────────────────────
class AuthRequiredError(AppError):
    def __init__(self):
        super().__init__(code="AUTH_REQUIRED", message="인증이 필요합니다.", http_status=401)


class HostRequiredError(AppError):
    def __init__(self):
        super().__init__(code="HOST_REQUIRED", message="모임장 권한이 필요합니다.", http_status=403)


class OwnerRequiredError(AppError):
    def __init__(self, code: str = "OWNER_REQUIRED", message: str = "본인만 수행할 수 있습니다."):
        super().__init__(code=code, message=message, http_status=403)


class AnswerRevealNotAllowedError(OwnerRequiredError):
    def __init__(self):
        super().__init__("ANSWER_REVEAL_NOT_ALLOWED", "본인 답변만 공개할 수 있습니다.")


class NotFoundError(AppError):
    def __init__(self, resource: str = "리소스"):
        super().__init__(
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource}을(를) 찾을 수 없습니다.",
            http_status=404,
        )


class MeetingCodeInvalidError(AppError):
    def __init__(self):
        super().__init__(code="MEETING_CODE_INVALID", message="유효하지 않은 모임 코드입니다.", http_status=400)


class BookHasAnswersError(AppError):
    def __init__(self):
        super().__init__(code="BOOK_HAS_ANSWERS", message="답변이 존재하는 책은 삭제할 수 없습니다.", http_status=409)


class VoteDataUnavailableError(AppError):
    def __init__(self):
        super().__init__(code="VOTE_DATA_UNAVAILABLE", message="발언자 선정에 필요한 데이터가 없습니다.", http_status=422)


class CardTypeInvalidError(AppError):
    def __init__(self):
        super().__init__(code="CARD_TYPE_INVALID", message="유효하지 않은 카드 유형입니다.", http_status=400)


class RuleMeetingIdMismatchError(AppError):
    def __init__(self):
        super().__init__(code="RULE_MEETING_ID_MISMATCH", message="다른 모임에 접근할 수 없습니다.", http_status=403)
