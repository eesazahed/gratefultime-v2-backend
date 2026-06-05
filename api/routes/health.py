from fastapi import APIRouter

from api.config import settings
from api.core.git import get_latest_commit

router = APIRouter(tags=["health"])


@router.get("/")
@router.get("/health")
def health():
    return {
        "message": "server running",
        "dev_mode": settings.dev_mode,
        "commit": get_latest_commit()
    }


@router.get("/commit")
def commit():
    return get_latest_commit()
