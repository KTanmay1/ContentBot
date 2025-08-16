import asyncio

from src.core.workflow_engine import WorkflowEngine
from src.agents.base_agent import BaseAgent
from src.models.state_models import ContentState, WorkflowStatus


class StepAgent(BaseAgent):
    def execute(self, state: ContentState) -> ContentState:
        state.text_content.setdefault("steps", []).append(self.name)
        return state


def test_engine_with_memory_and_interrupt_resume():
    engine = WorkflowEngine([])  # use default conditional graph
    state = ContentState(workflow_id="wf-mem", status=WorkflowStatus.INITIATED, original_input={"text": "x"})
    # Run with memory so it will interrupt before human review; then resume
    _ = engine.execute_with_memory(state, thread_id="wf-mem")
    out = asyncio.run(engine.resume_human_review_async(thread_id="wf-mem", human_feedback={"review": "approved"}))
    assert out.status in (WorkflowStatus.COMPLETED, "completed")


def test_engine_linear_graph_completion():
    engine = WorkflowEngine([StepAgent(name="A"), StepAgent(name="B")])
    state = ContentState(workflow_id="wf-lin", status=WorkflowStatus.INITIATED)
    out = engine.execute(state)
    assert out.status == WorkflowStatus.COMPLETED
    assert out.text_content["steps"] == ["A", "B"]


