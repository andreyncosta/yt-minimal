import os
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
import jwt

_JWT_ALGORITHM = "HS256"
_WWW_AUTH = {"WWW-Authenticate": "Bearer"}


async def get_current_user(
    request: Request,
    authorization: Annotated[str, Header()],
) -> str:
    """Validate the Bearer JWT and return the authenticated user_id.

    Also writes user_id to request.state so the rate-limiter key function
    can switch from IP-based to per-user limiting on protected endpoints.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorisation header",
            headers=_WWW_AUTH,
        )

    token = authorization.removeprefix("Bearer ")

    try:
        payload = jwt.decode(
            token,
            os.environ["JWT_SECRET_KEY"],
            algorithms=[_JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers=_WWW_AUTH,
        )

    user_id: str = payload["sub"]
    request.state.user_id = user_id
    return user_id


# Convenience alias — use as a type annotation in route signatures
CurrentUser = Annotated[str, Depends(get_current_user)]
