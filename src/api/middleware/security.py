"""Security headers middleware for ViraLearn ContentBot."""

from __future__ import annotations

from typing import Callable, Awaitable, Dict, Optional, List

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ...core.error_handling import error_handler


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""
    
    def __init__(
        self,
        app,
        *,
        # Content Security Policy
        csp_policy: Optional[str] = None,
        # HTTP Strict Transport Security
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        # X-Frame-Options
        frame_options: str = "DENY",
        # X-Content-Type-Options
        content_type_options: bool = True,
        # Referrer Policy
        referrer_policy: str = "strict-origin-when-cross-origin",
        # Permissions Policy
        permissions_policy: Optional[str] = None,
        # Custom headers
        custom_headers: Optional[Dict[str, str]] = None,
        # Development mode
        development_mode: bool = False
    ):
        super().__init__(app)
        
        self.development_mode = development_mode
        
        # Default CSP for API
        if csp_policy is None:
            if development_mode:
                # More permissive CSP for development
                self.csp_policy = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: https:; "
                    "connect-src 'self' ws: wss:; "
                    "font-src 'self' data:; "
                    "object-src 'none'; "
                    "base-uri 'self';"
                )
            else:
                # Strict CSP for production API
                self.csp_policy = (
                    "default-src 'none'; "
                    "script-src 'self'; "
                    "style-src 'self'; "
                    "img-src 'self' data:; "
                    "connect-src 'self'; "
                    "font-src 'self'; "
                    "object-src 'none'; "
                    "base-uri 'self'; "
                    "form-action 'self'; "
                    "frame-ancestors 'none';"
                )
        else:
            self.csp_policy = csp_policy
            
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.referrer_policy = referrer_policy
        
        # Default permissions policy for API
        if permissions_policy is None:
            self.permissions_policy = (
                "accelerometer=(), "
                "camera=(), "
                "geolocation=(), "
                "gyroscope=(), "
                "magnetometer=(), "
                "microphone=(), "
                "payment=(), "
                "usb=()"
            )
        else:
            self.permissions_policy = permissions_policy
            
        self.custom_headers = custom_headers or {}
        
        # Additional security headers
        self.security_headers = {
            "X-XSS-Protection": "1; mode=block",
            "X-Download-Options": "noopen",
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin"
        }
        
        # Adjust for development mode
        if development_mode:
            # Relax some policies for development
            self.security_headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
            self.security_headers["Cross-Origin-Resource-Policy"] = "cross-origin"

    def _build_hsts_header(self) -> str:
        """Build the HSTS header value."""
        hsts_value = f"max-age={self.hsts_max_age}"
        
        if self.hsts_include_subdomains:
            hsts_value += "; includeSubDomains"
            
        if self.hsts_preload:
            hsts_value += "; preload"
            
        return hsts_value

    def _should_add_hsts(self, request: Request) -> bool:
        """Determine if HSTS header should be added."""
        # Only add HSTS for HTTPS requests
        return request.url.scheme == "https"

    def _get_security_headers(self, request: Request) -> Dict[str, str]:
        """Get all security headers for the response."""
        headers = {}
        
        # Content Security Policy
        if self.csp_policy:
            headers["Content-Security-Policy"] = self.csp_policy
            
        # HTTP Strict Transport Security (only for HTTPS)
        if self._should_add_hsts(request):
            headers["Strict-Transport-Security"] = self._build_hsts_header()
            
        # X-Frame-Options
        if self.frame_options:
            headers["X-Frame-Options"] = self.frame_options
            
        # X-Content-Type-Options
        if self.content_type_options:
            headers["X-Content-Type-Options"] = "nosniff"
            
        # Referrer Policy
        if self.referrer_policy:
            headers["Referrer-Policy"] = self.referrer_policy
            
        # Permissions Policy
        if self.permissions_policy:
            headers["Permissions-Policy"] = self.permissions_policy
            
        # Additional security headers
        headers.update(self.security_headers)
        
        # Custom headers
        headers.update(self.custom_headers)
        
        return headers

    def _add_server_header(self, headers: Dict[str, str]):
        """Add or modify server header for security."""
        # Remove or obfuscate server information
        headers["Server"] = "ViraLearn-API"

    def _add_cache_headers(self, headers: Dict[str, str], request: Request):
        """Add appropriate cache headers for API responses."""
        # For API endpoints, generally disable caching for security
        if request.url.path.startswith("/api/"):
            headers.update({
                "Cache-Control": "no-store, no-cache, must-revalidate, private",
                "Pragma": "no-cache",
                "Expires": "0"
            })
        # For static content, allow caching with validation
        elif request.url.path.startswith("/static/"):
            headers["Cache-Control"] = "public, max-age=3600, must-revalidate"

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Add security headers to the response."""
        try:
            # Process the request
            response = await call_next(request)
            
            # Get security headers
            security_headers = self._get_security_headers(request)
            
            # Add server header
            self._add_server_header(security_headers)
            
            # Add cache headers
            self._add_cache_headers(security_headers, request)
            
            # Apply all headers to the response
            for header_name, header_value in security_headers.items():
                response.headers[header_name] = header_value
            
            # Remove potentially sensitive headers
            sensitive_headers = ["X-Powered-By", "X-AspNet-Version", "X-AspNetMvc-Version"]
            for header in sensitive_headers:
                if header in response.headers:
                    del response.headers[header]
            
            return response
            
        except Exception as e:
            await error_handler.handle_error(e, {
                "middleware": "security_headers",
                "path": request.url.path,
                "method": request.method
            })
            # In case of error, still try to add basic security headers
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            return response

    def update_csp_policy(self, new_policy: str):
        """Update the Content Security Policy."""
        self.csp_policy = new_policy

    def add_custom_header(self, name: str, value: str):
        """Add a custom security header."""
        self.custom_headers[name] = value

    def remove_custom_header(self, name: str):
        """Remove a custom security header."""
        self.custom_headers.pop(name, None)

    def get_configuration(self) -> dict:
        """Get current security configuration."""
        return {
            "csp_policy": self.csp_policy,
            "hsts_max_age": self.hsts_max_age,
            "hsts_include_subdomains": self.hsts_include_subdomains,
            "hsts_preload": self.hsts_preload,
            "frame_options": self.frame_options,
            "content_type_options": self.content_type_options,
            "referrer_policy": self.referrer_policy,
            "permissions_policy": self.permissions_policy,
            "custom_headers": self.custom_headers,
            "development_mode": self.development_mode
        }


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size for security."""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Check request size before processing."""
        try:
            # Check Content-Length header
            content_length = request.headers.get("content-length")
            if content_length:
                if int(content_length) > self.max_size:
                    from starlette.responses import JSONResponse
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "Request entity too large",
                            "max_size": self.max_size,
                            "received_size": int(content_length)
                        }
                    )
            
            return await call_next(request)
            
        except Exception as e:
            await error_handler.handle_error(e, {
                "middleware": "request_size",
                "path": request.url.path,
                "content_length": request.headers.get("content-length")
            })
            return await call_next(request)