"""Workflow coordinator agent responsible for orchestrating the pipeline."""
# Step 8: Implement a basic WorkflowCoordinator skeleton with routing hooks.
# Why: Orchestration layer is the critical path for Developer A in Phase 2.

from __future__ import annotations

from typing import Dict, Optional

from src.core.error_handling import AgentException
from src.core.monitoring import get_monitoring
from src.models.state_models import ContentState, WorkflowStatus
from .base_agent import BaseAgent

# Import all available agents
try:
    from .input_analyzer import InputAnalyzer
    from .content_planner import ContentPlanner
    from .quality_assurance import QualityAssurance
    from .human_review import HumanReview
    from .text_generator import TextGenerator
    from .image_generator import ImageGenerator
    from .audio_processor import AudioProcessor
    from .brand_voice import BrandVoice
    from .cross_platform import CrossPlatform
except ImportError:
    # Placeholder implementations for missing agents
    class InputAnalyzer(BaseAgent):
        def execute(self, state: ContentState) -> ContentState:
            state.input_analysis = {"analyzed": True, "type": "placeholder"}
            return state
    
    class ContentPlanner(BaseAgent):
        def execute(self, state: ContentState) -> ContentState:
            state.platform_content["plan"] = {"planned": True, "type": "placeholder"}
            return state
    
    class QualityAssurance(BaseAgent):
        def execute(self, state: ContentState) -> ContentState:
            state.quality_scores["overall"] = 0.8
            return state
    
    class HumanReview(BaseAgent):
        def execute(self, state: ContentState) -> ContentState:
            if not state.human_feedback:
                state.human_feedback.append({"reviewer": "system", "approved": True})
            return state
    
    class TextGenerator(BaseAgent):
        def execute(self, state: ContentState) -> ContentState:
            state.text_content = {"main_content": "Generated text placeholder"}
            return state
    
    class ImageGenerator(BaseAgent):
        def execute(self, state: ContentState) -> ContentState:
            state.image_content = {"main_images": ["Generated image placeholder"]}
            return state
    
    class AudioProcessor(BaseAgent):
        def execute(self, state: ContentState) -> ContentState:
            state.audio_content = {"main_audio": "Generated audio placeholder"}
            return state
    
    class BrandVoice(BaseAgent):
        def execute(self, state: ContentState) -> ContentState:
            state.brand_compliance = {"status": "compliant", "score": 0.85}
            return state
    
    class CrossPlatform(BaseAgent):
        def execute(self, state: ContentState) -> ContentState:
            state.platform_content = {"optimized": True}
            return state


class WorkflowCoordinator(BaseAgent):
    def __init__(
        self,
        *,
        name: Optional[str] = None,
        input_analyzer: Optional[InputAnalyzer] = None,
        content_planner: Optional[ContentPlanner] = None,
        text_generator: Optional[TextGenerator] = None,
        image_generator: Optional[ImageGenerator] = None,
        audio_processor: Optional[AudioProcessor] = None,
        brand_voice: Optional[BrandVoice] = None,
        cross_platform: Optional[CrossPlatform] = None,
        quality_assurance: Optional[QualityAssurance] = None,
        human_review: Optional[HumanReview] = None,
    ) -> None:
        super().__init__(name=name)
        self._agents: Dict[str, BaseAgent] = {
            "InputAnalyzer": input_analyzer or InputAnalyzer(),
            "ContentPlanner": content_planner or ContentPlanner(),
            "TextGenerator": text_generator or TextGenerator(),
            "ImageGenerator": image_generator or ImageGenerator(),
            "AudioProcessor": audio_processor or AudioProcessor(),
            "BrandVoice": brand_voice or BrandVoice(),
            "CrossPlatform": cross_platform or CrossPlatform(),
            "QualityAssurance": quality_assurance or QualityAssurance(),
            "HumanReview": human_review or HumanReview(),
        }
    
    def determine_next_agent(self, _state: ContentState) -> Optional[str]:
        """Decide which agent should run next based on current state."""
        # Terminal conditions
        if _state.status in (WorkflowStatus.FAILED, WorkflowStatus.CANCELLED):
            return None

        # Route by data-availability and workflow progression
        if not _state.input_analysis:
            return "InputAnalyzer"

        if "plan" not in _state.platform_content:
            return "ContentPlanner"

        # Content generation phase
        if not _state.text_content:
            return "TextGenerator"

        if not _state.image_content:
            return "ImageGenerator"

        if not hasattr(_state, 'audio_content') or not _state.audio_content:
            return "AudioProcessor"

        # Brand compliance and platform optimization
        if not hasattr(_state, 'brand_compliance') or not _state.brand_compliance:
            return "BrandVoice"

        if not hasattr(_state, 'platform_content') or not _state.platform_content.get('optimized'):
            return "CrossPlatform"

        # Quality assurance and review
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