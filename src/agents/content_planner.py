"""Content planning agent producing actionable tasks from analysis."""
# Step 10: Implement ContentPlanner skeleton returning high-level plan.
# Why: Provides structured tasks for generation agents.

from __future__ import annotations

from typing import Dict, List

from src.models.state_models import ContentState
from .base_agent import BaseAgent


class ContentPlanner(BaseAgent):
    def create_content_strategy(self, analysis: Dict) -> Dict:
        return {"strategy": "linear", "themes": analysis.get("themes", [])}

    def plan_content_package(self, strategy: Dict) -> List[Dict]:
        return [
            {"type": "blog_post", "title": "Draft Title", "keywords": strategy.get("themes", [])},
            {"type": "social_post", "platform": "twitter"},
        ]

    def execute(self, state: ContentState) -> ContentState:
        analysis = state.input_analysis or {}
        strategy = self.create_content_strategy(analysis)
        state.platform_content["plan"] = {"tasks": self.plan_content_package(strategy)}
        return state


# Completed Step 10: Added ContentPlanner skeleton with basic plan stubs.

