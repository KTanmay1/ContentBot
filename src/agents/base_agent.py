"""Abstract base agent with validation, monitoring, and error handling."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

try:
    from pydantic import BaseModel
except ImportError:  # pragma: no cover - fallback for static analyzers
    class BaseModel:  # type: ignore
        # Minimal stand-in for type checkers
        def __init__(self, **_kwargs):
            pass

from src.core.error_handling import AgentException, ValidationException, exception_to_payload
from src.core.monitoring import Monitoring, get_monitoring
from src.models.state_models import ContentState, WorkflowStatus
from src.utils.validators import validate_content_state


class AgentResult(BaseModel):
    state: ContentState


class BaseAgent(ABC):
    """Abstract base class for all agents.

    Subclasses implement `execute()` and may override hooks.
    """

    name: str

    def __init__(self, *, name: Optional[str] = None) -> None:
        self.name = name or self.__class__.__name__

    # Hooks
    def before_execute(self, state: ContentState, monitoring: Monitoring) -> None:
        monitoring.info("agent_before_execute", agent=self.name, status=state.status)

    def after_execute(self, new_state: ContentState, monitoring: Monitoring) -> None:
        monitoring.info("agent_after_execute", agent=self.name, status=new_state.status)

    @abstractmethod
    def execute(self, state: ContentState) -> ContentState:
        """Perform the agent-specific work and return the updated state."""
        raise NotImplementedError

    def run(self, state: ContentState) -> AgentResult:
        """Run wrapper that validates input, logs, and handles errors."""
        monitoring = get_monitoring(state.workflow_id)
        try:
            validate_content_state(state)
            state.current_agent = self.name
            # Normalize and advance status from INITIATED -> IN_PROGRESS
            current_status = state.status
            if isinstance(current_status, str):
                try:
                    current_status = WorkflowStatus(current_status)
                except Exception:  # pragma: no cover - best effort normalization
                    current_status = None
            if current_status in (WorkflowStatus.INITIATED, None):
                state.status = WorkflowStatus.IN_PROGRESS
            self.before_execute(state, monitoring)

            updated = self.execute(state)

            updated.increment_step()
            updated.current_agent = self.name
            # Ensure post-exec status is not stuck at INITIATED (string or enum)
            if updated.status in (WorkflowStatus.INITIATED, "initiated"):
                updated.status = WorkflowStatus.IN_PROGRESS

            self.after_execute(updated, monitoring)
            monitoring.info("agent_success", agent=self.name, step_count=updated.step_count)
            return AgentResult(state=updated)

        except ValidationException as exc:
            payload = exception_to_payload(exc)
            monitoring.error("agent_validation_failed", agent=self.name, **payload)
            state.status = WorkflowStatus.FAILED
            return AgentResult(state=state)
        except AgentException as exc:
            payload = exception_to_payload(exc)
            monitoring.error("agent_failed", agent=self.name, **payload)
            state.status = WorkflowStatus.FAILED
            return AgentResult(state=state)
        except Exception as exc:  # noqa: BLE001
            payload = exception_to_payload(exc)
            monitoring.error("agent_crashed", agent=self.name, **payload)
            state.status = WorkflowStatus.FAILED
            return AgentResult(state=state)