"""Workflow management API endpoints (Developer A)."""
# Step 14: Implement workflow routers for creation, status, content, and cancel.
# Why: Aligns with Phase 3 responsibilities for Developer A without requiring
# Developer B's main app or database; uses an in-memory store for tests.

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from src.agents.workflow_coordinator import WorkflowCoordinator
from src.models import (
    ContentState,
    CreateWorkflowRequest,
    CreateWorkflowResponse,
    WorkflowStatusResponse,
)
from src.core.workflow_engine import WorkflowEngine


router = APIRouter(prefix="/api/v1", tags=["workflows"])


class StateRepository(Protocol):
    def save(self, state: ContentState) -> None: ...
    def load(self, workflow_id: str) -> Optional[ContentState]: ...
    def delete(self, workflow_id: str) -> bool: ...


class InMemoryStateRepository:
    def __init__(self) -> None:
        self._store: Dict[str, ContentState] = {}

    def save(self, state: ContentState) -> None:
        self._store[state.workflow_id] = state

    def load(self, workflow_id: str) -> Optional[ContentState]:
        return self._store.get(workflow_id)

    def delete(self, workflow_id: str) -> bool:
        return self._store.pop(workflow_id, None) is not None

# Use a process-wide in-memory repository for now so subsequent requests can
# retrieve previously saved state during tests.
_GLOBAL_REPO = InMemoryStateRepository()


def get_repository() -> StateRepository:
    return _GLOBAL_REPO


def get_coordinator() -> WorkflowCoordinator:
    return WorkflowCoordinator()


def get_engine() -> WorkflowEngine:
    # Engine with default conditional graph (uses Router and conditional edges)
    return WorkflowEngine([])


def _status_value(status_obj: object) -> str:
    try:
        # Enum case
        return status_obj.value  # type: ignore[attr-defined]
    except Exception:
        # Already a string or unrecognized
        return str(status_obj)


@router.post("/workflows", response_model=CreateWorkflowResponse)
def create_workflow(
    payload: CreateWorkflowRequest,
    repo: StateRepository = Depends(get_repository),
    coordinator: WorkflowCoordinator = Depends(get_coordinator),
    engine: WorkflowEngine = Depends(get_engine),
) -> CreateWorkflowResponse:
    workflow_id = str(uuid4())
    state = ContentState(workflow_id=workflow_id, status="initiated", original_input=payload.input, user_id=payload.user_id)

    # Execute immediately for MVP (coordinator handles full routing)
    result = coordinator.run(state).state
    repo.save(result)
    return CreateWorkflowResponse(workflow_id=workflow_id, status=_status_value(result.status))


@router.get("/workflows/{workflow_id}", response_model=WorkflowStatusResponse)
def get_workflow_status(
    workflow_id: str,
    repo: StateRepository = Depends(get_repository),
) -> WorkflowStatusResponse:
    state = repo.load(workflow_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workflow not found")
    return WorkflowStatusResponse(workflow_id=workflow_id, status=_status_value(state.status), current_agent=state.current_agent, step_count=state.step_count)


@router.post("/workflows/{workflow_id}/pause")
def pause_for_human_review(
    workflow_id: str,
    repo: StateRepository = Depends(get_repository),
) -> Dict[str, str]:
    state = repo.load(workflow_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workflow not found")
    state.status = "waiting_human"
    repo.save(state)
    return {"workflow_id": workflow_id, "status": "waiting_human"}


@router.post("/workflows/{workflow_id}/resume")
def resume_after_human_review(
    workflow_id: str,
    feedback: Dict[str, Any],
    repo: StateRepository = Depends(get_repository),
    engine: WorkflowEngine = Depends(get_engine),
) -> Dict[str, Any]:
    state = repo.load(workflow_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workflow not found")
    # Append feedback and mark in progress
    state.human_feedback.append(feedback)
    state.status = "in_progress"
    repo.save(state)
    return {"workflow_id": workflow_id, "status": "in_progress", "human_feedback": state.human_feedback}


@router.get("/workflows/{workflow_id}/content")
def get_workflow_content(
    workflow_id: str,
    repo: StateRepository = Depends(get_repository),
) -> Dict[str, Any]:
    state = repo.load(workflow_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workflow not found")
    return {
        "text_content": state.text_content,
        "image_content": state.image_content,
        "platform_content": state.platform_content,
        "quality_scores": state.quality_scores,
        "brand_compliance": state.brand_compliance,
        "human_feedback": state.human_feedback,
    }


@router.delete("/workflows/{workflow_id}")
def cancel_workflow(
    workflow_id: str,
    repo: StateRepository = Depends(get_repository),
) -> Dict[str, str]:
    state = repo.load(workflow_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workflow not found")
    state.status = "cancelled"
    repo.save(state)
    return {"workflow_id": workflow_id, "status": "cancelled"}


# Completed Step 14: Added workflow router with in-memory repository and DI.