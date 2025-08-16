"""Monitoring endpoints (Developer A)."""
# Step 15: Implement health and metrics stubs to align with Developer A tasks.

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["monitoring"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/metrics")
def metrics() -> dict:
    # Placeholder; integrate with real metrics backend later
    return {"uptime_seconds": 0, "workflows_completed": 0}


# Completed Step 15: Added health and metrics endpoints.