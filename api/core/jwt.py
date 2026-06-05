import jwt

from api.config import settings


def encode_token(user_id: int) -> str:
    token = jwt.encode(
        {"user_id": user_id},
        settings.secret_key,
        algorithm="HS256"
    )
    return token.decode("utf-8") if isinstance(token, bytes) else token


def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"]
        )
        return payload["user_id"]
    except Exception:
        return None
