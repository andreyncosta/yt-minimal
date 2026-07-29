import os
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError
from jose import jwt as jose_jwt

import token_store

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_YOUTUBE_SCOPE = "openid https://www.googleapis.com/auth/youtube.readonly"
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRY_HOURS = 1
_JWT_REFRESH_GRACE_HOURS = 24  # allow refresh up to 24h after token expiry
_STATE_TTL_SECONDS = 600  # 10 minutes — window to complete the Google consent screen


def _fernet() -> Fernet:
    return Fernet(os.environ["FERNET_KEY"].encode())


def _create_session_jwt(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(hours=_JWT_EXPIRY_HOURS),
    }
    return jose_jwt.encode(payload, os.environ["JWT_SECRET_KEY"], algorithm=_JWT_ALGORITHM)


def _extract_user_id(id_token: str) -> str:
    """Extract sub claim from Google id_token without signature verification.

    Safe because id_token arrived directly from Google's token endpoint over TLS.
    """
    return jose_jwt.get_unverified_claims(id_token)["sub"]


def _sign_state() -> str:
    """Create a short-lived, signed anti-CSRF ``state`` token for the OAuth flow.

    Stateless by design: the JWT's own signature and ``exp`` claim are all that
    ``verify_state`` checks on callback, so no server-side session storage is
    needed between ``/auth/login`` and ``/auth/callback``. This closes a login
    CSRF gap where an attacker could otherwise drive a victim's client to
    ``/auth/callback`` with an authorization code the attacker controls,
    binding the victim's session to the attacker's Google account (see
    RFC 6749 §10.12).
    """
    now = datetime.now(timezone.utc)
    payload = {
        "purpose": "oauth_state",
        "nonce": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + timedelta(seconds=_STATE_TTL_SECONDS),
    }
    return jose_jwt.encode(payload, os.environ["JWT_SECRET_KEY"], algorithm=_JWT_ALGORITHM)


def verify_state(state: str | None) -> bool:
    """Verify a ``state`` value returned from Google was one we issued and
    hasn't expired. Never raises — any failure (missing, malformed, expired,
    bad signature, wrong purpose) is treated as a rejected OAuth attempt."""
    if not state:
        return False
    try:
        payload = jose_jwt.decode(
            state,
            os.environ["JWT_SECRET_KEY"],
            algorithms=[_JWT_ALGORITHM],
        )
    except JWTError:
        return False
    return payload.get("purpose") == "oauth_state"


def build_auth_url() -> str:
    params = {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "redirect_uri": os.environ["GOOGLE_REDIRECT_URI"],
        "response_type": "code",
        "scope": _YOUTUBE_SCOPE,
        "access_type": "offline",
        "prompt": "consent",  # ensures refresh_token is always returned
        "state": _sign_state(),
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
        payload = jose_jwt.decode(
            session_token,
            os.environ["JWT_SECRET_KEY"],
            algorithms=[_JWT_ALGORITHM],
            options={"verify_exp": False},
        )
    except JWTError as exc:
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
