import pytest

from src.agents.workflow_coordinator import WorkflowCoordinator
from src.models.state_models import ContentState, WorkflowStatus


def test_coordinator_determines_next_agent_sequence():
    coord = WorkflowCoordinator()

    # Starts with missing analysis -> InputAnalyzer
    s = ContentState(workflow_id="wf-cc-1", status=WorkflowStatus.INITIATED)
    assert coord.determine_next_agent(s) == "InputAnalyzer"

    # With analysis, but no plan -> ContentPlanner
    s.input_analysis = {"themes": ["ai"]}
    assert coord.determine_next_agent(s) == "ContentPlanner"

    # With plan, but no quality -> QualityAssurance
    s.platform_content["plan"] = {"tasks": []}
    assert coord.determine_next_agent(s) == "QualityAssurance"

    # With quality, but no human feedback -> HumanReview
    s.quality_scores["overall"] = 0.9
    assert coord.determine_next_agent(s) == "HumanReview"

    # With human feedback -> complete (None)
    s.human_feedback.append({"review": "approved"})
    assert coord.determine_next_agent(s) is None


