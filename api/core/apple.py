import datetime

import jwt
from jwt import PyJWKClient

from api.config import settings

APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"

_jwk_client = PyJWKClient(APPLE_KEYS_URL)


class AppleAuthError(Exception):
    pass


def verify_identity_token(identity_token: str) -> dict:
    try:
        signing_key = _jwk_client.get_signing_key_from_jwt(identity_token)
        return jwt.decode(
            identity_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.apple_audiences,
            issuer=APPLE_ISSUER,
            leeway=datetime.timedelta(seconds=300)
        )
    except Exception as error:
        raise AppleAuthError("Invalid identity token") from error
