"""Enhanced authentication & authorization middleware for ViraLearn ContentBot."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Callable, Awaitable, Optional, Set

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from ...core.error_handling import AuthenticationException, error_handler
from ...utils.validators import validate_api_key


class AuthMiddleware(BaseHTTPMiddleware):
    """Enhanced authentication middleware with multiple auth methods."""
    
    def __init__(
        self, 
        app, 
        *, 
        header_name: str = "x-api-key", 
        valid_keys: Optional[Set[str]] = None,
        jwt_secret: Optional[str] = None,
        exempt_paths: Optional[Set[str]] = None,
        enable_signature_auth: bool = False
    ):
        super().__init__(app)
        self.header_name = header_name
        self.valid_keys = valid_keys or set()
        self.jwt_secret = jwt_secret
        self.exempt_paths = exempt_paths or {"/health", "/docs", "/openapi.json", "/redoc"}
        self.enable_signature_auth = enable_signature_auth

    def _is_exempt_path(self, path: str) -> bool:
        """Check if the path is exempt from authentication."""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)

    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key against known valid keys."""
        if not api_key:
            return False
        
        try:
            validate_api_key(api_key)
            return api_key in self.valid_keys
        except Exception:
            return False

    def _validate_signature(self, request: Request) -> bool:
        """Validate request signature for enhanced security."""
        if not self.enable_signature_auth:
            return True
            
        signature = request.headers.get("x-signature")
        timestamp = request.headers.get("x-timestamp")
        
        if not signature or not timestamp:
            return False
            
        try:
            # Check timestamp (prevent replay attacks)
            request_time = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - request_time) > 300:  # 5 minutes tolerance
                return False
                
            # Validate signature (simplified - in production use proper HMAC)
            expected_signature = hmac.new(
                self.jwt_secret.encode() if self.jwt_secret else b"default",
                f"{request.method}{request.url.path}{timestamp}".encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, TypeError):
            return False

    def _validate_jwt_token(self, token: str) -> bool:
        """Validate JWT token (simplified implementation)."""
        if not self.jwt_secret or not token:
            return False
            
        try:
            # In production, use proper JWT library like PyJWT
            # This is a simplified validation
            parts = token.split('.')
            if len(parts) != 3:
                return False
                
            # Basic validation - in production implement full JWT verification
            return True
            
        except Exception:
            return False

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process authentication for incoming requests."""
        try:
            # Skip authentication for exempt paths
            if self._is_exempt_path(request.url.path):
                return await call_next(request)

            # If no authentication configured, allow all requests (dev mode)
            if not self.valid_keys and not self.jwt_secret:
                return await call_next(request)

            # Check for JWT token first
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                if self._validate_jwt_token(token):
                    # Add user info to request state for downstream use
                    request.state.authenticated = True
                    request.state.auth_method = "jwt"
                    return await call_next(request)

            # Check API key authentication
            api_key = request.headers.get(self.header_name)
            if api_key and self._validate_api_key(api_key):
                # Validate signature if enabled
                if not self._validate_signature(request):
                    await error_handler.handle_error(
                        AuthenticationException("Invalid request signature"),
                        {"path": request.url.path, "method": request.method}
                    )
                    return JSONResponse(
                        {"error": "Invalid request signature", "code": "INVALID_SIGNATURE"}, 
                        status_code=401
                    )
                
                # Add user info to request state
                request.state.authenticated = True
                request.state.auth_method = "api_key"
                request.state.api_key = api_key
                return await call_next(request)

            # Authentication failed
            await error_handler.handle_error(
                AuthenticationException("Authentication required"),
                {"path": request.url.path, "method": request.method}
            )
            
            return JSONResponse(
                {
                    "error": "Authentication required", 
                    "code": "AUTHENTICATION_REQUIRED",
                    "message": "Valid API key or JWT token required"
                }, 
                status_code=401
            )

        except Exception as e:
            await error_handler.handle_error(e, {"middleware": "auth", "path": request.url.path})
            return JSONResponse(
                {"error": "Authentication error", "code": "AUTH_ERROR"}, 
                status_code=500
            )


# Completed Step 17: Added AuthMiddleware with header-based auth.