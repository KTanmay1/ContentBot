"""Enhanced request/response logging middleware for ViraLearn ContentBot."""

from __future__ import annotations

import json
import time
import uuid
from typing import Callable, Awaitable, Dict, Any, Optional, Set

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ...core.monitoring import get_monitoring
from ...core.error_handling import error_handler


class LoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced logging middleware with structured logging and performance tracking."""
    
    def __init__(
        self,
        app,
        *,
        log_requests: bool = True,
        log_responses: bool = True,
        log_request_body: bool = False,
        log_response_body: bool = False,
        sensitive_headers: Optional[Set[str]] = None,
        exempt_paths: Optional[Set[str]] = None,
        max_body_size: int = 1024,  # Max body size to log in bytes
        enable_performance_tracking: bool = True
    ):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.sensitive_headers = sensitive_headers or {
            "authorization", "x-api-key", "cookie", "x-auth-token"
        }
        self.exempt_paths = exempt_paths or {"/health", "/metrics"}
        self.max_body_size = max_body_size
        self.enable_performance_tracking = enable_performance_tracking
        self.request_counts: Dict[str, int] = {}
        self.response_times: Dict[str, list] = {}

    def _should_log_path(self, path: str) -> bool:
        """Check if the path should be logged."""
        return not any(path.startswith(exempt) for exempt in self.exempt_paths)

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive information from headers."""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized

    async def _get_request_body(self, request: Request) -> Optional[str]:
        """Safely extract request body for logging."""
        if not self.log_request_body:
            return None
            
        try:
            body = await request.body()
            if len(body) > self.max_body_size:
                return f"[BODY TOO LARGE: {len(body)} bytes]"
            
            # Try to decode as text
            try:
                body_text = body.decode('utf-8')
                # Try to parse as JSON for better formatting
                try:
                    json_body = json.loads(body_text)
                    return json.dumps(json_body, indent=2)
                except json.JSONDecodeError:
                    return body_text
            except UnicodeDecodeError:
                return f"[BINARY CONTENT: {len(body)} bytes]"
                
        except Exception:
            return "[ERROR READING BODY]"

    def _get_response_body(self, response: Response) -> Optional[str]:
        """Safely extract response body for logging."""
        if not self.log_response_body:
            return None
            
        try:
            # This is a simplified implementation
            # In production, you might need to handle streaming responses differently
            if hasattr(response, 'body') and response.body:
                body = response.body
                if len(body) > self.max_body_size:
                    return f"[BODY TOO LARGE: {len(body)} bytes]"
                
                try:
                    body_text = body.decode('utf-8')
                    try:
                        json_body = json.loads(body_text)
                        return json.dumps(json_body, indent=2)
                    except json.JSONDecodeError:
                        return body_text
                except UnicodeDecodeError:
                    return f"[BINARY CONTENT: {len(body)} bytes]"
            return None
        except Exception:
            return "[ERROR READING RESPONSE BODY]"

    def _track_performance_metrics(self, path: str, method: str, duration_ms: int, status_code: int):
        """Track performance metrics for analytics."""
        if not self.enable_performance_tracking:
            return
            
        endpoint_key = f"{method}:{path}"
        
        # Track request counts
        if endpoint_key not in self.request_counts:
            self.request_counts[endpoint_key] = 0
        self.request_counts[endpoint_key] += 1
        
        # Track response times
        if endpoint_key not in self.response_times:
            self.response_times[endpoint_key] = []
        
        # Keep only last 100 response times to prevent memory growth
        self.response_times[endpoint_key].append(duration_ms)
        if len(self.response_times[endpoint_key]) > 100:
            self.response_times[endpoint_key] = self.response_times[endpoint_key][-100:]

    def _generate_request_id(self) -> str:
        """Generate a unique request ID for tracking."""
        return str(uuid.uuid4())[:8]

    def _get_client_info(self, request: Request) -> Dict[str, Any]:
        """Extract client information from request."""
        client_info = {
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        # Add authenticated user info if available
        if hasattr(request.state, 'authenticated') and request.state.authenticated:
            client_info["authenticated"] = True
            client_info["auth_method"] = getattr(request.state, 'auth_method', 'unknown')
        else:
            client_info["authenticated"] = False
            
        return client_info

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process logging for incoming requests and responses."""
        # Skip logging for exempt paths
        if not self._should_log_path(request.url.path):
            return await call_next(request)
            
        # Generate request ID and start timing
        request_id = self._generate_request_id()
        start_time = time.time()
        
        # Get workflow ID from headers or generate one
        workflow_id = request.headers.get("x-workflow-id") or f"req_{request_id}"
        mon = get_monitoring(workflow_id)
        
        # Add request ID to request state for downstream use
        request.state.request_id = request_id
        
        try:
            # Log request information
            if self.log_requests:
                client_info = self._get_client_info(request)
                request_body = await self._get_request_body(request)
                
                request_data = {
                    "request_id": request_id,
                    "workflow_id": workflow_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "headers": self._sanitize_headers(dict(request.headers)),
                    "client": client_info,
                    "timestamp": time.time()
                }
                
                if request_body:
                    request_data["body"] = request_body
                
                mon.info("http_request", **request_data)
            
            # Process the request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log response information
            if self.log_responses:
                response_body = self._get_response_body(response)
                
                response_data = {
                    "request_id": request_id,
                    "workflow_id": workflow_id,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "response_headers": dict(response.headers),
                    "timestamp": time.time()
                }
                
                if response_body:
                    response_data["body"] = response_body
                
                mon.info("http_response", **response_data)
            
            # Track performance metrics
            self._track_performance_metrics(
                request.url.path, 
                request.method, 
                duration_ms, 
                response.status_code
            )
            
            # Add request ID to response headers for client tracking
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log the error
            duration_ms = int((time.time() - start_time) * 1000)
            
            error_data = {
                "request_id": request_id,
                "workflow_id": workflow_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "error_type": type(e).__name__,
                "duration_ms": duration_ms,
                "timestamp": time.time()
            }
            
            mon.error("http_request_error", **error_data)
            
            # Handle the error through the error handler
            await error_handler.handle_error(e, {
                "middleware": "logging",
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method
            })
            
            # Re-raise the exception
            raise

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all endpoints."""
        stats = {}
        
        for endpoint, times in self.response_times.items():
            if times:
                stats[endpoint] = {
                    "request_count": self.request_counts.get(endpoint, 0),
                    "avg_response_time_ms": sum(times) / len(times),
                    "min_response_time_ms": min(times),
                    "max_response_time_ms": max(times),
                    "recent_requests": len(times)
                }
        
        return stats

    def reset_performance_stats(self):
        """Reset performance statistics."""
        self.request_counts.clear()
        self.response_times.clear()


# Completed Step 19: Added LoggingMiddleware with request/response events.