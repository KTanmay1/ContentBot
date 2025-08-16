"""API request/response models for workflow endpoints."""
# Step 3: Define minimal request/response shapes that the API and tests will
# use for workflow creation and status queries.

from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from pydantic import BaseModel
except ImportError:  # pragma: no cover - fallback for static analyzers
    class BaseModel:  # type: ignore
        pass


class CreateWorkflowRequest(BaseModel):
    input: Dict[str, Any]
    user_id: Optional[str] = None


class CreateWorkflowResponse(BaseModel):
    workflow_id: str
    status: str


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    status: str
    current_agent: Optional[str] = None
    step_count: int


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None

# Completed Step 3: Added create/status response models and a generic
# ErrorResponse to standardize error payloads.