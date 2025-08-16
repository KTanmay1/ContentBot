"""Simple token-bucket rate limiting middleware (Developer A)."""
# Step 18: Implement a lightweight in-memory rate limiter for development/test.

from __future__ import annotations

import time
from typing import Callable, Awaitable, Dict, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


class TokenBucket:
    def __init__(self, capacity: int, refill_rate_per_sec: float):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens = capacity
        self.last_refill = time.monotonic()

    def consume(self, amount: int = 1) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.last_refill = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


class RateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, capacity: int = 10, refill_rate_per_sec: float = 5.0, key_header: str = "x-client-id"):
        super().__init__(app)
        self.capacity = capacity
        self.refill_rate_per_sec = refill_rate_per_sec
        self.key_header = key_header
        self.buckets: Dict[str, TokenBucket] = {}

    def _bucket_for(self, key: str) -> TokenBucket:
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(self.capacity, self.refill_rate_per_sec)
        return self.buckets[key]

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        key = request.headers.get(self.key_header, "anonymous")
        if not self._bucket_for(key).consume(1):
            return JSONResponse({"error": "rate_limited"}, status_code=429)
        return await call_next(request)


# Completed Step 18: Added RateLimitingMiddleware with token-bucket strategy.


