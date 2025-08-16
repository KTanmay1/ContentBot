"""Unit tests for BaseAgent class."""

import pytest
from unittest.mock import Mock, patch

from src.agents.base_agent import BaseAgent, AgentResult
from src.models.state_models import ContentState, WorkflowStatus
from src.core.error_handling import AgentException
from src.core.monitoring import get_monitoring


class NoopAgent(BaseAgent):
    """Test agent that performs no operation."""
    
    def execute(self, state: ContentState) -> ContentState:
        state.text_content["noop"] = "ok"
        return state


class ErrorAgent(BaseAgent):
    """Test agent that raises an error."""
    
    def execute(self, state: ContentState) -> ContentState:
        raise AgentException("Test error")


class SlowAgent(BaseAgent):
    """Test agent that simulates slow processing."""
    
    def execute(self, state: ContentState) -> ContentState:
        import time
        time.sleep(0.1)  # Small delay for testing
        state.text_content["slow"] = "completed"
        return state


class TestBaseAgent:
    """Test cases for BaseAgent class."""
    
    def test_base_agent_initialization(self):
        """Test BaseAgent initialization."""
        agent = NoopAgent()
        assert agent.name == "NoopAgent"
        assert hasattr(agent, 'execute')
    
    def test_base_agent_custom_name(self):
        """Test BaseAgent with custom name."""
        agent = NoopAgent(name="CustomAgent")
        assert agent.name == "CustomAgent"
    
    def test_base_agent_run_success(self):
        """Test successful agent execution."""
        agent = NoopAgent()
        state = ContentState(workflow_id="wf-a", status=WorkflowStatus.INITIATED)
        result = agent.run(state)
        
        assert result.state.text_content["noop"] == "ok"
        assert result.state.status in (WorkflowStatus.IN_PROGRESS, WorkflowStatus.INITIATED)
        assert result.state.current_agent == agent.name
    
    def test_base_agent_run_with_error(self):
        """Test agent execution with error."""
        agent = ErrorAgent()
        state = ContentState(workflow_id="test-456")
        
        result = agent.run(state)
        
        assert isinstance(result, AgentResult)
        assert result.state.status == WorkflowStatus.FAILED
    
    def test_base_agent_step_increment(self):
        """Test that agent execution increments step count."""
        agent = NoopAgent()
        state = ContentState(workflow_id="wf-c", status=WorkflowStatus.INITIATED)
        initial_step = state.step_count
        
        result = agent.run(state)
        assert result.state.step_count == initial_step + 1
    
    def test_base_agent_monitoring_integration(self):
        """Test monitoring integration."""
        agent = NoopAgent()
        state = ContentState(workflow_id="wf-d", status=WorkflowStatus.INITIATED)
        
        with patch('src.agents.base_agent.get_monitoring') as mock_get_monitoring:
            mock_monitoring = Mock()
            mock_get_monitoring.return_value = mock_monitoring
            
            result = agent.run(state)
            
            # Verify monitoring was called
            mock_get_monitoring.assert_called_with(state.workflow_id)
            # Check that info method was called for before_execute, after_execute, and success
            assert mock_monitoring.info.call_count >= 2
    
    def test_base_agent_current_agent_tracking(self):
        """Test that current agent is properly tracked."""
        agent = NoopAgent()
        state = ContentState(workflow_id="wf-e", status=WorkflowStatus.INITIATED)
        
        result = agent.run(state)
        assert result.state.current_agent == "NoopAgent"
    
    def test_base_agent_error_logging(self):
        """Test error logging in agent execution."""
        agent = ErrorAgent()
        state = ContentState(workflow_id="wf-f", status=WorkflowStatus.INITIATED)
        
        with patch('src.agents.base_agent.get_monitoring') as mock_get_monitoring:
            mock_monitoring = Mock()
            mock_get_monitoring.return_value = mock_monitoring
            
            result = agent.run(state)
            
            # Check that error was logged to monitoring
            assert mock_monitoring.error.call_count >= 1
            assert result.state.status == WorkflowStatus.FAILED
    
    def test_base_agent_abstract_execute(self):
        """Test that BaseAgent.execute is abstract."""
        with pytest.raises(TypeError):
            # Should not be able to instantiate BaseAgent directly
            BaseAgent()
    
    def test_base_agent_state_preservation(self):
        """Test that agent preserves existing state data."""
        agent = NoopAgent()
        state = ContentState(workflow_id="wf-g", status=WorkflowStatus.INITIATED)
        
        # Add some existing data
        state.text_content["existing"] = "data"
        state.quality_scores["test"] = 0.8
        
        result = agent.run(state)
        
        # Verify existing data is preserved
        assert result.state.text_content["existing"] == "data"
        assert result.state.quality_scores["test"] == 0.8
        # Verify new data is added
        assert result.state.text_content["noop"] == "ok"
    
    def test_base_agent_workflow_id_preservation(self):
        """Test that workflow ID is preserved."""
        agent = NoopAgent()
        workflow_id = "wf-preserve-test"
        state = ContentState(workflow_id=workflow_id, status=WorkflowStatus.INITIATED)
        
        result = agent.run(state)
        assert result.state.workflow_id == workflow_id
    
    def test_base_agent_multiple_executions(self):
        """Test multiple executions of the same agent."""
        agent = NoopAgent()
        state = ContentState(workflow_id="wf-multi", status=WorkflowStatus.INITIATED)
        
        # First execution
        result1 = agent.run(state)
        step_count_1 = result1.state.step_count
        
        # Second execution
        result2 = agent.run(result1.state)
        step_count_2 = result2.state.step_count
        
        assert step_count_2 == step_count_1 + 1
        assert result2.state.current_agent == "NoopAgent"
    
    @patch('src.agents.base_agent.get_monitoring')
    def test_base_agent_performance_tracking(self, mock_get_monitoring):
        """Test performance tracking in agent execution."""
        mock_monitoring = Mock()
        mock_get_monitoring.return_value = mock_monitoring
        
        agent = SlowAgent()
        state = ContentState(workflow_id="wf-perf", status=WorkflowStatus.INITIATED)
        
        result = agent.run(state)
        
        # Verify monitoring calls were made
        assert mock_monitoring.info.call_count >= 2  # Start and end calls
        
        # Verify execution completed successfully despite delay
        assert result.state.text_content["slow"] == "completed"


class TestAgentResult:
    """Test cases for AgentResult class."""
    
    def test_agent_result_success(self):
        """Test successful AgentResult creation."""
        from src.core.workflow_engine import AgentResult
        
        state = ContentState(workflow_id="wf-result", status=WorkflowStatus.COMPLETED)
        result = AgentResult(state=state)
        
        assert result.state == state
    
    def test_agent_result_failure(self):
        """Test failed AgentResult creation."""
        from src.core.workflow_engine import AgentResult
        
        state = ContentState(workflow_id="wf-result-fail", status=WorkflowStatus.FAILED)
        result = AgentResult(state=state)
        
        assert result.state == state