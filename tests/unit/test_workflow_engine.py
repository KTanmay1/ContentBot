import pytest

from src.core.workflow_engine import WorkflowEngine
from src.agents.base_agent import BaseAgent
from src.models.state_models import ContentState, WorkflowStatus


class StepAgent(BaseAgent):
    def execute(self, state: ContentState) -> ContentState:
        state.text_content.setdefault("steps", []).append(self.name)
        return state


def test_engine_sequential_execution():
    a1 = StepAgent(name="A1")
    a2 = StepAgent(name="A2")
    engine = WorkflowEngine([a1, a2])

    state = ContentState(workflow_id="wf-e1", status=WorkflowStatus.INITIATED)
    out = engine.execute(state)

    assert out.status == WorkflowStatus.COMPLETED
    assert out.text_content["steps"] == ["A1", "A2"]
    assert out.step_count >= 2


