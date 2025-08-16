import pytest

from src.agents.base_agent import BaseAgent
from src.models.state_models import ContentState, WorkflowStatus


class NoopAgent(BaseAgent):
    def execute(self, state: ContentState) -> ContentState:
        state.text_content["noop"] = "ok"
        return state


def test_base_agent_run_success():
    agent = NoopAgent()
    state = ContentState(workflow_id="wf-a", status=WorkflowStatus.INITIATED)
    result = agent.run(state)
    assert result.state.text_content["noop"] == "ok"
    assert result.state.status in (WorkflowStatus.IN_PROGRESS, WorkflowStatus.INITIATED)
    assert result.state.current_agent == agent.name


