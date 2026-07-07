from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def user_or_ip_key(request: Request) -> str:
    """Rate-limit key: user_id when the auth dependency has run, IP otherwise."""
    user_id: str | None = getattr(request.state, "user_id", None)
    return user_id if user_id else get_remote_address(request)


limiter = Limiter(key_func=user_or_ip_key, default_limits=["60/minute"])
