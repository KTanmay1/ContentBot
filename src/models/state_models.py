"""State and workflow status models."""
# Step 1: Define workflow status enum and primary ContentState schema.
# Why: This central state is referenced by all agents and the API; it must
# exist before orchestration, validation, or base agent logic can be implemented.

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover - fallback for static analyzers
    class BaseModel:  # type: ignore
        pass

    def Field(*_args, **kwargs):  # type: ignore
        return kwargs.get("default", None)


class WorkflowStatus(Enum):
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    WAITING_HUMAN = "waiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ContentState(BaseModel):
    """Overall workflow state shared across all agents.

    Mirrors the architecture document: workflow identifiers, content data,
    quality controls, and human feedback history.
    """

    # Workflow Management
    workflow_id: str = Field(..., description="Unique workflow identifier")
    user_id: Optional[str] = Field(default=None, description="End user id")
    status: WorkflowStatus = Field(default=WorkflowStatus.INITIATED)
    current_agent: Optional[str] = Field(default=None)
    step_count: int = Field(default=0)

    # Content Data
    original_input: Dict[str, Any] = Field(default_factory=dict)
    input_analysis: Optional[Dict[str, Any]] = Field(default=None)
    analysis_data: Optional[Dict[str, Any]] = Field(default=None)
    text_content: Dict[str, str] = Field(default_factory=dict)
    image_content: Dict[str, str] = Field(default_factory=dict)
    platform_content: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Quality Control
    quality_scores: Dict[str, float] = Field(default_factory=dict)
    brand_compliance: Optional[Dict[str, Any]] = Field(default=None)
    human_feedback: List[Dict[str, Any]] = Field(default_factory=list)

    # Error Handling
    error_log: List[Dict[str, Any]] = Field(default_factory=list)
    retry_count: int = Field(default=0)

    def increment_step(self) -> None:
        """Increment the internal step counter for each agent transition."""
        self.step_count += 1

    class Config:
        use_enum_values = True

# Completed Step 1: Added WorkflowStatus and ContentState with all required fields
# and a utility increment_step() method consistent with the architecture docs.