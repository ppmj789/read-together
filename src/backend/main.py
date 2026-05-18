# main.py — FastAPI 앱 진입점
# PRG-ID: 전체 (CMP-05 공통 인프라)
# Failure Categories:
#   Resource — DB 초기화 실패 (시작 시 즉시 종료)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from backend.adapter.web.api.v1 import auth, discussion, letter, meeting, retrospective, roadmap, setup
from backend.adapter.web.exception_handlers import app_error_handler, generic_error_handler
from backend.common.errors import AppError
from backend.infrastructure.db import get_engine, init_db

# ── 앱 팩토리 ─────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="read-together API",
        description="독서토론 보조 플랫폼 REST API (PRG-01~PRG-11)",
        version="1.0.0",
    )

    # 예외 핸들러
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    # CORS (개발 환경)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 정적 파일
    static_dir = Path(__file__).parent.parent / "web" / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # API 라우터 등록
    prefix = "/api/v1"
    app.include_router(auth.router, prefix=prefix)
    app.include_router(roadmap.router, prefix=prefix)
    app.include_router(discussion.router, prefix=prefix)
    app.include_router(meeting.router, prefix=prefix)
    app.include_router(retrospective.router, prefix=prefix)
    app.include_router(setup.router, prefix=prefix)
    app.include_router(letter.router, prefix=prefix)

    # Jinja2 페이지 라우터 (SCN 렌더링)
    try:
        from backend.adapter.web.pages import router as page_router
        app.include_router(page_router)
    except ImportError:
        pass  # 페이지 라우터 선택적

    # 시작 시 DB 초기화
    @app.on_event("startup")
    def on_startup():
        engine = get_engine()
        init_db(engine)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
