from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pytz

from api.config import settings
from api.core.apple import AppleAuthError, verify_identity_token
from api.core.jwt import encode_token
from api.db import users as user_db

router = APIRouter(tags=["auth"])


class AppleLoginRequest(BaseModel):
    identityToken: str | None = None
    user: str | None = None
    email: str | None = None
    fullName: dict | None = None
    user_timezone: str | None = None


@router.post("/applelogin")
def apple_login(body: AppleLoginRequest):
    if not body.user_timezone:
        raise HTTPException(status_code=400, detail={"message": "Could not fetch user timezone"})

    if body.user_timezone not in pytz.all_timezones:
        raise HTTPException(status_code=400, detail={"message": "Invalid timezone"})

    if not body.identityToken or not body.user:
        raise HTTPException(
            status_code=400,
            detail={"message": "Missing Apple identity token or user ID"}
        )

    try:
        payload = verify_identity_token(body.identityToken)
    except AppleAuthError:
        raise HTTPException(status_code=401, detail={"message": "Invalid identity token"})

    if payload.get("sub") != body.user:
        raise HTTPException(status_code=401, detail={"message": "Token user ID mismatch"})

    full_name = body.fullName or {}
    given_name = full_name.get("givenName")
    family_name = full_name.get("familyName")
    full_name_str = f"{given_name} {family_name}" if given_name or family_name else ""
    email = (body.email or "").strip().lower()

    user = user_db.find_by_apple_user_id(body.user)
    if not user:
        if settings.dev_mode:
            user = user_db.create_user(
                email="eszhd@icloud.com",
                username="Eesa Zahed",
                apple_user_id=body.user,
                user_timezone=body.user_timezone
            )
            return {"token": encode_token(user.user_id)}

        if not email:
            raise HTTPException(
                status_code=400,
                detail={"message": "Email required on first Apple login"}
            )

        if user_db.find_by_email_insensitive(email):
            raise HTTPException(
                status_code=400,
                detail={"message": "Account conflict. Email already taken"}
            )

        user = user_db.create_user(
            email=email,
            username=full_name_str,
            apple_user_id=body.user,
            user_timezone=body.user_timezone
        )

    return {"token": encode_token(user.user_id)}
