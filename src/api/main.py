"""FastAPI application factory and main entry point (Developer A)."""
# Step 15: Implement FastAPI app factory to wire routers and middleware.
# Why: Completes Phase 3 API integration layer by connecting all components
# into a unified application with proper middleware and dependency injection.

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware import auth, logging, rate_limiting
from src.api.routers import monitoring_router, workflows_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    app.state.startup_time = "2024-01-01T00:00:00Z"  # Placeholder
    yield
    # Shutdown
    app.state.shutdown_time = "2024-01-01T00:00:00Z"  # Placeholder


def create_app(
    *,
    title: str = "ViraLearn Content Agent API",
    description: str = "AI-powered content generation and workflow orchestration",
    version: str = "1.0.0",
    debug: bool = False,
) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        title: Application title
        description: Application description
        version: API version
        debug: Enable debug mode
        
    Returns:
        Configured FastAPI application instance
    """
    # Create FastAPI app with lifespan management
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        debug=debug,
        lifespan=lifespan,
    )
    
    # Add CORS middleware for cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware in order of execution
    # 1. Logging middleware (first to capture all requests)
    app.add_middleware(logging.LoggingMiddleware)
    
    # 2. Rate limiting middleware
    app.add_middleware(rate_limiting.RateLimitingMiddleware)
    
    # 3. Authentication middleware (last to ensure proper context)
    app.add_middleware(auth.AuthMiddleware)
    
    # Include API routers (no prefix needed as routers already have /api/v1 prefix)
    app.include_router(workflows_router)
    app.include_router(monitoring_router)
    
    # Add root endpoint for API discovery
    @app.get("/")
    async def root() -> dict[str, Any]:
        """Root endpoint providing API information."""
        return {
            "name": title,
            "version": version,
            "description": description,
            "endpoints": {
                "workflows": "/api/v1/workflows",
                "monitoring": "/api/v1/health",
                "docs": "/docs",
                "redoc": "/redoc",
            },
        }
    
    # Add health check at root level for load balancers
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Basic health check endpoint."""
        return {"status": "healthy"}
    
    # Global exception handler for unhandled exceptions
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> Response:
        """Global exception handler for unhandled errors."""
        from src.core.error_handling import exception_to_payload
        from src.core.monitoring import get_monitoring
        
        # Get monitoring instance for error logging
        monitoring_instance = get_monitoring("global")
        monitoring_instance.error(
            "unhandled_exception",
            error=str(exc),
            path=request.url.path,
            method=request.method,
        )
        
        # Convert exception to standardized error response
        error_payload = exception_to_payload(exc)
        
        # Handle both dict and Pydantic model responses
        if hasattr(error_payload, 'model_dump_json'):
            content = error_payload.model_dump_json()
        else:
            import json
            content = json.dumps(error_payload)
        
        return Response(
            content=content,
            status_code=500,
            media_type="application/json",
        )
    
    return app


# Create default app instance for uvicorn
app = create_app()


# Completed Step 15: Added FastAPI app factory with proper middleware wiring,
# lifespan management, CORS support, global exception handling, and API discovery.
# This completes Phase 3 API integration layer by providing a unified application
# that can be deployed and integrated with Developer B's services.
