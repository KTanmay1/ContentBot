"""Authentication & authorization middleware (Developer A)."""
# Step 17: Provide a simple header-based auth middleware placeholder.

from __future__ import annotations

from typing import Callable, Awaitable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, header_name: str = "x-api-key", valid_key: str | None = None):
        super().__init__(app)
        self.header_name = header_name
        self.valid_key = valid_key

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # If no key configured, allow all requests (dev/test mode)
        if not self.valid_key:
            return await call_next(request)

        api_key = request.headers.get(self.header_name)
        if api_key != self.valid_key:
            return JSONResponse({"error": "unauthorized"}, status_code=401)

        return await call_next(request)


# Completed Step 17: Added AuthMiddleware with header-based auth.


