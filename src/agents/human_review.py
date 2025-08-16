"""Human-in-the-loop review agent to collect and apply feedback."""
# Step 12: Implement HumanReview skeleton that appends a feedback stub.
# Why: Enables WAITING_HUMAN transitions and feedback capture later.

from __future__ import annotations

from typing import Dict

from src.models.state_models import ContentState, WorkflowStatus
from .base_agent import BaseAgent


class HumanReview(BaseAgent):
    def request_review(self, state: ContentState) -> None:
        state.status = WorkflowStatus.WAITING_HUMAN

    def collect_feedback(self, payload: Dict) -> Dict:
        return {"review": "approved", **payload}

    def execute(self, state: ContentState) -> ContentState:
        self.request_review(state)
        # Placeholder: in a real system this would be asynchronous
        feedback = self.collect_feedback({"notes": "LGTM"})
        state.human_feedback.append(feedback)
        state.status = WorkflowStatus.IN_PROGRESS
        return state


# Completed Step 12: Added HumanReview skeleton with WAITING_HUMAN transition.

