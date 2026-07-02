import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import decode_token, get_current_user
from tests.conftest import make_token


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


class TestDecodeToken:
    def test_valid_token_decodes(self):
        payload = decode_token(make_token(user_id=42))
        assert payload["user_id"] == 42
        assert payload["token_type"] == "access"


class TestGetCurrentUser:
    def test_valid_access_token_accepted(self):
        user = get_current_user(_credentials(make_token(user_id=42)))
        assert user.user_id == 42

    def test_wrong_signature_rejected(self):
        token = make_token(signing_key="a-completely-different-signing-key")
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(_credentials(token))
        assert exc_info.value.status_code == 401

    def test_expired_token_rejected(self):
        token = make_token(expires_in=-10)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(_credentials(token))
        assert exc_info.value.status_code == 401

    def test_refresh_token_rejected_as_access(self):
        token = make_token(token_type="refresh")
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(_credentials(token))
        assert exc_info.value.status_code == 401
        assert "access" in exc_info.value.detail.lower()

    def test_garbage_token_rejected(self):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(_credentials("not-a-jwt-at-all"))
        assert exc_info.value.status_code == 401
