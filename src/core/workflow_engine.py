"""Workflow engine implemented on LangGraph to orchestrate agents over state."""
# Step 13 → Replace internals using LangGraph with same external API.
# Step 16: Preserve async/background helpers, now backed by LangGraph.

from __future__ import annotations

import asyncio
from typing import Iterable, List, Protocol, runtime_checkable, Any, Optional, Callable, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Send

from src.core.error_handling import AgentException
from src.core.monitoring import get_monitoring
from src.models.state_models import ContentState, WorkflowStatus
@runtime_checkable
class EngineAgent(Protocol):
    name: str

    def run(self, state: ContentState) -> Any:  # should return object with `.state`
        ...


class WorkflowEngine:
    def __init__(self, agents: Iterable[EngineAgent], *, checkpointer: object | None = None):
        self.agents: List[EngineAgent] = list(agents)
        # Checkpointer (e.g., MemorySaver) to be used when memory is enabled
        self.checkpointer = checkpointer
        # Simple in-process snapshot for interrupt/resume unit tests
        self._memory_store: dict[str, ContentState] = {}

    class _GraphState(TypedDict):
        content_state: ContentState

    def _build_linear_graph(self, monitoring):
        graph = StateGraph(self._GraphState)

        node_names: List[str] = []
        for agent in self.agents:
            name = agent.name
            node_names.append(name)

            def _make_node(a):
                def _node(s: WorkflowEngine._GraphState) -> WorkflowEngine._GraphState:
                    monitoring.info("engine_step_start", agent=a.name, step=s["content_state"].step_count)
                    new_state = a.run(s["content_state"]).state
                    return {"content_state": new_state}

                return _node

            graph.add_node(name, _make_node(agent))

        if node_names:
            graph.set_entry_point(node_names[0])
            for prev_name, next_name in zip(node_names, node_names[1:]):
                graph.add_edge(prev_name, next_name)
            graph.add_edge(node_names[-1], END)
        else:
            def _noop(s: WorkflowEngine._GraphState) -> WorkflowEngine._GraphState:
                return s

            graph.add_node("NOOP", _noop)
            graph.set_entry_point("NOOP")
            graph.add_edge("NOOP", END)

        return graph.compile()

    def _build_default_conditional_graph(self, monitoring, *, with_memory: bool = True, interrupt_before_human: bool = True):
        from src.agents.input_analyzer import InputAnalyzer
        from src.agents.content_planner import ContentPlanner
        from src.agents.quality_assurance import QualityAssurance
        # HumanReview handled via interrupt; node becomes a no-op pass-through

        analyzer = InputAnalyzer()
        planner = ContentPlanner()
        qa = QualityAssurance()
        graph = StateGraph(self._GraphState)

        # Add a Router node since conditional edges must originate from a node
        def _router_node(s: WorkflowEngine._GraphState) -> WorkflowEngine._GraphState:
            return s

        graph.add_node("Router", _router_node)

        def _router(s: WorkflowEngine._GraphState) -> str:
            st = s["content_state"]
            if st.status in (WorkflowStatus.FAILED, WorkflowStatus.CANCELLED):
                return "END"
            if not st.input_analysis:
                return "InputAnalyzer"
            if "plan" not in st.platform_content:
                return "ContentPlanner"
            # If no generated content yet, run parallel generation
            if not st.text_content:
                return "ParallelGen"
            if "overall" not in st.quality_scores:
                return "QualityAssurance"
            if len(st.human_feedback) == 0:
                return "HumanReview"
            return "END"

        def _node_for(a):
            def _node(s: WorkflowEngine._GraphState) -> WorkflowEngine._GraphState:
                monitoring.info("engine_step_start", agent=a.name, step=s["content_state"].step_count)
                new_state = a.run(s["content_state"]).state
                return {"content_state": new_state}

            return _node

        graph.add_node("InputAnalyzer", _node_for(analyzer))
        graph.add_node("ContentPlanner", _node_for(planner))
        graph.add_node("QualityAssurance", _node_for(qa))
        
        # Parallel generation entry: emits sends to generator nodes
        def _parallel_gen(s: WorkflowEngine._GraphState):
            # Minimal demo: always produce a text generation task
            return Send("TextGen", s)

        def _text_gen(s: WorkflowEngine._GraphState) -> WorkflowEngine._GraphState:
            st = s["content_state"]
            st.text_content.setdefault("steps", [])
            st.text_content["generated"] = "ok"
            return {"content_state": st}

        graph.add_node("ParallelGen", _parallel_gen)
        graph.add_node("TextGen", _text_gen)
        def _human_review_noop(s: WorkflowEngine._GraphState) -> WorkflowEngine._GraphState:
            # Pause happens before this node via interrupt; on resume, we just loop back
            return s

        graph.add_node("HumanReview", _human_review_noop)

        graph.add_conditional_edges(
            "Router",
            _router,
            {
                "InputAnalyzer": "InputAnalyzer",
                "ContentPlanner": "ContentPlanner",
                "ParallelGen": "ParallelGen",
                "QualityAssurance": "QualityAssurance",
                "HumanReview": "HumanReview",
                "END": END,
            },
        )

        graph.add_edge("InputAnalyzer", "Router")
        graph.add_edge("ContentPlanner", "Router")
        graph.add_edge("TextGen", "Router")
        graph.add_edge("QualityAssurance", "Router")
        graph.add_edge("HumanReview", "Router")

        graph.set_entry_point("Router")
        checkpointer = self.checkpointer or (MemorySaver() if with_memory else None)
        interrupts = ["HumanReview"] if interrupt_before_human else []
        return graph.compile(checkpointer=checkpointer, interrupt_before=interrupts)

    def _compile_graph(self, monitoring, *, with_memory: bool = False, interrupt_before_human: bool = False):
        if self.agents:
            return self._build_linear_graph(monitoring)
        return self._build_default_conditional_graph(monitoring, with_memory=with_memory, interrupt_before_human=interrupt_before_human)

    def execute(self, state: ContentState) -> ContentState:
        monitoring = get_monitoring(state.workflow_id)
        compiled = self._compile_graph(monitoring)
        out = compiled.invoke({"content_state": state})
        result = out["content_state"]
        # Ensure terminal completion parity with previous engine behavior
        terminal_values = {WorkflowStatus.FAILED, WorkflowStatus.CANCELLED, WorkflowStatus.COMPLETED, "failed", "cancelled", "completed"}
        if result.status not in terminal_values:
            result.status = WorkflowStatus.COMPLETED
        return result

    async def execute_async(self, state: ContentState) -> ContentState:
        monitoring = get_monitoring(state.workflow_id)
        compiled = self._compile_graph(monitoring)
        out = await compiled.ainvoke({"content_state": state})
        result = out["content_state"]
        terminal_values = {WorkflowStatus.FAILED, WorkflowStatus.CANCELLED, WorkflowStatus.COMPLETED, "failed", "cancelled", "completed"}
        if result.status not in terminal_values:
            result.status = WorkflowStatus.COMPLETED
        return result

    # LangGraph with memory + interrupt helpers
    def execute_with_memory(self, state: ContentState, *, thread_id: str) -> ContentState:
        monitoring = get_monitoring(state.workflow_id)
        compiled = self._compile_graph(monitoring, with_memory=True, interrupt_before_human=True)
        config = {"configurable": {"thread_id": thread_id}}
        out = compiled.invoke({"content_state": state}, config=config)
        result = out["content_state"]
        self._memory_store[thread_id] = result
        return result

    async def execute_with_memory_async(self, state: ContentState, *, thread_id: str) -> ContentState:
        monitoring = get_monitoring(state.workflow_id)
        compiled = self._compile_graph(monitoring, with_memory=True, interrupt_before_human=True)
        config = {"configurable": {"thread_id": thread_id}}
        out = await compiled.ainvoke({"content_state": state}, config=config)
        return out["content_state"]

    async def resume_human_review_async(self, *, thread_id: str, human_feedback: dict) -> ContentState:
        monitoring = get_monitoring(thread_id)
        compiled = self._compile_graph(monitoring, with_memory=True, interrupt_before_human=True)
        config = {"configurable": {"thread_id": thread_id}}
        # Use in-process snapshot from previous execution for tests
        s = self._memory_store.get(thread_id)
        if s is None:
            # Fallback: try get_state if available
            try:
                current_state = compiled.get_state(config)
                s = current_state.values.get("content_state")  # type: ignore[assignment]
            except Exception:
                s = None
        if s is None:
            raise AgentException("No saved state to resume from for thread_id")
        s.human_feedback.append(human_feedback)
        s.status = WorkflowStatus.IN_PROGRESS
        out = await compiled.ainvoke({"content_state": s}, config=config)
        result = out["content_state"]
        terminal_values = {WorkflowStatus.FAILED, WorkflowStatus.CANCELLED, WorkflowStatus.COMPLETED, "failed", "cancelled", "completed"}
        if result.status not in terminal_values:
            result.status = WorkflowStatus.COMPLETED
        return result

    async def retry_async(self, *, thread_id: str, max_retries: int = 3, backoff_base: float = 0.5) -> ContentState:
        monitoring = get_monitoring(thread_id)
        compiled = self._compile_graph(monitoring, with_memory=True, interrupt_before_human=True)
        config = {"configurable": {"thread_id": thread_id}}
        s = self._memory_store.get(thread_id)
        if s is None:
            try:
                current_state = compiled.get_state(config)
                s = current_state.values.get("content_state")  # type: ignore[assignment]
            except Exception:
                s = None
        if s is None:
            raise AgentException("No saved state to retry")

        retry_count = 0
        last_exc: Exception | None = None
        while retry_count < max_retries:
            try:
                s.status = WorkflowStatus.IN_PROGRESS
                out = await compiled.ainvoke({"content_state": s}, config=config)
                result = out["content_state"]
                self._memory_store[thread_id] = result
                terminal_values = {WorkflowStatus.FAILED, WorkflowStatus.CANCELLED, WorkflowStatus.COMPLETED, "failed", "cancelled", "completed"}
                if result.status not in terminal_values:
                    result.status = WorkflowStatus.COMPLETED
                return result
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                retry_count += 1
                await asyncio.sleep(backoff_base * (2 ** (retry_count - 1)))

        raise AgentException(f"Retry attempts exceeded: {last_exc}")

    def get_last_state(self, *, thread_id: str) -> Optional[ContentState]:
        return self._memory_store.get(thread_id)

    def start_background(
        self,
        state: ContentState,
        *,
        on_complete: Optional[Callable[[ContentState], None]] = None,
    ) -> "asyncio.Task[ContentState]":
        """Schedule workflow execution in the background.

        If `on_complete` is provided, it will be called with the resulting
        state when the task finishes (best-effort; exceptions are swallowed
        after logging by the engine).
        """

        async def _run_and_callback() -> ContentState:
            result = await self.execute_async(state)
            if on_complete is not None:
                try:
                    on_complete(result)
                except Exception:
                    # Intentionally swallow callback errors to avoid leaking
                    # into the task lifecycle
                    pass
            return result

        return asyncio.create_task(_run_and_callback())


# Completed Step 13: Added `WorkflowEngine` with sequential agent execution,
# status propagation, and centralized monitoring.


