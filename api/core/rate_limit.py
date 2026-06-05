import jwt
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.config import settings


def get_user_or_ip(request: Request):
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            user_id = jwt.decode(
                token,
                settings.secret_key,
                algorithms=["HS256"]
            )["user_id"]
            return str(user_id)
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=get_user_or_ip)
