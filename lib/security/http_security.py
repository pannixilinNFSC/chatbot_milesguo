import hashlib
import os
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from lib.app_logger import get_logger

logger = get_logger(__name__)

#
# Auth + CORS + Rate limiting utilities for HTTP endpoints.
# Keep security-related logic out of `main.py` so the app wiring stays readable.
#

# Simple Bearer token auth:
# - Set `API_AUTH_TOKEN` to enable auth.
# - If unset/empty, endpoints are accessible without auth (useful for local dev).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


def setup_cors(app) -> None:
    # Allow browser-based frontends to call this API.
    # Configure via `CORS_ALLOW_ORIGINS` (comma-separated) or "*" to allow all.
    cors_allow_origins = os.environ.get("CORS_ALLOW_ORIGINS", "*").strip()
    if cors_allow_origins == "*":
        cors_origins = ["*"]
    else:
        cors_origins = [o.strip() for o in cors_allow_origins.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _is_auth_enabled() -> bool:
    return bool(os.environ.get("API_AUTH_TOKEN", "").strip())


def _get_expected_token() -> str:
    return os.environ.get("API_AUTH_TOKEN", "").strip()


def require_auth(request: Request, token: str | None = Depends(oauth2_scheme)) -> None:
    if not _is_auth_enabled():
        return

    # Fallback for simple browser/manual testing: allow passing token via query string.
    # Motivation: a raw browser navigation can't set Authorization headers, but users
    # often want to quickly validate an endpoint. Prefer the Authorization header in
    # real clients because query strings can leak via logs/referrers.
    if not token:
        token = (request.query_params.get("token") or "").strip() or None

    # Optional fallback header for simpler tooling (non-standard).
    if not token:
        token = (request.headers.get("x-api-token") or "").strip() or None

    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    if token != _get_expected_token():
        raise HTTPException(status_code=401, detail="Invalid bearer token")


def _get_client_ip(request: Request) -> str:
    # Prefer X-Forwarded-For when behind proxies (Cloud Run / Cloud Functions).
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # Format: "client, proxy1, proxy2"
        first = xff.split(",")[0].strip()
        if first:
            return first
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _hash_token(token: str) -> str:
    # Avoid storing raw tokens as dict keys.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


class InMemoryRateLimiter:
    """
    In-memory sliding-window rate limiter.

    NOTE: In serverless / multi-instance environments, limits are enforced per instance.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._minute_hits: dict[str, deque[float]] = defaultdict(deque)
        self._hour_hits: dict[str, deque[float]] = defaultdict(deque)

    def _purge(self, q: deque[float], now: float, window_s: int) -> None:
        cutoff = now - window_s
        while q and q[0] <= cutoff:
            q.popleft()

    def check_and_hit(self, key: str, *, per_minute: int, per_hour: int) -> int | None:
        """
        Returns:
          - None if allowed (and records the hit)
          - retry_after seconds (int) if blocked
        """
        now = time.time()
        with self._lock:
            qm = self._minute_hits[key]
            qh = self._hour_hits[key]
            self._purge(qm, now, 60)
            self._purge(qh, now, 3600)

            if len(qm) >= per_minute:
                retry_after = int(max(1, 60 - (now - qm[0])))
                return retry_after
            if len(qh) >= per_hour:
                retry_after = int(max(1, 3600 - (now - qh[0])))
                return retry_after

            qm.append(now)
            qh.append(now)
            return None


rate_limiter = InMemoryRateLimiter()


def _get_rate_limit_config() -> tuple[int, int]:
    # Defaults match requested limits.
    per_minute = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "5"))
    per_hour = int(os.environ.get("RATE_LIMIT_PER_HOUR", "30"))
    return max(1, per_minute), max(1, per_hour)


def require_rate_limit(request: Request, token: str | None = Depends(oauth2_scheme)) -> None:
    # Don't rate-limit CORS preflight.
    if request.method.upper() == "OPTIONS":
        return

    per_minute, per_hour = _get_rate_limit_config()
    if token:
        key = f"token:{_hash_token(token)}"
    else:
        key = f"ip:{_get_client_ip(request)}"

    retry_after = rate_limiter.check_and_hit(key, per_minute=per_minute, per_hour=per_hour)
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler to log all unhandled exceptions.
    
    Motivation: Ensure all exceptions are logged with full stack traces
    for debugging in Cloud Run, even if they're not caught by endpoint handlers.
    """
    logger.error(
        "Unhandled exception: %s",
        exc,
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "query_params": str(request.query_params),
        }
    )
    # Handle HTTPException by returning the proper response
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    # For other exceptions, return a 500 error
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


