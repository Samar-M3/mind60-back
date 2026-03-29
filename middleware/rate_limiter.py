"""
Lightweight in-memory rate limiter (per-IP, per-minute).
Suitable for local dev; replace with Redis in production.
"""
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self.hits: Dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        q = self.hits[client_ip]
        while q and now - q[0] > self.window:
            q.popleft()

        if len(q) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests, please slow down."},
            )

        q.append(now)
        return await call_next(request)

