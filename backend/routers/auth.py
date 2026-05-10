import os
from typing import Annotated

import httpx
from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict

from limiter import limiter
from services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


def _mobile_scheme() -> str:
    return os.getenv("MOBILE_REDIRECT_SCHEME", "ytminimal")


@router.get("/login")
@limiter.limit("30/minute")
async def login(request: Request) -> RedirectResponse:
    return RedirectResponse(url=auth_service.build_auth_url())


@router.get("/callback")
@limiter.limit("10/minute")
async def callback(
    request: Request,
    code: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
    # error_description excluded from responses — may contain PII
    error_description: Annotated[str | None, Query()] = None,  # noqa: ARG001
) -> RedirectResponse:
    """Exchange the OAuth code and redirect to the mobile app with the session JWT.

    On success:  <scheme>://auth?token=<jwt>
    On failure:  <scheme>://auth?error=<reason>

    The redirect is intercepted by expo-web-browser (openAuthSessionAsync) before
    the OS ever opens the app, so the JWT is never shown in a browser address bar.
    """
    scheme = _mobile_scheme()

    if error or not code:
        return RedirectResponse(
            url=f"{scheme}://auth?error=oauth_denied",
            status_code=302,
        )

    try:
        session_token = await auth_service.exchange_code(code)
    except httpx.HTTPStatusError:
        return RedirectResponse(
            url=f"{scheme}://auth?error=exchange_failed",
            status_code=302,
        )
    except Exception:
        return RedirectResponse(
            url=f"{scheme}://auth?error=internal",
            status_code=302,
        )

    return RedirectResponse(
        url=f"{scheme}://auth?token={session_token}",
        status_code=302,
    )


@router.post("/refresh", response_model=SessionResponse)
async def refresh(
    authorization: Annotated[str, Header()],
) -> SessionResponse:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorisation header")

    token = authorization.removeprefix("Bearer ")

    try:
        new_token = await auth_service.refresh_session(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=502, detail="Failed to contact Google")
    except Exception:
        raise HTTPException(status_code=500, detail="Token refresh failed")

    return SessionResponse(session_token=new_token)
