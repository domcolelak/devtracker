import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer()


class CurrentUser:
    """MINIMAL IDENTITY DERIVED FROM THE JWT CLAIMS - NO DB LOOKUP AGAINST core-django's
    USER TABLE IS NEEDED SINCE THE TOKEN IS ALREADY SIGNED BY THAT SERVICE."""

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id


def decode_token(token: str) -> dict:
    """VALIDATES A TOKEN ISSUED BY core-django's djangorestframework-simplejwt USING THE
    SAME JWT_SIGNING_KEY/JWT_ALGORITHM, SO NO EXTRA ROUND TRIP TO DJANGO IS NEEDED.
    RAISES jwt.PyJWTError SUBCLASSES ON FAILURE."""
    return jwt.decode(token, settings.jwt_signing_key, algorithms=[settings.jwt_algorithm])


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc

    if payload.get("token_type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not an access token")

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing user_id claim"
        )

    return CurrentUser(user_id=user_id)
