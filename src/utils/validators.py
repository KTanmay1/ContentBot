"""Validators for shared state and inputs."""

from __future__ import annotations

from typing import Any

from src.core.error_handling import ValidationException
from src.models.state_models import ContentState, WorkflowStatus


def validate_content_state(state: ContentState) -> None:
    if not state.workflow_id or not isinstance(state.workflow_id, str):
        raise ValidationException("`workflow_id` must be a non-empty string")

    # Allow either enum or its string value (due to use_enum_values in model).
    if not (
        isinstance(state.status, WorkflowStatus)
        or (isinstance(state.status, str) and state.status in {m.value for m in WorkflowStatus})
    ):
        raise ValidationException("`status` must be a WorkflowStatus or its value string")

    if state.step_count < 0:
        raise ValidationException("`step_count` must be >= 0")

    if not isinstance(state.original_input, dict):
        raise ValidationException("`original_input` must be a dict of input fields")


def ensure_field_present(container: dict[str, Any], field_name: str) -> None:
    if field_name not in container:
        raise ValidationException(f"Missing required field: {field_name}")


 


