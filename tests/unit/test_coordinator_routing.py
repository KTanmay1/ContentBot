import pytest

from src.agents.workflow_coordinator import WorkflowCoordinator
from src.models.state_models import ContentState, WorkflowStatus


def test_coordinator_routes_through_pipeline_until_completion():
    state = ContentState(workflow_id="wf-c1", status=WorkflowStatus.INITIATED)
    coord = WorkflowCoordinator()
    out = coord.run(state).state

    assert out.status == WorkflowStatus.COMPLETED
    assert out.input_analysis is not None
    assert "plan" in out.platform_content
    assert "overall" in out.quality_scores
    assert len(out.human_feedback) >= 1

