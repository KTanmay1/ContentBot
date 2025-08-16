# ViraLearn LangGraph Implementation Specification

## Critical Gap Analysis

**Current Status**: The existing deliverables provide excellent conceptual architecture but are **missing critical LangGraph-specific implementation details** needed for actual development.

**LangGraph Readiness**: Only **30%** of required LangGraph components have adequate implementation guidance.

**Critical Missing Components**:
- StateGraph construction and configuration
- Node and edge definitions with actual LangGraph syntax
- Conditional edge routing logic
- Graph compilation and invocation patterns
- State reducer implementations
- Human-in-the-loop interrupts and resumption
- LangGraph checkpointing and persistence

---

## Complete LangGraph Implementation Guide

### 1. Graph Construction & Configuration

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, List
import operator

# State Schema with LangGraph Annotations
class ContentState(TypedDict):
    # Core workflow data
    workflow_id: str
    user_id: str
    status: str
    current_agent: str
    step_count: int
    
    # Input and analysis
    original_input: dict
    input_analysis: dict
    
    # Content generation
    content_plan: dict
    text_content: Annotated[dict, operator.add]  # Mergeable state
    image_content: Annotated[dict, operator.add]
    audio_content: Annotated[dict, operator.add]
    
    # Quality control
    quality_scores: dict
    quality_issues: Annotated[List[dict], operator.add]
    
    # Platform optimization  
    platform_content: dict
    
    # Messages for agent communication
    messages: Annotated[List, operator.add]
    
    # Error handling
    error_log: Annotated[List[dict], operator.add]
    retry_count: int

# Graph Construction Function
def create_viralearn_graph() -> StateGraph:
    """Create the complete ViraLearn workflow graph."""
    
    # Initialize graph with state schema
    workflow = StateGraph(ContentState)
    
    # Add all agent nodes
    workflow.add_node("input_analyzer", input_analyzer_node)
    workflow.add_node("content_planner", content_planner_node)
    workflow.add_node("text_generator", text_generator_node)
    workflow.add_node("image_generator", image_generator_node) 
    workflow.add_node("audio_processor", audio_processor_node)
    workflow.add_node("quality_assurance", quality_assurance_node)
    workflow.add_node("brand_voice", brand_voice_node)
    workflow.add_node("cross_platform", cross_platform_node)
    workflow.add_node("human_review", human_review_node)
    
    # Add tool node for external services
    tools = [gemini_tool, imagen_tool, audio_tool]
    tool_node = ToolNode(tools)
    workflow.add_node("tools", tool_node)
    
    # Define edges (workflow transitions)
    workflow.add_edge("input_analyzer", "content_planner")
    workflow.add_edge("content_planner", "parallel_generation")
    workflow.add_edge("parallel_generation", "quality_assurance")
    
    # Conditional edges for workflow routing
    workflow.add_conditional_edges(
        "quality_assurance",
        quality_gate_condition,
        {
            "approved": "brand_voice",
            "needs_improvement": "parallel_generation",
            "human_review": "human_review"
        }
    )
    
    workflow.add_conditional_edges(
        "brand_voice", 
        brand_compliance_condition,
        {
            "compliant": "cross_platform",
            "needs_revision": "text_generator"
        }
    )
    
    workflow.add_conditional_edges(
        "cross_platform",
        completion_condition,
        {
            "complete": END,
            "needs_review": "human_review"
        }
    )
    
    workflow.add_conditional_edges(
        "human_review",
        human_decision_condition,
        {
            "approved": END,
            "revise": "parallel_generation",
            "reject": END
        }
    )
    
    # Set entry point
    workflow.set_entry_point("input_analyzer")
    
    # Configure checkpointing for state persistence
    memory = MemorySaver()
    
    # Compile graph with configuration
    compiled_graph = workflow.compile(
        checkpointer=memory,
        interrupt_before=["human_review"],  # Human-in-the-loop
        interrupt_after=["quality_assurance"]  # Quality gate
    )
    
    return compiled_graph
```

### 2. Agent Node Implementations

```python
# Input Analyzer Node
async def input_analyzer_node(state: ContentState) -> ContentState:
    """
    LangGraph node for input analysis.
    
    This function signature is required by LangGraph:
    - Takes state as input
    - Returns updated state
    - All state updates are automatically merged
    """
    
    try:
        # Initialize agent
        analyzer = InputAnalyzer()
        
        # Extract input data
        original_input = state["original_input"]
        
        # Perform analysis using the agent
        analysis_result = await analyzer.analyze_multimodal_input(original_input)
        
        # Update state with analysis results
        return {
            **state,
            "input_analysis": analysis_result,
            "status": "analyzing_complete", 
            "current_agent": "input_analyzer",
            "step_count": state.get("step_count", 0) + 1,
            "messages": [
                {
                    "role": "system",
                    "content": f"Input analysis completed. Found {len(analysis_result.get('themes', []))} themes.",
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
        
    except Exception as e:
        # Error handling with state update
        error_entry = {
            "agent": "input_analyzer",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            **state,
            "status": "error",
            "error_log": [error_entry],
            "retry_count": state.get("retry_count", 0) + 1
        }

# Content Planner Node
async def content_planner_node(state: ContentState) -> ContentState:
    """LangGraph node for content planning."""
    
    planner = ContentPlanner()
    
    # Use analysis results from previous node
    input_analysis = state["input_analysis"]
    user_preferences = state.get("user_preferences", {})
    
    # Create content strategy
    content_plan = await planner.create_content_strategy(
        analysis=input_analysis,
        preferences=user_preferences
    )
    
    # Define generation tasks
    generation_tasks = planner.define_generation_tasks(content_plan)
    
    return {
        **state,
        "content_plan": content_plan,
        "generation_tasks": generation_tasks,
        "status": "planning_complete",
        "current_agent": "content_planner",
        "step_count": state["step_count"] + 1
    }

# Parallel Generation Handler
async def parallel_generation_node(state: ContentState) -> ContentState:
    """
    Handle parallel content generation using LangGraph's Send API.
    """
    from langgraph.constants import Send
    
    # Get generation tasks from state
    tasks = state.get("generation_tasks", [])
    
    # Create Send objects for parallel execution
    sends = []
    for task in tasks:
        if task["type"] == "text":
            sends.append(Send("text_generator", {"task": task, **state}))
        elif task["type"] == "image":
            sends.append(Send("image_generator", {"task": task, **state}))
        elif task["type"] == "audio":
            sends.append(Send("audio_processor", {"task": task, **state}))
    
    return sends

# Text Generator Node with Tool Integration
async def text_generator_node(state: ContentState) -> ContentState:
    """LangGraph node for text generation with tool calling."""
    
    generator = TextGenerator()
    
    # Get task from state
    task = state.get("task", {})
    content_plan = state.get("content_plan", {})
    
    # Generate text content
    generated_text = await generator.generate_content(
        task=task,
        content_plan=content_plan,
        brand_guidelines=state.get("brand_guidelines", {})
    )
    
    # Update state with generated content
    text_content_update = {
        task.get("content_type", "blog_post"): generated_text
    }
    
    return {
        **state,
        "text_content": text_content_update,  # Will be merged due to Annotated type
        "status": "text_generation_complete",
        "messages": [
            {
                "role": "assistant", 
                "content": f"Generated {task.get('content_type')} content: {len(generated_text)} characters",
                "timestamp": datetime.now().isoformat()
            }
        ]
    }

# Quality Assurance Node
async def quality_assurance_node(state: ContentState) -> ContentState:
    """LangGraph node for quality assessment."""
    
    qa_agent = QualityAssurance()
    
    # Assess all generated content
    text_content = state.get("text_content", {})
    image_content = state.get("image_content", {})
    
    quality_results = await qa_agent.comprehensive_quality_check(
        text_content=text_content,
        image_content=image_content,
        quality_criteria=state.get("quality_requirements", {})
    )
    
    return {
        **state,
        "quality_scores": quality_results["scores"],
        "quality_issues": quality_results["issues"],
        "status": "quality_assessment_complete",
        "current_agent": "quality_assurance",
        "step_count": state["step_count"] + 1
    }

# Human Review Node with Interrupts
async def human_review_node(state: ContentState) -> ContentState:
    """
    LangGraph node for human review with interrupt/resume capability.
    
    This node will cause the graph to pause and wait for human input.
    """
    
    # Check if we're resuming from an interrupt
    if state.get("human_review_status") == "pending":
        # This is a resume - human feedback should be in state
        human_feedback = state.get("human_feedback", {})
        
        if human_feedback.get("action") == "approve":
            return {
                **state,
                "status": "approved",
                "human_review_status": "completed",
                "approval_timestamp": datetime.now().isoformat()
            }
        elif human_feedback.get("action") == "revise":
            return {
                **state,
                "status": "needs_revision", 
                "human_review_status": "completed",
                "revision_notes": human_feedback.get("notes", "")
            }
        else:
            return {
                **state,
                "status": "rejected",
                "human_review_status": "completed"
            }
    
    # Initial human review request
    return {
        **state,
        "status": "awaiting_human_review",
        "human_review_status": "pending",
        "review_requested_at": datetime.now().isoformat(),
        "messages": [
            {
                "role": "system",
                "content": "Content submitted for human review. Workflow paused.",
                "timestamp": datetime.now().isoformat()
            }
        ]
    }
```

### 3. Conditional Edge Functions

```python
# Quality Gate Condition
def quality_gate_condition(state: ContentState) -> str:
    """
    Determine next step based on quality assessment.
    
    Returns:
        str: Next node name or condition
    """
    
    quality_scores = state.get("quality_scores", {})
    overall_score = quality_scores.get("overall", 0.0)
    
    # Check for critical quality issues
    critical_issues = [
        issue for issue in state.get("quality_issues", [])
        if issue.get("severity") == "critical"
    ]
    
    if critical_issues:
        return "needs_improvement"
    elif overall_score >= 0.8:
        return "approved"
    elif overall_score >= 0.6:
        return "human_review"  # Borderline quality
    else:
        return "needs_improvement"

# Brand Compliance Condition  
def brand_compliance_condition(state: ContentState) -> str:
    """Determine if content meets brand guidelines."""
    
    brand_scores = state.get("brand_compliance", {})
    compliance_score = brand_scores.get("overall_compliance", 0.0)
    
    if compliance_score >= 0.9:
        return "compliant"
    else:
        return "needs_revision"

# Completion Condition
def completion_condition(state: ContentState) -> str:
    """Determine if workflow is complete."""
    
    # Check if all required platforms are optimized
    target_platforms = state.get("target_platforms", [])
    platform_content = state.get("platform_content", {})
    
    platforms_ready = all(
        platform in platform_content 
        for platform in target_platforms
    )
    
    # Check if human review is required
    user_preferences = state.get("user_preferences", {})
    requires_human_review = user_preferences.get("require_human_review", False)
    
    if platforms_ready and not requires_human_review:
        return "complete"
    elif platforms_ready and requires_human_review:
        return "needs_review"
    else:
        return "needs_optimization"

# Human Decision Condition
def human_decision_condition(state: ContentState) -> str:
    """Route based on human reviewer decision."""
    
    human_feedback = state.get("human_feedback", {})
    action = human_feedback.get("action")
    
    if action == "approve":
        return "approved"
    elif action == "revise":
        return "revise" 
    else:
        return "reject"
```

### 4. Graph Invocation Patterns

```python
# Basic Graph Invocation
async def run_content_workflow(
    input_data: dict,
    user_preferences: dict = None,
    config: dict = None
) -> dict:
    """
    Run the complete ViraLearn content creation workflow.
    
    Args:
        input_data: User's input content
        user_preferences: User configuration
        config: LangGraph execution configuration
        
    Returns:
        dict: Final workflow state with generated content
    """
    
    # Create graph
    graph = create_viralearn_graph()
    
    # Initialize state
    initial_state = {
        "workflow_id": str(uuid.uuid4()),
        "user_id": config.get("user_id") if config else "default",
        "original_input": input_data,
        "user_preferences": user_preferences or {},
        "status": "initiated",
        "step_count": 0,
        "messages": [],
        "text_content": {},
        "image_content": {},
        "audio_content": {},
        "quality_issues": [],
        "error_log": [],
        "retry_count": 0
    }
    
    # Execute workflow
    try:
        result = await graph.ainvoke(
            initial_state,
            config=config or {"configurable": {"thread_id": initial_state["workflow_id"]}}
        )
        return result
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise

# Streaming Invocation for Real-time Updates
async def stream_content_workflow(
    input_data: dict,
    user_preferences: dict = None
) -> AsyncIterator[dict]:
    """
    Stream workflow execution with real-time updates.
    
    Yields:
        dict: Partial state updates as workflow progresses
    """
    
    graph = create_viralearn_graph()
    
    initial_state = {
        "workflow_id": str(uuid.uuid4()),
        "original_input": input_data,
        "user_preferences": user_preferences or {},
        "status": "initiated"
    }
    
    config = {"configurable": {"thread_id": initial_state["workflow_id"]}}
    
    async for chunk in graph.astream(initial_state, config=config):
        yield chunk

# Human-in-the-Loop Handling
async def handle_human_review(
    workflow_id: str,
    human_feedback: dict,
    graph: StateGraph
) -> dict:
    """
    Resume workflow after human review.
    
    Args:
        workflow_id: Workflow identifier
        human_feedback: Human reviewer feedback
        graph: Compiled LangGraph instance
        
    Returns:
        dict: Updated workflow state
    """
    
    config = {"configurable": {"thread_id": workflow_id}}
    
    # Get current state
    current_state = graph.get_state(config)
    
    # Update state with human feedback
    updated_state = {
        **current_state.values,
        "human_feedback": human_feedback,
        "human_review_status": "feedback_received"
    }
    
    # Resume workflow from interrupt
    result = await graph.ainvoke(updated_state, config=config)
    
    return result

# Error Recovery and Retry
async def retry_workflow_step(
    workflow_id: str,
    failed_node: str,
    graph: StateGraph,
    max_retries: int = 3
) -> dict:
    """
    Retry a failed workflow step with exponential backoff.
    
    Args:
        workflow_id: Workflow identifier
        failed_node: Name of the failed node
        graph: Compiled LangGraph instance
        max_retries: Maximum retry attempts
        
    Returns:
        dict: Updated workflow state
    """
    
    config = {"configurable": {"thread_id": workflow_id}}
    current_state = graph.get_state(config)
    
    retry_count = current_state.values.get("retry_count", 0)
    
    if retry_count >= max_retries:
        # Max retries exceeded - mark as failed
        updated_state = {
            **current_state.values,
            "status": "failed",
            "error_message": f"Max retries exceeded for {failed_node}"
        }
        return updated_state
    
    # Exponential backoff
    await asyncio.sleep(2 ** retry_count)
    
    # Update retry count and resume
    updated_state = {
        **current_state.values,
        "retry_count": retry_count + 1,
        "status": "retrying"
    }
    
    result = await graph.ainvoke(updated_state, config=config)
    return result
```

### 5. Integration with FastAPI

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="ViraLearn API")

# Global graph instance
viralearn_graph = create_viralearn_graph()

class WorkflowRequest(BaseModel):
    input_data: dict
    user_preferences: dict = {}
    user_id: str

class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    message: str

@app.post("/api/v1/workflows", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks
) -> WorkflowResponse:
    """Create new content generation workflow using LangGraph."""
    
    # Generate workflow ID
    workflow_id = str(uuid.uuid4())
    
    # Start workflow in background
    background_tasks.add_task(
        run_workflow_background,
        workflow_id,
        request.input_data,
        request.user_preferences,
        request.user_id
    )
    
    return WorkflowResponse(
        workflow_id=workflow_id,
        status="initiated",
        message="Workflow started successfully"
    )

async def run_workflow_background(
    workflow_id: str,
    input_data: dict,
    user_preferences: dict,
    user_id: str
):
    """Background task to run LangGraph workflow."""
    
    config = {
        "configurable": {"thread_id": workflow_id},
        "user_id": user_id
    }
    
    try:
        result = await run_content_workflow(
            input_data=input_data,
            user_preferences=user_preferences,
            config=config
        )
        
        # Store final result in database
        await store_workflow_result(workflow_id, result)
        
    except Exception as e:
        logger.error(f"Background workflow {workflow_id} failed: {e}")
        await store_workflow_error(workflow_id, str(e))

@app.get("/api/v1/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get current workflow status using LangGraph state."""
    
    config = {"configurable": {"thread_id": workflow_id}}
    
    try:
        state = viralearn_graph.get_state(config)
        
        return {
            "workflow_id": workflow_id,
            "status": state.values.get("status", "unknown"),
            "current_agent": state.values.get("current_agent"),
            "step_count": state.values.get("step_count", 0),
            "messages": state.values.get("messages", [])[-5:]  # Last 5 messages
        }
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {e}")

@app.post("/api/v1/workflows/{workflow_id}/human-review")
async def submit_human_review(
    workflow_id: str,
    feedback: dict
):
    """Submit human review feedback to resume workflow."""
    
    try:
        result = await handle_human_review(
            workflow_id=workflow_id,
            human_feedback=feedback,
            graph=viralearn_graph
        )
        
        return {
            "workflow_id": workflow_id,
            "status": result.get("status"),
            "message": "Human review processed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process review: {e}")

@app.get("/api/v1/workflows/{workflow_id}/stream")
async def stream_workflow_progress(workflow_id: str):
    """Stream workflow progress in real-time."""
    
    async def generate():
        config = {"configurable": {"thread_id": workflow_id}}
        
        async for chunk in viralearn_graph.astream(None, config=config):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/plain")
```

### 6. Complete File Structure for LangGraph Implementation

```
src/
├── langgraph/
│   ├── __init__.py
│   ├── graph_builder.py          # create_viralearn_graph()
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── input_analyzer_node.py
│   │   ├── content_planner_node.py  
│   │   ├── generator_nodes.py     # text, image, audio generators
│   │   ├── quality_nodes.py       # QA, brand voice, cross-platform
│   │   └── human_review_node.py
│   ├── conditions/
│   │   ├── __init__.py
│   │   ├── routing_conditions.py  # quality_gate_condition, etc.
│   │   └── completion_conditions.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── gemini_tool.py
│   │   ├── imagen_tool.py
│   │   └── audio_tool.py
│   └── utils/
│       ├── __init__.py
│       ├── state_management.py
│       └── checkpointing.py
```

This comprehensive LangGraph specification fills the critical gaps identified in the analysis and provides the actual implementation details needed for development.