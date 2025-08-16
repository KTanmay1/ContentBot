"""Enhanced token-bucket rate limiting middleware for ViraLearn ContentBot."""

from __future__ import annotations

import time
from typing import Callable, Awaitable, Dict, Optional, Set

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from ...core.error_handling import RateLimitException, error_handler


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
    """Enhanced rate limiting middleware with per-endpoint and per-user limits."""
    
    def __init__(
        self, 
        app, 
        *, 
        default_capacity: int = 100,
        default_refill_rate_per_sec: float = 10.0,
        key_header: str = "x-client-id",
        exempt_paths: Optional[Set[str]] = None,
        endpoint_limits: Optional[Dict[str, Dict[str, float]]] = None,
        enable_user_tracking: bool = True
    ):
        super().__init__(app)
        self.default_capacity = default_capacity
        self.default_refill_rate_per_sec = default_refill_rate_per_sec
        self.key_header = key_header
        self.exempt_paths = exempt_paths or {"/health", "/docs", "/openapi.json", "/redoc"}
        self.endpoint_limits = endpoint_limits or {
            "/content/generate": {"capacity": 20, "refill_rate": 2.0},
            "/content/analyze": {"capacity": 50, "refill_rate": 5.0},
            "/content/plan": {"capacity": 30, "refill_rate": 3.0},
            "/content/assess-quality": {"capacity": 40, "refill_rate": 4.0}
        }
        self.enable_user_tracking = enable_user_tracking
        self.buckets: Dict[str, TokenBucket] = {}
        self.user_request_counts: Dict[str, Dict[str, int]] = {}  # user_id -> {endpoint: count}
        self.cleanup_interval = 3600  # 1 hour
        self.last_cleanup = time.monotonic()

    def _is_exempt_path(self, path: str) -> bool:
        """Check if the path is exempt from rate limiting."""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)

    def _get_endpoint_limits(self, path: str) -> tuple[int, float]:
        """Get capacity and refill rate for a specific endpoint."""
        for endpoint, limits in self.endpoint_limits.items():
            if path.startswith(endpoint):
                return limits["capacity"], limits["refill_rate"]
        return self.default_capacity, self.default_refill_rate_per_sec

    def _get_client_key(self, request: Request) -> str:
        """Generate a unique key for the client."""
        # Try to get authenticated user info first
        if hasattr(request.state, 'authenticated') and request.state.authenticated:
            if hasattr(request.state, 'api_key'):
                return f"api_key:{request.state.api_key[:8]}"  # Use first 8 chars for privacy
            return "authenticated_user"
        
        # Fall back to header-based identification
        client_id = request.headers.get(self.key_header)
        if client_id:
            return f"client:{client_id}"
        
        # Use IP address as last resort
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _bucket_for(self, key: str, path: str) -> TokenBucket:
        """Get or create a token bucket for the given key and path."""
        bucket_key = f"{key}:{path}"
        if bucket_key not in self.buckets:
            capacity, refill_rate = self._get_endpoint_limits(path)
            self.buckets[bucket_key] = TokenBucket(capacity, refill_rate)
        return self.buckets[bucket_key]

    def _track_user_request(self, user_key: str, endpoint: str):
        """Track user request for analytics and monitoring."""
        if not self.enable_user_tracking:
            return
            
        if user_key not in self.user_request_counts:
            self.user_request_counts[user_key] = {}
        
        if endpoint not in self.user_request_counts[user_key]:
            self.user_request_counts[user_key][endpoint] = 0
            
        self.user_request_counts[user_key][endpoint] += 1

    def _cleanup_old_buckets(self):
        """Clean up old, unused token buckets to prevent memory leaks."""
        now = time.monotonic()
        if now - self.last_cleanup < self.cleanup_interval:
            return
            
        # Remove buckets that haven't been used recently
        cutoff_time = now - self.cleanup_interval
        buckets_to_remove = []
        
        for key, bucket in self.buckets.items():
            if bucket.last_refill < cutoff_time:
                buckets_to_remove.append(key)
        
        for key in buckets_to_remove:
            del self.buckets[key]
            
        self.last_cleanup = now

    def _get_rate_limit_headers(self, bucket: TokenBucket, capacity: int) -> Dict[str, str]:
        """Generate rate limit headers for the response."""
        remaining = max(0, int(bucket.tokens))
        reset_time = int(time.time() + (capacity - bucket.tokens) / bucket.refill_rate)
        
        return {
            "X-RateLimit-Limit": str(capacity),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time)
        }

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process rate limiting for incoming requests."""
        try:
            # Skip rate limiting for exempt paths
            if self._is_exempt_path(request.url.path):
                return await call_next(request)

            # Clean up old buckets periodically
            self._cleanup_old_buckets()

            # Get client identifier
            client_key = self._get_client_key(request)
            path = request.url.path
            
            # Get the appropriate bucket
            bucket = self._bucket_for(client_key, path)
            capacity, _ = self._get_endpoint_limits(path)
            
            # Check if request can be processed
            if not bucket.consume(1):
                # Track the rate limit violation
                await error_handler.handle_error(
                    RateLimitException(f"Rate limit exceeded for {client_key}"),
                    {
                        "client_key": client_key,
                        "path": path,
                        "method": request.method
                    }
                )
                
                # Return rate limit error with headers
                headers = self._get_rate_limit_headers(bucket, capacity)
                return JSONResponse(
                    {
                        "error": "Rate limit exceeded",
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Too many requests. Try again later.",
                        "retry_after": headers["X-RateLimit-Reset"]
                    },
                    status_code=429,
                    headers=headers
                )
            
            # Track the successful request
            self._track_user_request(client_key, path)
            
            # Process the request
            response = await call_next(request)
            
            # Add rate limit headers to successful responses
            rate_limit_headers = self._get_rate_limit_headers(bucket, capacity)
            for header_name, header_value in rate_limit_headers.items():
                response.headers[header_name] = header_value
            
            return response
            
        except Exception as e:
            await error_handler.handle_error(e, {"middleware": "rate_limiting", "path": request.url.path})
            # In case of error, allow the request to proceed to avoid blocking legitimate traffic
            return await call_next(request)

    def get_user_stats(self, user_key: str) -> Dict[str, int]:
        """Get request statistics for a specific user."""
        return self.user_request_counts.get(user_key, {})

    def reset_user_limits(self, user_key: str):
        """Reset rate limits for a specific user (admin function)."""
        buckets_to_reset = [key for key in self.buckets.keys() if key.startswith(f"{user_key}:")]
        for bucket_key in buckets_to_reset:
            if bucket_key in self.buckets:
                capacity, refill_rate = self._get_endpoint_limits(bucket_key.split(":", 1)[1])
                self.buckets[bucket_key] = TokenBucket(capacity, refill_rate)


# Completed Step 18: Added RateLimitingMiddleware with token-bucket strategy.