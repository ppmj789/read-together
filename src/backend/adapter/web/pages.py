# adapter/web/pages.py
# Jinja2 HTML 페이지 라우터 (SCN-01~09)
# PRG-ID: SCN-01~SCN-09 (web 계층)
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["페이지"])

_template_dir = Path(__file__).parent.parent.parent.parent / "web" / "templates"
templates = Jinja2Templates(directory=str(_template_dir))


@router.get("/", response_class=HTMLResponse)
def scn01_join(request: Request):
    """SCN-01: 참가 화면."""
    return templates.TemplateResponse(request, "scn01_join.html")


@router.get("/roadmap", response_class=HTMLResponse)
def scn02_roadmap(request: Request):
    """SCN-02: 로드맵 관리 화면 (모임장)."""
    return templates.TemplateResponse(request, "scn02_roadmap.html")


@router.get("/book", response_class=HTMLResponse)
def scn03_book(request: Request):
    """SCN-03: 책 상세 + 사전 답변 화면."""
    return templates.TemplateResponse(request, "scn03_book.html")


@router.get("/discussion", response_class=HTMLResponse)
def scn04_discussion(request: Request):
    """SCN-04: 토론 화면."""
    return templates.TemplateResponse(request, "scn04_discussion.html")


@router.get("/speaker", response_class=HTMLResponse)
def scn05_speaker(request: Request):
    """SCN-05: 발언자 선정 화면."""
    return templates.TemplateResponse(request, "scn05_speaker.html")


@router.get("/poll", response_class=HTMLResponse)
def scn06_poll(request: Request):
    """SCN-06: 투표 화면."""
    return templates.TemplateResponse(request, "scn06_poll.html")


@router.get("/timer", response_class=HTMLResponse)
def scn07_timer(request: Request):
    """SCN-07: 타이머 화면."""
    return templates.TemplateResponse(request, "scn07_timer.html")


@router.get("/session", response_class=HTMLResponse)
def scn08_session(request: Request):
    """SCN-08: 모임 진행 통합 화면 (실시간)."""
    return templates.TemplateResponse(request, "scn08_session.html")


@router.get("/retro", response_class=HTMLResponse)
def scn09_retro(request: Request):
    """SCN-09: 회고 화면."""
    return templates.TemplateResponse(request, "scn09_retro.html")
