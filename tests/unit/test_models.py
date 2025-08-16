"""Unit tests for data models."""

import pytest
from datetime import datetime
from typing import Dict, Any

from src.models.state_models import ContentState, WorkflowStatus
from src.models.content_models import BlogPost, SocialPost
from src.models.api_models import CreateWorkflowRequest, CreateWorkflowResponse


class TestContentState:
    """Test cases for ContentState model."""
    
    def test_content_state_defaults(self):
        """Test ContentState default values."""
        state = ContentState(workflow_id="wf-1", status=WorkflowStatus.INITIATED)
        assert state.step_count == 0
        assert state.text_content == {}
        assert state.image_content == {}
        assert state.platform_content == {}
        assert state.quality_scores == {}
        assert state.human_feedback == []
        assert state.error_log == []
    
    def test_increment_step(self):
        """Test step increment functionality."""
        state = ContentState(workflow_id="wf-2", status=WorkflowStatus.INITIATED)
        state.increment_step()
        assert state.step_count == 1
        
        state.increment_step()
        assert state.step_count == 2
    
    def test_workflow_status_transitions(self):
        """Test workflow status transitions."""
        state = ContentState(workflow_id="wf-3", status=WorkflowStatus.INITIATED)
        
        # Test status updates
        state.status = WorkflowStatus.IN_PROGRESS
        assert state.status == WorkflowStatus.IN_PROGRESS
        
        state.status = WorkflowStatus.COMPLETED
        assert state.status == WorkflowStatus.COMPLETED
    
    def test_content_updates(self):
        """Test content updates in state."""
        state = ContentState(workflow_id="wf-4", status=WorkflowStatus.INITIATED)
        
        # Test text content updates
        state.text_content["title"] = "Test Title"
        state.text_content["body"] = "Test content body"
        assert state.text_content["title"] == "Test Title"
        assert state.text_content["body"] == "Test content body"
        
        # Test image content updates
        state.image_content["featured"] = "image_url.jpg"
        assert state.image_content["featured"] == "image_url.jpg"
    
    def test_quality_scores(self):
        """Test quality score tracking."""
        state = ContentState(workflow_id="wf-5", status=WorkflowStatus.INITIATED)
        
        state.quality_scores["readability"] = 0.85
        state.quality_scores["brand_compliance"] = 0.92
        assert state.quality_scores["readability"] == 0.85
        assert state.quality_scores["brand_compliance"] == 0.92
    
    def test_human_feedback(self):
        """Test human feedback tracking."""
        state = ContentState(workflow_id="wf-6", status=WorkflowStatus.INITIATED)
        
        feedback = {"reviewer": "john_doe", "approved": True, "comments": "Looks good"}
        state.human_feedback.append(feedback)
        assert len(state.human_feedback) == 1
        assert state.human_feedback[0]["reviewer"] == "john_doe"
    
    def test_error_logging(self):
        """Test error logging functionality."""
        state = ContentState(workflow_id="wf-7", status=WorkflowStatus.INITIATED)
        
        error = {"agent": "TextGenerator", "error": "API timeout", "timestamp": datetime.now().isoformat()}
        state.error_log.append(error)
        assert len(state.error_log) == 1
        assert state.error_log[0]["agent"] == "TextGenerator"


class TestContentModels:
    """Test cases for content models."""
    
    def test_blog_post_creation(self):
        """Test BlogPost model creation."""
        blog_post = BlogPost(
            title="Test Blog Post",
            summary="This is a test summary.",
            sections=[{"heading": "Introduction", "body": "This is the intro."}],
            keywords=["test", "blog"]
        )
        assert blog_post.title == "Test Blog Post"
        assert blog_post.summary == "This is a test summary."
        assert len(blog_post.sections) == 1
        assert blog_post.sections[0]["heading"] == "Introduction"
        assert "test" in blog_post.keywords
    
    def test_social_post_creation(self):
        """Test SocialPost model creation."""
        social_post = SocialPost(
            content="Test social media post",
            platform="twitter",
            hashtags=["#AI", "#Tech"]
        )
        assert social_post.content == "Test social media post"
        assert social_post.platform == "twitter"
        assert "#AI" in social_post.hashtags


class TestAPIModels:
    """Test cases for API models."""
    
    def test_create_workflow_request(self):
        """Test CreateWorkflowRequest model."""
        request = CreateWorkflowRequest(
            input={
                "text": "Create a blog post about AI",
                "content_type": "blog_post",
                "target_platforms": ["linkedin", "twitter"]
            },
            user_id="user123"
        )
        assert request.input["text"] == "Create a blog post about AI"
        assert request.input["content_type"] == "blog_post"
        assert "linkedin" in request.input["target_platforms"]
        assert request.user_id == "user123"
    
    def test_create_workflow_response(self):
        """Test CreateWorkflowResponse model."""
        response = CreateWorkflowResponse(
            workflow_id="wf-123",
            status="initiated"
        )
        assert response.workflow_id == "wf-123"
        assert response.status == "initiated"


class TestWorkflowStatus:
    """Test cases for WorkflowStatus enum."""
    
    def test_workflow_status_values(self):
        """Test WorkflowStatus enum values."""
        assert WorkflowStatus.INITIATED.value == "initiated"
        assert WorkflowStatus.IN_PROGRESS.value == "in_progress"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.WAITING_HUMAN.value == "waiting_human"
        assert WorkflowStatus.CANCELLED.value == "cancelled"
    
    def test_workflow_status_comparison(self):
        """Test WorkflowStatus enum comparison."""
        status1 = WorkflowStatus.INITIATED
        status2 = WorkflowStatus.IN_PROGRESS
        status3 = WorkflowStatus.INITIATED
        
        assert status1 == status3
        assert status1 != status2
        assert status1.value == "initiated"
        assert status2.value == "in_progress"