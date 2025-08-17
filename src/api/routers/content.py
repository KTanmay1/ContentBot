"""Content API router for ViraLearn ContentBot.

This router handles content-related operations including content generation,
analysis, quality assessment, and content management.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from fastapi import APIRouter, HTTPException, Depends, Query, Path, UploadFile, File
    from fastapi.responses import JSONResponse
except ImportError:
    # Fallback for environments without FastAPI
    class APIRouter:
        def __init__(self, *args, **kwargs):
            pass
        def post(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def get(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def put(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def delete(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
    
    def Depends(dependency):
        return dependency
    
    def Query(default=None, **kwargs):
        return default
    
    def Path(**kwargs):
        return None
    
    class UploadFile:
        pass
    
    def File():
        return None
    
    class JSONResponse:
        def __init__(self, content, status_code=200):
            self.content = content
            self.status_code = status_code

from ...models.api_models import CreateWorkflowRequest, CreateWorkflowResponse, WorkflowStatusResponse, ErrorResponse
from ...models.content_models import BlogPost, SocialPost
from ...core.error_handling import (
    AgentException, ValidationException, ResourceNotFoundException,
    create_error_response, error_handler
)
from ...utils.validators import (
    validate_workflow_input, validate_text_length, validate_content_metadata,
    validate_file_upload, sanitize_input
)
from ...services.database_service import DatabaseService
from ...core.workflow_engine import WorkflowEngine
from ...agents.input_analyzer import InputAnalyzer
from ...agents.content_planner import ContentPlanner
from ...agents.quality_assurance import QualityAssurance
from ...agents.human_review import HumanReview


# Create router instance
router = APIRouter(prefix="/content", tags=["content"])

# Initialize services
database_service = DatabaseService()
workflow_engine = WorkflowEngine()

# Initialize agents
input_analyzer = InputAnalyzer()
content_planner = ContentPlanner()
quality_assurance = QualityAssurance()
human_review = HumanReview()


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_content(
    request: Dict[str, Any],
    user_id: Optional[str] = Query(None, description="User ID for tracking")
):
    """Analyze content for themes, sentiment, and characteristics.
    
    Args:
        request: Content analysis request containing text_content
        user_id: Optional user ID for tracking
        
    Returns:
        Analysis results including themes, sentiment, keywords, etc.
    """
    try:
        # Validate input
        if not request or "text_content" not in request:
            raise ValidationException("text_content is required")
        
        text_content = sanitize_input(request["text_content"])
        validate_text_length(text_content, min_length=1, max_length=50000, field_name="text_content")
        
        # Create content state for analysis
        from ...models.state_models import ContentState, WorkflowStatus
        
        state = ContentState(
            workflow_id=f"analysis_{int(datetime.utcnow().timestamp())}",
            status=WorkflowStatus.RUNNING,
            text_content=text_content,
            original_input=request,
            step_count=0
        )
        
        # Run input analysis
        result = await input_analyzer.execute(state)
        
        if not result.success:
            raise AgentException(f"Analysis failed: {result.error}")
        
        return {
            "success": True,
            "analysis": result.data,
            "workflow_id": state.workflow_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AgentException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        await error_handler.handle_error(e, {"endpoint": "analyze_content", "user_id": user_id})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/plan", response_model=Dict[str, Any])
async def plan_content(
    request: Dict[str, Any],
    user_id: Optional[str] = Query(None, description="User ID for tracking")
):
    """Create a content plan based on input analysis.
    
    Args:
        request: Content planning request
        user_id: Optional user ID for tracking
        
    Returns:
        Content planning results including strategy and structure
    """
    try:
        # Validate input
        validate_workflow_input(request)
        
        text_content = sanitize_input(request["text_content"])
        
        # Create content state
        from ...models.state_models import ContentState, WorkflowStatus
        
        state = ContentState(
            workflow_id=f"planning_{int(datetime.utcnow().timestamp())}",
            status=WorkflowStatus.RUNNING,
            text_content=text_content,
            original_input=request,
            step_count=0
        )
        
        # Run analysis first
        analysis_result = await input_analyzer.execute(state)
        if analysis_result.success:
            state.analysis_data = analysis_result.data
        
        # Run content planning
        planning_result = await content_planner.execute(state)
        
        if not planning_result.success:
            raise AgentException(f"Planning failed: {planning_result.error}")
        
        return {
            "success": True,
            "plan": planning_result.data,
            "analysis": analysis_result.data if analysis_result.success else None,
            "workflow_id": state.workflow_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AgentException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        await error_handler.handle_error(e, {"endpoint": "plan_content", "user_id": user_id})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/assess-quality", response_model=Dict[str, Any])
async def assess_content_quality(
    request: Dict[str, Any],
    user_id: Optional[str] = Query(None, description="User ID for tracking")
):
    """Assess content quality and provide improvement suggestions.
    
    Args:
        request: Quality assessment request
        user_id: Optional user ID for tracking
        
    Returns:
        Quality assessment results and suggestions
    """
    try:
        # Validate input
        if not request or "text_content" not in request:
            raise ValidationException("text_content is required")
        
        text_content = sanitize_input(request["text_content"])
        validate_text_length(text_content, min_length=1, max_length=50000, field_name="text_content")
        
        # Create content state
        from ...models.state_models import ContentState, WorkflowStatus
        
        state = ContentState(
            workflow_id=f"qa_{int(datetime.utcnow().timestamp())}",
            status=WorkflowStatus.RUNNING,
            text_content=text_content,
            original_input=request,
            step_count=0
        )
        
        # Run quality assessment
        qa_result = await quality_assurance.execute(state)
        
        if not qa_result.success:
            raise AgentException(f"Quality assessment failed: {qa_result.error}")
        
        return {
            "success": True,
            "quality_assessment": qa_result.data,
            "workflow_id": state.workflow_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AgentException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        await error_handler.handle_error(e, {"endpoint": "assess_quality", "user_id": user_id})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/generate/blog", response_model=Dict[str, Any])
async def generate_blog_post(
    request: Dict[str, Any],
    user_id: Optional[str] = Query(None, description="User ID for tracking")
):
    """Generate a blog post based on input content.
    
    Args:
        request: Blog generation request
        user_id: Optional user ID for tracking
        
    Returns:
        Generated blog post structure
    """
    try:
        # Validate input
        validate_workflow_input(request)
        
        # Create workflow for blog generation using workflow coordinator
        from uuid import uuid4
        from src.agents.workflow_coordinator import WorkflowCoordinator
        from src.models import ContentState
        
        workflow_id = str(uuid4())
        # Structure input for agents - they expect "text" field in original_input
        structured_input = {
            "text": request.get("text_content", ""),
            "content_type": request.get("content_type", "blog_post"),
            "platform": request.get("platform", "blog"),
            "llm_model": request.get("llm_model", "mistral")
        }
        
        state = ContentState(
            workflow_id=workflow_id, 
            status="initiated", 
            original_input=structured_input, 
            user_id=user_id
        )
        
        # Execute workflow using coordinator
        coordinator = WorkflowCoordinator()
        result = coordinator.run(state)
        
        if result.state.status == "completed" and result.state.final_content:
            return {
                "success": True,
                "blog_post": result.state.final_content,
                "workflow_id": workflow_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        elif result.state.status == "failed":
            raise AgentException(f"Blog generation failed: {result.state.error_message or 'Unknown error'}")
        else:
            # Return partial result if available
            return {
                "success": False,
                "message": "Content generation in progress",
                "workflow_id": workflow_id,
                "status": result.state.status,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # If we get here, the workflow didn't complete in time
        return {
            "success": False,
            "message": "Blog generation is taking longer than expected",
            "workflow_id": workflow_id,
            "status": "in_progress",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AgentException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        await error_handler.handle_error(e, {"endpoint": "generate_blog", "user_id": user_id})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/generate/social", response_model=Dict[str, Any])
async def generate_social_post(
    request: Dict[str, Any],
    platform: str = Query(..., description="Target social media platform"),
    user_id: Optional[str] = Query(None, description="User ID for tracking")
):
    """Generate a social media post for a specific platform.
    
    Args:
        request: Social post generation request
        platform: Target platform (twitter, facebook, linkedin, instagram)
        user_id: Optional user ID for tracking
        
    Returns:
        Generated social media post
    """
    try:
        # Validate platform
        valid_platforms = ['twitter', 'facebook', 'linkedin', 'instagram']
        if platform not in valid_platforms:
            raise ValidationException(f"Platform must be one of: {', '.join(valid_platforms)}")
        
        # Validate input
        validate_workflow_input(request)
        
        # Build structured input
        from uuid import uuid4
        from src.agents.workflow_coordinator import WorkflowCoordinator
        from src.models import ContentState
        
        workflow_id = str(uuid4())
        structured_input = {
            "text": request.get("text_content", ""),
            "content_type": "social_post",
            "platform": platform,
            "llm_model": request.get("llm_model", "mistral")
        }
        
        state = ContentState(
            workflow_id=workflow_id,
            status="initiated",
            original_input=structured_input,
            user_id=user_id
        )
        
        # Execute workflow synchronously using coordinator
        coordinator = WorkflowCoordinator()
        result = coordinator.run(state)
        
        if result.state.status == "completed" and result.state.final_content:
            return {
                "success": True,
                "social_post": result.state.final_content,
                "platform": platform,
                "workflow_id": workflow_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        elif result.state.status == "failed":
            raise AgentException(f"Social post generation failed: {result.state.error_message or 'Unknown error'}")
        else:
            return {
                "success": False,
                "message": "Content generation in progress",
                "workflow_id": workflow_id,
                "platform": platform,
                "status": result.state.status,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AgentException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        await error_handler.handle_error(e, {"endpoint": "generate_social", "user_id": user_id, "platform": platform})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/content/{content_id}", response_model=Dict[str, Any])
async def get_content(
    content_id: str = Path(..., description="Content ID to retrieve"),
    user_id: Optional[str] = Query(None, description="User ID for authorization")
):
    """Retrieve content by ID.
    
    Args:
        content_id: ID of the content to retrieve
        user_id: Optional user ID for authorization
        
    Returns:
        Content data
    """
    try:
        # Get content from database
        content_data = await database_service.get_content(content_id)
        
        if not content_data:
            raise ResourceNotFoundException(f"Content not found: {content_id}")
        
        # Basic authorization check (if user_id provided)
        if user_id and content_data.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "success": True,
            "content": content_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await error_handler.handle_error(e, {"endpoint": "get_content", "content_id": content_id, "user_id": user_id})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/content", response_model=Dict[str, Any])
async def list_content(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
):
    """List content with optional filtering.
    
    Args:
        user_id: Optional user ID filter
        content_type: Optional content type filter
        limit: Maximum number of items to return
        offset: Number of items to skip
        
    Returns:
        List of content items
    """
    try:
        # Build filter criteria
        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if content_type:
            filters["content_type"] = content_type
        
        # Get content list from database
        content_list = await database_service.list_content(
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "content": content_list,
            "count": len(content_list),
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        await error_handler.handle_error(e, {"endpoint": "list_content", "user_id": user_id})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/content/{content_id}", response_model=Dict[str, Any])
async def delete_content(
    content_id: str = Path(..., description="Content ID to delete"),
    user_id: Optional[str] = Query(None, description="User ID for authorization")
):
    """Delete content by ID.
    
    Args:
        content_id: ID of the content to delete
        user_id: Optional user ID for authorization
        
    Returns:
        Deletion confirmation
    """
    try:
        # Check if content exists and get user info
        content_data = await database_service.get_content(content_id)
        
        if not content_data:
            raise ResourceNotFoundException(f"Content not found: {content_id}")
        
        # Basic authorization check (if user_id provided)
        if user_id and content_data.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete content
        success = await database_service.delete_content(content_id)
        
        if not success:
            raise AgentException("Failed to delete content")
        
        return {
            "success": True,
            "message": f"Content {content_id} deleted successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await error_handler.handle_error(e, {"endpoint": "delete_content", "content_id": content_id, "user_id": user_id})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/upload", response_model=Dict[str, Any])
async def upload_content_file(
    file: UploadFile = File(...),
    user_id: Optional[str] = Query(None, description="User ID for tracking")
):
    """Upload a content file for processing.
    
    Args:
        file: File to upload
        user_id: Optional user ID for tracking
        
    Returns:
        Upload confirmation and file info
    """
    try:
        # Validate file
        if not file.filename:
            raise ValidationException("No file provided")
        
        file_data = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": 0  # Will be calculated when reading
        }
        
        # Read file content
        content = await file.read()
        file_data["size"] = len(content)
        
        # Validate file data
        validate_file_upload(file_data)
        
        # Store file (implementation depends on storage backend)
        file_id = f"file_{int(datetime.utcnow().timestamp())}_{file.filename}"
        
        # For now, just return success (actual storage implementation needed)
        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "size": file_data["size"],
            "content_type": file.content_type,
            "message": "File uploaded successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await error_handler.handle_error(e, {"endpoint": "upload_file", "user_id": user_id})
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint
@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint for the content API.
    
    Returns:
        Health status information
    """
    try:
        # Check database connectivity
        db_healthy = await database_service.health_check()
        
        # Check agent availability
        agents_healthy = all([
            hasattr(input_analyzer, 'execute'),
            hasattr(content_planner, 'execute'),
            hasattr(quality_assurance, 'execute'),
            hasattr(human_review, 'execute')
        ])
        
        overall_healthy = db_healthy and agents_healthy
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "database": "healthy" if db_healthy else "unhealthy",
            "agents": "healthy" if agents_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        await error_handler.handle_error(e, {"endpoint": "health_check"})
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }