# infrastructure/db.py
# PRG-ID: 공통 인프라 (CMP-05)
# Failure Categories:
#   Resource — SQLite 파일 생성 실패 / 연결 실패
#   State Transition — FK 위반 (PRAGMA foreign_keys=ON)
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.infrastructure.config import get_settings


class Base(DeclarativeBase):
    pass


def _apply_pragmas(dbapi_conn: sqlite3.Connection, _connection_record) -> None:
    """SQLite 연결 시 WAL 모드 + FK 강제 활성화."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.execute("PRAGMA cache_size = -8000")
    cursor.close()


def _build_engine(db_path: str):
    url = f"sqlite:///{db_path}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    event.listen(engine, "connect", _apply_pragmas)
    return engine


def _create_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db(engine) -> None:
    """DDL 파일을 순서대로 실행하고, ALTER TABLE 컬럼을 안전하게 추가한다."""
    migrations_dir = Path(__file__).parent.parent.parent / "db" / "migrations"
    with engine.begin() as conn:
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            sql = sql_file.read_text(encoding="utf-8")
            conn.connection.executescript(sql)
        # SQLite ALTER TABLE ADD COLUMN은 IF NOT EXISTS 미지원 → Python에서 safe-add
        _safe_add_column(conn, "topic", "status", "TEXT NOT NULL DEFAULT 'active'")
        _safe_add_column(conn, "participant", "topic_id", "INTEGER REFERENCES topic(id)")


def _safe_add_column(conn, table: str, column: str, definition: str) -> None:
    """컬럼이 없을 때만 ALTER TABLE ADD COLUMN 실행."""
    import sqlite3
    try:
        conn.connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    except sqlite3.OperationalError:
        pass  # 이미 존재


# ── 싱글턴 엔진/세션팩토리 ──────────────────────────────────────────────────

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = _build_engine(settings.db_path)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = _create_session_factory(get_engine())
    return _SessionLocal


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """컨텍스트 매니저 기반 세션 (usecase에서 직접 사용)."""
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# FastAPI Depends 용
def get_db() -> Generator[Session, None, None]:
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
