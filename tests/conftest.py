"""Shared test fixtures and configuration for ContentBot tests."""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from src.models.state_models import ContentState, WorkflowStatus
from src.agents.base_agent import BaseAgent
from src.core.monitoring import Monitoring
from src.services.llm_service import LLMService
from src.services.image_service import ImageService
from src.services.audio_service import AudioService
from src.services.database_service import DatabaseService


@pytest.fixture
def sample_content_state():
    """Create a sample ContentState for testing."""
    return ContentState(
        workflow_id="test-workflow-123",
        status=WorkflowStatus.INITIATED,
        user_input="Create a blog post about AI",
        content_type="blog_post",
        target_platforms=["linkedin", "twitter"]
    )


@pytest.fixture
def mock_monitoring():
    """Create a mock monitoring instance."""
    mock = Mock(spec=Monitoring)
    mock.workflow_id = "test-workflow-123"
    mock.info = Mock()
    mock.error = Mock()
    mock.warning = Mock()
    return mock


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    mock = AsyncMock(spec=LLMService)
    mock.generate_text.return_value = {
        "content": "Generated text content",
        "metadata": {"model": "gemini-2.0-flash", "tokens": 150}
    }
    return mock


@pytest.fixture
def mock_image_service():
    """Create a mock Image service."""
    mock = AsyncMock(spec=ImageService)
    mock.generate_image.return_value = {
        "image_url": "https://example.com/generated-image.jpg",
        "metadata": {"model": "imagen-4", "style": "professional"}
    }
    return mock


@pytest.fixture
def mock_audio_service():
    """Create a mock Audio service."""
    mock = AsyncMock(spec=AudioService)
    mock.text_to_speech.return_value = {
        "audio_url": "https://example.com/generated-audio.mp3",
        "metadata": {"voice": "professional", "duration": 30}
    }
    mock.speech_to_text.return_value = {
        "transcript": "Transcribed text content",
        "confidence": 0.95
    }
    return mock


@pytest.fixture
def mock_database_service():
    """Create a mock Database service."""
    mock = AsyncMock(spec=DatabaseService)
    mock.save_content.return_value = {"id": "content-123", "status": "saved"}
    mock.get_content.return_value = {
        "id": "content-123",
        "content": "Sample content",
        "created_at": "2024-01-01T00:00:00Z"
    }
    return mock


@pytest.fixture
def mock_base_agent():
    """Create a mock base agent for testing."""
    class MockAgent(BaseAgent):
        def __init__(self, name: str = "MockAgent"):
            super().__init__(name)
        
        def execute(self, state: ContentState) -> ContentState:
            state.increment_step()
            return state
    
    return MockAgent()


@pytest.fixture
def sample_workflow_config():
    """Sample workflow configuration for testing."""
    return {
        "content_type": "blog_post",
        "target_platforms": ["linkedin", "twitter"],
        "brand_guidelines": {
            "tone": "professional",
            "style": "informative",
            "target_audience": "business professionals"
        },
        "quality_thresholds": {
            "readability_score": 0.8,
            "brand_compliance": 0.9,
            "platform_optimization": 0.85
        }
    }


@pytest.fixture
def sample_api_request():
    """Sample API request data for testing."""
    return {
        "user_input": "Create a blog post about AI trends in 2024",
        "content_type": "blog_post",
        "target_platforms": ["linkedin", "medium"],
        "brand_guidelines": {
            "tone": "professional",
            "style": "thought-leadership"
        }
    }


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset any global state between tests."""
    # This fixture runs automatically before each test
    # Add any global state cleanup here
    yield
    # Cleanup after test if needed


# Test configuration
pytest_plugins = []

# Async test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()