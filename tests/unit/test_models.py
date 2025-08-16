import pytest

from src.models.state_models import ContentState, WorkflowStatus


def test_content_state_defaults():
    state = ContentState(workflow_id="wf-1", status=WorkflowStatus.INITIATED)
    assert state.step_count == 0
    assert state.text_content == {}
    assert state.image_content == {}
    assert state.platform_content == {}
    assert state.quality_scores == {}


def test_increment_step():
    state = ContentState(workflow_id="wf-2", status=WorkflowStatus.INITIATED)
    state.increment_step()
    assert state.step_count == 1


