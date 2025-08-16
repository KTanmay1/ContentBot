import pytest

from src.agents.input_analyzer import InputAnalyzer
from src.agents.content_planner import ContentPlanner
from src.agents.quality_assurance import QualityAssurance
from src.agents.human_review import HumanReview
from src.models.state_models import ContentState, WorkflowStatus


def test_input_analyzer_execute_populates_analysis():
    agent = InputAnalyzer()
    state = ContentState(workflow_id="wf-ia", status=WorkflowStatus.INITIATED, original_input={"text": "hello"})
    out = agent.run(state).state
    assert out.input_analysis is not None
    assert "themes" in out.input_analysis
    assert "sentiment" in out.input_analysis


def test_content_planner_execute_creates_plan_tasks():
    agent = ContentPlanner()
    state = ContentState(workflow_id="wf-cp", status=WorkflowStatus.INITIATED)
    state.input_analysis = {"themes": ["ai", "ml"]}
    out = agent.run(state).state
    assert "plan" in out.platform_content
    tasks = out.platform_content["plan"]["tasks"]
    assert isinstance(tasks, list) and len(tasks) >= 2
    kinds = {t.get("type") for t in tasks}
    assert {"blog_post", "social_post"}.issubset(kinds)


def test_quality_assurance_sets_quality_and_compliance():
    agent = QualityAssurance()
    state = ContentState(workflow_id="wf-qa", status=WorkflowStatus.INITIATED)
    state.text_content["example"] = "text"
    out = agent.run(state).state
    assert out.quality_scores.get("overall") == 0.75
    assert out.brand_compliance == {"brand": True, "style": True}


def test_human_review_transitions_and_appends_feedback():
    agent = HumanReview()
    state = ContentState(workflow_id="wf-hr", status=WorkflowStatus.INITIATED)
    out = agent.run(state).state
    # Agent sets WAITING_HUMAN then collects feedback and returns to IN_PROGRESS
    assert out.status in (WorkflowStatus.IN_PROGRESS, "in_progress")
    assert len(out.human_feedback) >= 1


