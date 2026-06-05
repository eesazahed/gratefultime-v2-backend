from fastapi import Depends, Header, HTTPException

from api.core.jwt import decode_token


def require_auth(authorization: str | None = Header(default=None)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"message": "Missing or invalid token"}
        )

    token = authorization.split(" ", 1)[1]
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid or expired token"}
        )

    return user_id


AuthUserId = Depends(require_auth)
