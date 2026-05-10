import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from limiter import limiter
from middleware.security import SecurityHeadersMiddleware
from routers import audio, auth, feed

load_dotenv()

app = FastAPI(title="YT Minimal API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — origin list comes exclusively from ENV; empty list blocks all origins
_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Security headers (must be added after CORS so it wraps the full response)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth.router)
app.include_router(feed.router)
app.include_router(audio.router)


@app.get("/health")
@limiter.limit("60/minute")
async def health(request: Request) -> dict[str, str]:
    return {"status": "ok"}
