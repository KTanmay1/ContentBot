"""CORS (Cross-Origin Resource Sharing) middleware for ViraLearn ContentBot."""

from __future__ import annotations

from typing import Callable, Awaitable, Set, Optional, List

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, PlainTextResponse

from ...core.error_handling import error_handler


class CORSMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with configurable policies."""
    
    def __init__(
        self,
        app,
        *,
        allow_origins: Optional[List[str]] = None,
        allow_methods: Optional[List[str]] = None,
        allow_headers: Optional[List[str]] = None,
        allow_credentials: bool = False,
        expose_headers: Optional[List[str]] = None,
        max_age: int = 600,
        allow_origin_regex: Optional[str] = None,
        development_mode: bool = False
    ):
        super().__init__(app)
        
        # Default configurations
        if development_mode:
            # Permissive settings for development
            self.allow_origins = ["*"]
            self.allow_methods = ["*"]
            self.allow_headers = ["*"]
            self.allow_credentials = False
        else:
            # Production-safe defaults
            self.allow_origins = allow_origins or []
            self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
            self.allow_headers = allow_headers or [
                "Accept",
                "Accept-Language",
                "Content-Language",
                "Content-Type",
                "Authorization",
                "X-API-Key",
                "X-Requested-With",
                "X-Workflow-ID",
                "X-Client-ID"
            ]
            self.allow_credentials = allow_credentials
        
        self.expose_headers = expose_headers or [
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ]
        self.max_age = max_age
        self.allow_origin_regex = allow_origin_regex
        
        # Convert to sets for faster lookup
        self.allow_origins_set = set(self.allow_origins) if self.allow_origins != ["*"] else None
        self.allow_methods_set = set(self.allow_methods) if self.allow_methods != ["*"] else None
        self.allow_headers_set = set(h.lower() for h in self.allow_headers) if self.allow_headers != ["*"] else None

    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if the origin is allowed."""
        if self.allow_origins == ["*"]:
            return True
            
        if self.allow_origins_set and origin in self.allow_origins_set:
            return True
            
        # Check regex pattern if configured
        if self.allow_origin_regex:
            import re
            try:
                return bool(re.match(self.allow_origin_regex, origin))
            except re.error:
                return False
                
        return False

    def _is_method_allowed(self, method: str) -> bool:
        """Check if the method is allowed."""
        if self.allow_methods == ["*"]:
            return True
        return self.allow_methods_set and method.upper() in self.allow_methods_set

    def _are_headers_allowed(self, headers: List[str]) -> bool:
        """Check if all requested headers are allowed."""
        if self.allow_headers == ["*"]:
            return True
            
        if not self.allow_headers_set:
            return False
            
        requested_headers = set(h.lower() for h in headers)
        return requested_headers.issubset(self.allow_headers_set)

    def _add_cors_headers(self, response: Response, origin: str, request_method: str = None) -> Response:
        """Add CORS headers to the response."""
        # Add origin header
        if self.allow_origins == ["*"] and not self.allow_credentials:
            response.headers["Access-Control-Allow-Origin"] = "*"
        elif self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            
        # Add credentials header
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
            
        # Add methods header for preflight
        if request_method == "OPTIONS":
            if self.allow_methods == ["*"]:
                response.headers["Access-Control-Allow-Methods"] = "*"
            else:
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
                
            # Add headers header for preflight
            if self.allow_headers == ["*"]:
                response.headers["Access-Control-Allow-Headers"] = "*"
            else:
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
                
            # Add max age header
            response.headers["Access-Control-Max-Age"] = str(self.max_age)
            
        # Add expose headers
        if self.expose_headers:
            response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
            
        return response

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process CORS for incoming requests."""
        try:
            origin = request.headers.get("origin")
            
            # Handle preflight requests
            if request.method == "OPTIONS":
                # Check if this is a CORS preflight request
                if origin and request.headers.get("access-control-request-method"):
                    requested_method = request.headers.get("access-control-request-method")
                    requested_headers = request.headers.get("access-control-request-headers", "")
                    requested_headers_list = [h.strip() for h in requested_headers.split(",") if h.strip()]
                    
                    # Validate the preflight request
                    if not self._is_origin_allowed(origin):
                        return PlainTextResponse("CORS: Origin not allowed", status_code=403)
                        
                    if not self._is_method_allowed(requested_method):
                        return PlainTextResponse("CORS: Method not allowed", status_code=403)
                        
                    if requested_headers_list and not self._are_headers_allowed(requested_headers_list):
                        return PlainTextResponse("CORS: Headers not allowed", status_code=403)
                    
                    # Create preflight response
                    response = PlainTextResponse("", status_code=200)
                    return self._add_cors_headers(response, origin, "OPTIONS")
            
            # Process the actual request
            response = await call_next(request)
            
            # Add CORS headers to the response if origin is present
            if origin:
                if self._is_origin_allowed(origin):
                    response = self._add_cors_headers(response, origin, request.method)
                else:
                    # Origin not allowed, but we still process the request
                    # This follows the CORS specification
                    pass
            
            return response
            
        except Exception as e:
            await error_handler.handle_error(e, {
                "middleware": "cors",
                "origin": request.headers.get("origin"),
                "method": request.method,
                "path": request.url.path
            })
            # In case of error, allow the request to proceed
            return await call_next(request)

    def add_allowed_origin(self, origin: str):
        """Dynamically add an allowed origin."""
        if self.allow_origins != ["*"]:
            if origin not in self.allow_origins:
                self.allow_origins.append(origin)
                self.allow_origins_set = set(self.allow_origins)

    def remove_allowed_origin(self, origin: str):
        """Dynamically remove an allowed origin."""
        if self.allow_origins != ["*"] and origin in self.allow_origins:
            self.allow_origins.remove(origin)
            self.allow_origins_set = set(self.allow_origins)

    def get_configuration(self) -> dict:
        """Get current CORS configuration."""
        return {
            "allow_origins": self.allow_origins,
            "allow_methods": self.allow_methods,
            "allow_headers": self.allow_headers,
            "allow_credentials": self.allow_credentials,
            "expose_headers": self.expose_headers,
            "max_age": self.max_age,
            "allow_origin_regex": self.allow_origin_regex
        }