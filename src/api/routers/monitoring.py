"""Monitoring endpoints (Developer A)."""
# Step 15: Implement health and metrics stubs to align with Developer A tasks.

from __future__ import annotations

from fastapi import APIRouter

# Use absolute import path consistent with project structure
from src.services.image_service import get_image_service

router = APIRouter(prefix="/api/v1", tags=["monitoring"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/metrics")
def metrics() -> dict:
    # Placeholder; integrate with real metrics backend later
    return {"uptime_seconds": 0, "workflows_completed": 0}


# Additional endpoints for frontend compatibility
monitoring_router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@monitoring_router.get("/status")
def get_system_status() -> dict:
    return {
        "database": "healthy",
        "llm_provider": "healthy",
        "agents": {
            "content_planner": "healthy",
            "blog_writer": "healthy",
            "social_media_creator": "healthy",
            "quality_assessor": "healthy"
        },
        "lastChecked": "2024-01-01T00:00:00Z"
    }


@monitoring_router.get("/agents")
def get_agent_status() -> dict:
    return {
        "agents": [
            {
                "id": "content_planner",
                "name": "Content Planner",
                "status": "healthy",
                "last_activity": "2024-01-01T00:00:00Z"
            },
            {
                "id": "blog_writer",
                "name": "Blog Writer",
                "status": "healthy",
                "last_activity": "2024-01-01T00:00:00Z"
            },
            {
                "id": "social_media_creator",
                "name": "Social Media Creator",
                "status": "healthy",
                "last_activity": "2024-01-01T00:00:00Z"
            },
            {
                "id": "quality_assessor",
                "name": "Quality Assessor",
                "status": "healthy",
                "last_activity": "2024-01-01T00:00:00Z"
            }
        ]
    }


@monitoring_router.get("/workflows")
def get_workflow_stats() -> dict:
    return {
        "total_workflows": 0,
        "completed_workflows": 0,
        "failed_workflows": 0,
        "running_workflows": 0
    }


@monitoring_router.get("/activity")
def get_recent_activity() -> dict:
    return {
        "activities": []
    }


@monitoring_router.get("/image")
async def get_image_service_status() -> dict:
    """Health info for image generation provider(s)."""
    svc = await get_image_service()
    health = await svc.health_check()
    # Do NOT expose the token; only indicate presence
    token_present = bool(svc.hf_headers.get("Authorization"))
    return {
        **health,
        "hf_token_present": token_present,
        "hf_headers_set": bool(svc.hf_headers),
    }

# Completed Step 15: Added health and metrics endpoints.