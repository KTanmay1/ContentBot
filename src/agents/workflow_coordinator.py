"""Workflow coordinator agent responsible for orchestrating the pipeline."""
# Step 8: Implement a basic WorkflowCoordinator skeleton with routing hooks.
# Why: Orchestration layer is the critical path for Developer A in Phase 2.

from __future__ import annotations

from typing import Dict, Optional

from src.core.error_handling import AgentException
from src.core.monitoring import get_monitoring
from src.models.state_models import ContentState, WorkflowStatus
from .base_agent import BaseAgent
from .input_analyzer import InputAnalyzer
from .content_planner import ContentPlanner
from .quality_assurance import QualityAssurance
from .human_review import HumanReview


class WorkflowCoordinator(BaseAgent):
    def __init__(
        self,
        *,
        name: Optional[str] = None,
        input_analyzer: Optional[InputAnalyzer] = None,
        content_planner: Optional[ContentPlanner] = None,
        quality_assurance: Optional[QualityAssurance] = None,
        human_review: Optional[HumanReview] = None,
    ) -> None:
        super().__init__(name=name)
        self._agents: Dict[str, BaseAgent] = {
            "InputAnalyzer": input_analyzer or InputAnalyzer(),
            "ContentPlanner": content_planner or ContentPlanner(),
            "QualityAssurance": quality_assurance or QualityAssurance(),
            "HumanReview": human_review or HumanReview(),
        }
    def determine_next_agent(self, _state: ContentState) -> Optional[str]:
        """Decide which agent should run next based on current state."""
        # Terminal conditions
        if _state.status in (WorkflowStatus.FAILED, WorkflowStatus.CANCELLED):
            return None

        # Route by data-availability
        if not _state.input_analysis:
            return "InputAnalyzer"

        if "plan" not in _state.platform_content:
            return "ContentPlanner"

        if "overall" not in _state.quality_scores:
            return "QualityAssurance"

        if len(_state.human_feedback) == 0:
            return "HumanReview"

        return None

    def orchestrate_workflow(self, state: ContentState) -> ContentState:
        monitoring = get_monitoring(state.workflow_id)
        step_guard = 0
        while True:
            next_agent_name = self.determine_next_agent(state)
            monitoring.info("coordinator_route", next_agent=next_agent_name)
            if next_agent_name is None:
                state.status = WorkflowStatus.COMPLETED
                return state

            agent = self._agents.get(next_agent_name)
            if agent is None:
                raise AgentException(f"Unknown next agent: {next_agent_name}")

            state = agent.run(state).state
            if state.status in (WorkflowStatus.FAILED, WorkflowStatus.CANCELLED):
                return state

            step_guard += 1
            if step_guard > 20:
                raise AgentException("Coordinator exceeded max steps; possible loop")

    def handle_workflow_errors(self, _error: Exception, state: ContentState) -> ContentState:
        state.status = WorkflowStatus.FAILED
        return state

    def execute(self, state: ContentState) -> ContentState:
        return self.orchestrate_workflow(state)


# Completed Step 8: Added coordinator skeleton with routing/termination hooks.

