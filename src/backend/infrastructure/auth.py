# infrastructure/auth.py
# PRG-ID: PRG-10 (인증·세션 관리)
# Failure Categories:
#   Input — 토큰 형식 오류 / BASE64 디코딩 실패
#   Business Rule — HMAC 서명 불일치 (위조)
#   State Transition — 만료 토큰
import base64
import hashlib
import hmac
import time
from dataclasses import dataclass

from backend.infrastructure.config import get_settings


@dataclass(frozen=True)
class TokenPayload:
    participant_id: int
    meeting_id: int
    issued_at: int  # Unix epoch


def _sign(payload_str: str, secret: str) -> str:
    """HMAC-SHA256 서명 → HEX."""
    return hmac.new(
        secret.encode(),
        payload_str.encode(),
        hashlib.sha256,
    ).hexdigest()


def create_token(participant_id: int, meeting_id: int) -> str:
    """토큰 생성: BASE64URL({participant_id}:{meeting_id}:{ts}:{sig})."""
    settings = get_settings()
    ts = int(time.time())
    payload_str = f"{participant_id}:{meeting_id}:{ts}"
    sig = _sign(payload_str, settings.secret_key)
    raw = f"{payload_str}:{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def verify_token(token: str) -> TokenPayload:
    """토큰 검증 → TokenPayload.
    실패 시 ValueError 발생 (adapter 계층에서 401로 변환).
    """
    settings = get_settings()
    # Input Failure: BASE64 디코딩 오류
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
    except Exception as exc:
        raise ValueError("TOKEN_MALFORMED") from exc

    parts = raw.split(":")
    if len(parts) != 4:
        raise ValueError("TOKEN_MALFORMED")

    participant_id_str, meeting_id_str, ts_str, provided_sig = parts

    # Business Rule: HMAC 검증
    payload_str = f"{participant_id_str}:{meeting_id_str}:{ts_str}"
    expected_sig = _sign(payload_str, settings.secret_key)
    if not hmac.compare_digest(expected_sig, provided_sig):
        raise ValueError("TOKEN_INVALID_SIGNATURE")

    # State Transition: 만료 검사
    try:
        ts = int(ts_str)
        participant_id = int(participant_id_str)
        meeting_id = int(meeting_id_str)
    except ValueError as exc:
        raise ValueError("TOKEN_MALFORMED") from exc

    ttl_sec = settings.token_ttl_hours * 3600
    if int(time.time()) - ts > ttl_sec:
        raise ValueError("TOKEN_EXPIRED")

    return TokenPayload(
        participant_id=participant_id,
        meeting_id=meeting_id,
        issued_at=ts,
    )
