"""FastAPI application factory (Developer A)."""
# Step 16: Implement app factory with CORS, logging, rate limiting, and auth middleware.
# Why: Provides a clean separation of concerns and allows for easy testing and configuration.

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from src.api.middleware.auth import AuthMiddleware
from src.api.middleware.logging import LoggingMiddleware
from src.api.middleware.rate_limiting import RateLimitingMiddleware
from src.api.routers import monitoring, workflows
from src.core.error_handling import exception_to_payload
from src.core.monitoring import get_monitoring


def create_app(
    *,
    cors_origins: list[str] | None = None,
    auth_key: str | None = None,
    rate_limit_capacity: int = 10,
    rate_limit_refill_rate: float = 5.0,
) -> FastAPI:
    """Create and configure the FastAPI application.
    
    Args:
        cors_origins: List of allowed CORS origins. Defaults to ["*"] if None.
        auth_key: API key for authentication. If None, auth is disabled.
        rate_limit_capacity: Token bucket capacity for rate limiting.
        rate_limit_refill_rate: Token refill rate per second.
    
    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="ContentBot API",
        description="AI-powered content generation and workflow management",
        version="1.0.0",
    )

    # CORS middleware
    if cors_origins is None:
        cors_origins = ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware (order matters - last added is executed first)
    app.add_middleware(
        AuthMiddleware,
        header_name="x-api-key",
        valid_keys={auth_key} if auth_key else set(),
    )
    app.add_middleware(
        RateLimitingMiddleware,
        capacity=rate_limit_capacity,
        refill_rate_per_sec=rate_limit_refill_rate,
        key_header="x-client-id",
    )
    app.add_middleware(LoggingMiddleware)

    # Include routers
    app.include_router(monitoring.router)
    app.include_router(workflows.router)

    # Root endpoint
    @app.get("/")
    def root() -> Dict[str, str]:
        return {"message": "ContentBot API is running"}

    # Health check endpoint (also available at /api/v1/health)
    @app.get("/health")
    def health_check() -> Dict[str, str]:
        return {"status": "healthy"}

    return app


def add_exception_handlers(app: FastAPI) -> None:
    """Add global exception handlers to the FastAPI app."""
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all unhandled exceptions with structured logging and response."""
        workflow_id = request.headers.get("x-workflow-id")
        mon = get_monitoring(workflow_id)
        
        # Log the error with full context
        mon.error(
            "unhandled_exception",
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            request_method=request.method,
            request_path=str(request.url.path),
            request_headers=dict(request.headers),
        )
        
        # Convert exception to safe payload for response
        error_payload = exception_to_payload(exc)
        
        # Return standardized error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "details": error_payload,
            },
        )


# Create default app instance
app = create_app()
add_exception_handlers(app)


# Completed Phase 3 API integration.