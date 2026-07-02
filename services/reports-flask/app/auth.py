import functools
from collections.abc import Callable

import jwt
from flask import current_app, jsonify, request


def require_auth(view: Callable) -> Callable:
    """VALIDATES A JWT ISSUED BY core-django's djangorestframework-simplejwt USING
    THE SAME JWT_SIGNING_KEY/JWT_ALGORITHM - SAME PATTERN AS api-fastapi."""

    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify(detail="Missing bearer token"), 401

        token = auth_header.removeprefix("Bearer ")
        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SIGNING_KEY"],
                algorithms=[current_app.config["JWT_ALGORITHM"]],
            )
        except jwt.PyJWTError:
            return jsonify(detail="Invalid or expired token"), 401

        if payload.get("token_type") != "access":
            return jsonify(detail="Not an access token"), 401

        return view(*args, **kwargs)

    return wrapped
