import asyncio

from src.core.workflow_engine import WorkflowEngine
from src.agents.base_agent import BaseAgent
from src.models.state_models import ContentState, WorkflowStatus


class StepAgent(BaseAgent):
    def execute(self, state: ContentState) -> ContentState:
        state.text_content.setdefault("steps", []).append(self.name)
        return state


def test_engine_execute_async():
    engine = WorkflowEngine([StepAgent(name="A"), StepAgent(name="B")])
    state = ContentState(workflow_id="wf-async", status=WorkflowStatus.INITIATED)
    out = asyncio.run(engine.execute_async(state))
    assert out.status == WorkflowStatus.COMPLETED
    assert out.text_content["steps"] == ["A", "B"]


def test_engine_start_background():
    engine = WorkflowEngine([StepAgent(name="A")])
    state = ContentState(workflow_id="wf-bg", status=WorkflowStatus.INITIATED)

    async def run_case():
        done = asyncio.Event()
        result_holder = {}

        def on_complete(s: ContentState) -> None:
            result_holder["state"] = s
            done.set()

        task = engine.start_background(state, on_complete=on_complete)
        await done.wait()
        out = result_holder["state"]
        assert out.status == WorkflowStatus.COMPLETED
        assert out.text_content["steps"] == ["A"]
        await task

    asyncio.run(run_case())


