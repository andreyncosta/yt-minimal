import os
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from cryptography.fernet import Fernet, InvalidToken
from jwt.exceptions import InvalidTokenError

import token_store

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_YOUTUBE_SCOPE = "openid https://www.googleapis.com/auth/youtube.readonly"
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRY_HOURS = 1
_JWT_REFRESH_GRACE_HOURS = 24  # allow refresh up to 24h after token expiry


def _fernet() -> Fernet:
    return Fernet(os.environ["FERNET_KEY"].encode())


def _create_session_jwt(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(hours=_JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, os.environ["JWT_SECRET_KEY"], algorithm=_JWT_ALGORITHM)


def _extract_user_id(id_token: str) -> str:
    """Extract sub claim from Google id_token without signature verification.

    Safe because id_token arrived directly from Google's token endpoint over TLS.
    """
    return jwt.decode(id_token, options={"verify_signature": False})["sub"]


def build_auth_url() -> str:
    params = {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "redirect_uri": os.environ["GOOGLE_REDIRECT_URI"],
        "response_type": "code",
        "scope": _YOUTUBE_SCOPE,
        "access_type": "offline",
        "prompt": "consent",  # ensures refresh_token is always returned
    }
    return f"{_GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


async def _call_google_refresh(user_id: str) -> dict:
    """Exchange the stored encrypted refresh_token for a fresh Google token set.

    Persists a rotated refresh_token when Google returns one. Deletes the stored
    token and raises ValueError if Google reports the session as revoked (HTTP 400).
    """
    encrypted = token_store.get_token(user_id)
    if encrypted is None:
        raise ValueError("No session found — please log in again")

    try:
        refresh_token = _fernet().decrypt(encrypted).decode()
    except InvalidToken as exc:
        raise ValueError("Corrupted session — please log in again") from exc

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "client_id": os.environ["GOOGLE_CLIENT_ID"],
                "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        if resp.status_code == 400:
            token_store.delete_token(user_id)
            raise ValueError("Google session expired — please log in again")
        resp.raise_for_status()
        new_tokens: dict = resp.json()

    if "refresh_token" in new_tokens:
        new_encrypted = _fernet().encrypt(new_tokens["refresh_token"].encode())
        token_store.save_token(user_id, new_encrypted)

    return new_tokens


async def exchange_code(code: str) -> str:
    """Exchange an OAuth authorization code for tokens; persist encrypted
    refresh_token and return a signed session JWT."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": os.environ["GOOGLE_CLIENT_ID"],
                "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                "redirect_uri": os.environ["GOOGLE_REDIRECT_URI"],
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        tokens: dict = resp.json()

    user_id = _extract_user_id(tokens["id_token"])
    encrypted = _fernet().encrypt(tokens["refresh_token"].encode())
    token_store.save_token(user_id, encrypted)

    return _create_session_jwt(user_id)


async def refresh_session(session_token: str) -> str:
    """Verify the session JWT signature and enforce a grace-period cap, then
    confirm the Google session is still active and return a new session JWT."""
    try:
        payload = jwt.decode(
            session_token,
            os.environ["JWT_SECRET_KEY"],
            algorithms=[_JWT_ALGORITHM],
            options={"verify_exp": False},
        )
    except InvalidTokenError as exc:
        raise ValueError("Invalid session token") from exc

    exp_timestamp = payload.get("exp")
    if exp_timestamp is not None:
        exp_dt = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        if datetime.now(timezone.utc) > exp_dt + timedelta(hours=_JWT_REFRESH_GRACE_HOURS):
            raise ValueError("Session expired — please log in again")

    user_id: str = payload["sub"]
    await _call_google_refresh(user_id)
    return _create_session_jwt(user_id)


async def get_access_token(user_id: str) -> str:
    """Return a fresh Google access_token for the given user_id."""
    tokens = await _call_google_refresh(user_id)
    return tokens["access_token"]
