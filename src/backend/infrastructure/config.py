# infrastructure/config.py
# PRG-ID: 공통 인프라 (CMP-05)
# Failure Category: Resource (환경 변수 누락 시 즉시 실패)
import os
from functools import lru_cache


class Settings:
    # DB
    db_path: str = os.getenv("DB_PATH", "read_together.db")
    # 인증
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production-32chars!!")
    token_ttl_hours: int = int(os.getenv("TOKEN_TTL_HOURS", "24"))
    # 앱
    app_env: str = os.getenv("APP_ENV", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
