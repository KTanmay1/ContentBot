"""Request/response logging middleware (Developer A)."""
# Step 19: Implement lightweight logging middleware reusing core monitoring.

from __future__ import annotations

import time
from typing import Callable, Awaitable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.core.monitoring import get_monitoring


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start = time.time()
        workflow_id = request.headers.get("x-workflow-id")
        mon = get_monitoring(workflow_id)
        mon.info("http_request", method=request.method, path=request.url.path)
        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)
        mon.info("http_response", status_code=response.status_code, duration_ms=duration_ms)
        return response


# Completed Step 19: Added LoggingMiddleware with request/response events.


