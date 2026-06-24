from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Disallow embedding in frames (clickjacking protection)
        response.headers["X-Frame-Options"] = "DENY"

        # Force HTTPS for 2 years, including subdomains
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )

        # Restrict resource loading to same origin; allow Google OAuth and YouTube API
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "connect-src 'self' https://accounts.google.com https://www.googleapis.com; "
            "frame-ancestors 'none'; "
            "form-action 'self'"
        )

        # Do not send Referer header to cross-origin destinations
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser feature access
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        return response

