"""Auction Intelligence Agent — FastAPI 애플리케이션 엔트리포인트."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

app.include_router(api_router)

# 관리자용 정적 페이지 (지시서 §2.2 — Swagger UI 활용 원칙에 맞춘 빌드리스 HTML/JS 페이지).
# http://localhost:8000/admin 에서 접근 가능.
_ADMIN_STATIC_DIR = Path(__file__).parent / "static" / "admin"
app.mount("/admin", StaticFiles(directory=_ADMIN_STATIC_DIR, html=True), name="admin")
