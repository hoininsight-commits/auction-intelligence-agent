"""Health Check API (지시서 §7.1)."""

from fastapi import APIRouter

from app.core.constants import SERVICE_NAME

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
    }
