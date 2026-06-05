from fastapi import APIRouter, HTTPException

from api.db import users as user_db
from api.dependencies import AuthUserId
from api.services.quota import get_ai_previews_remaining

router = APIRouter(tags=["user"])


@router.get("/me")
def get_me(user_id: int = AuthUserId):
    user = user_db.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "User not found"})

    return {
        "message": "User information retrieved successfully",
        "data": {
            "user_id": user.user_id,
            "email": user.email,
            "is_plus": user.is_plus,
            "ai_previews_remaining": get_ai_previews_remaining(user)
        }
    }
