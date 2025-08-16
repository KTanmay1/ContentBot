"""Integration tests for workflow API endpoints."""

import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
import uuid
import time

from src.api.routers.workflows import router as workflows_router
from src.api.routers.monitoring import router as monitoring_router
from src.models.state_models import WorkflowStatus


def create_app() -> FastAPI:
    """Create test FastAPI app with workflow and monitoring routers."""
    app = FastAPI()
    app.include_router(workflows_router)
    app.include_router(monitoring_router)
    return app


class TestHealthEndpoints:
    """Test cases for health and monitoring endpoints."""
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        app = create_app()
        client = TestClient(app)
        
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint."""
        app = create_app()
        client = TestClient(app)
        
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200
        # Metrics format depends on implementation
        assert isinstance(resp.json(), dict)


class TestWorkflowCreation:
    """Test cases for workflow creation."""
    
    def test_workflow_create_basic(self):
        """Test basic workflow creation."""
        app = create_app()
        client = TestClient(app)
        
        payload = {"input": {"text": "Create content about AI"}}
        response = client.post("/api/v1/workflows", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data
        assert isinstance(data["workflow_id"], str)
        assert len(data["workflow_id"]) > 0
    
    def test_workflow_create_with_content_type(self):
        """Test workflow creation with specific content type."""
        app = create_app()
        client = TestClient(app)
        
        payload = {
            "input": {
                "text": "Create a blog post about machine learning",
                "content_type": "blog"
            }
        }
        response = client.post("/api/v1/workflows", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data
    
    def test_workflow_create_with_platform_specs(self):
        """Test workflow creation with platform specifications."""
        app = create_app()
        client = TestClient(app)
        
        payload = {
            "input": {
                "text": "Create social media content",
                "platforms": ["twitter", "linkedin"],
                "content_type": "social"
            }
        }
        response = client.post("/api/v1/workflows", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data
    
    def test_workflow_create_invalid_input(self):
        """Test workflow creation with invalid input."""
        app = create_app()
        client = TestClient(app)
        
        # Empty payload
        response = client.post("/api/v1/workflows", json={})
        assert response.status_code == 422  # Validation error
        
        # Missing required fields
        response = client.post("/api/v1/workflows", json={"input": {}})
        assert response.status_code == 422
    
    def test_workflow_create_large_input(self):
        """Test workflow creation with large input text."""
        app = create_app()
        client = TestClient(app)
        
        large_text = "A" * 5000  # 5KB of text
        payload = {"input": {"text": large_text}}
        
        response = client.post("/api/v1/workflows", json=payload)
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 413, 422]


class TestWorkflowStatus:
    """Test cases for workflow status retrieval."""
    
    def test_workflow_create_and_fetch_status(self):
        """Test workflow creation and status retrieval."""
        app = create_app()
        client = TestClient(app)
        
        # Create workflow
        payload = {"input": {"text": "Create content about AI"}}
        create_response = client.post("/api/v1/workflows", json=payload)
        assert create_response.status_code == 200
        
        workflow_id = create_response.json()["workflow_id"]
        
        # Fetch status
        status_response = client.get(f"/api/v1/workflows/{workflow_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["status"] in ["completed", "in_progress", "initiated", "failed"]
    
    def test_workflow_status_nonexistent(self):
        """Test status retrieval for non-existent workflow."""
        app = create_app()
        client = TestClient(app)
        
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/workflows/{fake_id}")
        assert response.status_code == 404
    
    def test_workflow_status_invalid_id(self):
        """Test status retrieval with invalid workflow ID."""
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/api/v1/workflows/invalid-id")
        assert response.status_code in [400, 404, 422]  # Depends on validation


class TestWorkflowContent:
    """Test cases for workflow content retrieval."""
    
    def test_workflow_content_retrieval(self):
        """Test workflow content retrieval."""
        app = create_app()
        client = TestClient(app)
        
        # Create workflow
        payload = {"input": {"text": "Create content about AI"}}
        create_response = client.post("/api/v1/workflows", json=payload)
        workflow_id = create_response.json()["workflow_id"]
        
        # Get content
        content_response = client.get(f"/api/v1/workflows/{workflow_id}/content")
        assert content_response.status_code == 200
        
        content_data = content_response.json()
        assert "platform_content" in content_data
    
    def test_workflow_content_nonexistent(self):
        """Test content retrieval for non-existent workflow."""
        app = create_app()
        client = TestClient(app)
        
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/workflows/{fake_id}/content")
        assert response.status_code == 404


class TestHumanReview:
    """Test cases for human review functionality."""
    
    def test_human_review_pause_resume(self):
        """Test human review pause and resume functionality."""
        app = create_app()
        client = TestClient(app)
        
        # Create workflow
        payload = {"input": {"text": "Create content about AI"}}
        create_response = client.post("/api/v1/workflows", json=payload)
        workflow_id = create_response.json()["workflow_id"]
        
        # Pause for human review
        pause_response = client.post(f"/api/v1/workflows/{workflow_id}/pause")
        assert pause_response.status_code == 200
        assert pause_response.json()["status"] == "waiting_human"
        
        # Resume with approval
        resume_response = client.post(
            f"/api/v1/workflows/{workflow_id}/resume",
            json={"review": "approved"}
        )
        assert resume_response.status_code == 200
        assert resume_response.json()["status"] == "in_progress"
    
    def test_human_review_rejection(self):
        """Test human review with rejection."""
        app = create_app()
        client = TestClient(app)
        
        # Create and pause workflow
        payload = {"input": {"text": "Create content about AI"}}
        create_response = client.post("/api/v1/workflows", json=payload)
        workflow_id = create_response.json()["workflow_id"]
        
        pause_response = client.post(f"/api/v1/workflows/{workflow_id}/pause")
        assert pause_response.status_code == 200
        
        # Resume with rejection and feedback
        resume_response = client.post(
            f"/api/v1/workflows/{workflow_id}/resume",
            json={
                "review": "rejected",
                "feedback": "Content needs more technical details"
            }
        )
        assert resume_response.status_code == 200
        # Status depends on implementation - might restart or fail
        assert resume_response.json()["status"] in ["in_progress", "failed", "initiated"]
    
    def test_human_review_invalid_action(self):
        """Test human review with invalid action."""
        app = create_app()
        client = TestClient(app)
        
        # Create and pause workflow
        payload = {"input": {"text": "Create content about AI"}}
        create_response = client.post("/api/v1/workflows", json=payload)
        workflow_id = create_response.json()["workflow_id"]
        
        # Try to resume without pausing first
        resume_response = client.post(
            f"/api/v1/workflows/{workflow_id}/resume",
            json={"review": "approved"}
        )
        # Should fail if workflow is not in paused state
        assert resume_response.status_code in [400, 409]  # Bad request or conflict


class TestWorkflowLifecycle:
    """Test cases for complete workflow lifecycle."""
    
    def test_complete_workflow_lifecycle(self):
        """Test complete workflow from creation to completion."""
        app = create_app()
        client = TestClient(app)
        
        # 1. Create workflow
        payload = {"input": {"text": "Create a short blog post about Python"}}
        create_response = client.post("/api/v1/workflows", json=payload)
        assert create_response.status_code == 200
        
        workflow_id = create_response.json()["workflow_id"]
        
        # 2. Check initial status
        status_response = client.get(f"/api/v1/workflows/{workflow_id}")
        assert status_response.status_code == 200
        initial_status = status_response.json()["status"]
        assert initial_status in ["initiated", "in_progress"]
        
        # 3. Wait a bit and check status again (workflow might complete)
        time.sleep(0.1)
        status_response = client.get(f"/api/v1/workflows/{workflow_id}")
        assert status_response.status_code == 200
        
        # 4. Get content (should work regardless of completion status)
        content_response = client.get(f"/api/v1/workflows/{workflow_id}/content")
        assert content_response.status_code == 200
    
    def test_workflow_error_handling(self):
        """Test workflow error handling."""
        app = create_app()
        client = TestClient(app)
        
        # Create workflow with potentially problematic input
        payload = {"input": {"text": ""}}
        response = client.post("/api/v1/workflows", json=payload)
        
        # Should either reject empty input or handle gracefully
        if response.status_code == 200:
            workflow_id = response.json()["workflow_id"]
            
            # Check that workflow handles empty input gracefully
            status_response = client.get(f"/api/v1/workflows/{workflow_id}")
            assert status_response.status_code == 200
            
            status = status_response.json()["status"]
            assert status in ["failed", "completed", "in_progress"]
        else:
            # Input validation rejected empty text
            assert response.status_code == 422


class TestConcurrentWorkflows:
    """Test cases for concurrent workflow handling."""
    
    def test_multiple_concurrent_workflows(self):
        """Test handling of multiple concurrent workflows."""
        app = create_app()
        client = TestClient(app)
        
        # Create multiple workflows concurrently
        workflows = []
        for i in range(3):
            payload = {"input": {"text": f"Create content about topic {i}"}}
            response = client.post("/api/v1/workflows", json=payload)
            assert response.status_code == 200
            workflows.append(response.json()["workflow_id"])
        
        # Check that all workflows were created successfully
        assert len(workflows) == 3
        assert len(set(workflows)) == 3  # All IDs should be unique
        
        # Check status of all workflows
        for workflow_id in workflows:
            status_response = client.get(f"/api/v1/workflows/{workflow_id}")
            assert status_response.status_code == 200
    
    def test_workflow_isolation(self):
        """Test that workflows are properly isolated."""
        app = create_app()
        client = TestClient(app)
        
        # Create two different workflows
        payload1 = {"input": {"text": "Create content about AI"}}
        payload2 = {"input": {"text": "Create content about blockchain"}}
        
        response1 = client.post("/api/v1/workflows", json=payload1)
        response2 = client.post("/api/v1/workflows", json=payload2)
        
        workflow_id1 = response1.json()["workflow_id"]
        workflow_id2 = response2.json()["workflow_id"]
        
        # Workflows should have different IDs
        assert workflow_id1 != workflow_id2
        
        # Both should be accessible independently
        status1 = client.get(f"/api/v1/workflows/{workflow_id1}")
        status2 = client.get(f"/api/v1/workflows/{workflow_id2}")
        
        assert status1.status_code == 200
        assert status2.status_code == 200


class TestAPIValidation:
    """Test cases for API input validation."""
    
    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        app = create_app()
        client = TestClient(app)
        
        # Send invalid JSON
        response = client.post(
            "/api/v1/workflows",
            data="{invalid json}",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_content_type(self):
        """Test handling of missing content type."""
        app = create_app()
        client = TestClient(app)
        
        # Send JSON without content-type header
        response = client.post(
            "/api/v1/workflows",
            data='{"input": {"text": "test"}}'
        )
        # FastAPI should handle this gracefully
        assert response.status_code in [200, 422]
    
    def test_oversized_request(self):
        """Test handling of oversized requests."""
        app = create_app()
        client = TestClient(app)
        
        # Create very large payload
        huge_text = "A" * 100000  # 100KB
        payload = {"input": {"text": huge_text}}
        
        response = client.post("/api/v1/workflows", json=payload)
        # Should either handle or reject gracefully
        assert response.status_code in [200, 413, 422]


class TestAPIPerformance:
    """Test cases for API performance."""
    
    def test_response_time(self):
        """Test API response time for basic operations."""
        app = create_app()
        client = TestClient(app)
        
        start_time = time.time()
        response = client.get("/api/v1/health")
        end_time = time.time()
        
        assert response.status_code == 200
        # Health check should be fast (under 1 second)
        assert (end_time - start_time) < 1.0
    
    def test_workflow_creation_performance(self):
        """Test workflow creation performance."""
        app = create_app()
        client = TestClient(app)
        
        payload = {"input": {"text": "Quick test content"}}
        
        start_time = time.time()
        response = client.post("/api/v1/workflows", json=payload)
        end_time = time.time()
        
        assert response.status_code == 200
        # Workflow creation should be reasonably fast (under 5 seconds)
        assert (end_time - start_time) < 5.0