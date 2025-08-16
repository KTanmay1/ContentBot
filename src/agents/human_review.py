"""Human Review Agent for ViraLearn ContentBot.

This agent is responsible for managing human review processes,
collecting feedback, and facilitating human-in-the-loop workflows.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum

from ..models.state_models import ContentState
from ..services.database_service import DatabaseService
from .base_agent import BaseAgent, AgentResult


class ReviewStatus(Enum):
    """Review status enumeration."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    TIMEOUT = "timeout"


class ReviewPriority(Enum):
    """Review priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class HumanReview(BaseAgent):
    """Agent for managing human review processes."""
    
    def __init__(self, database_service: Optional[DatabaseService] = None):
        """Initialize the Human Review agent.
        
        Args:
            database_service: Database service for storing review data
        """
        super().__init__()
        self.database_service = database_service or DatabaseService()
        self.agent_name = "HumanReview"
        
        # Review configuration
        self.default_timeout = timedelta(hours=24)  # 24 hours default timeout
        self.urgent_timeout = timedelta(hours=2)    # 2 hours for urgent reviews
        self.max_reviewers = 3
        
        # Callback functions for notifications (to be set by integrating system)
        self.notification_callbacks: List[Callable] = []
    
    async def execute(self, state: ContentState) -> AgentResult:
        """Execute human review process.
        
        Args:
            state: Current content state
            
        Returns:
            AgentResult with review process results
        """
        try:
            # Determine if human review is needed
            review_needed = await self.is_review_needed(state)
            
            if not review_needed:
                return AgentResult(
                    success=True,
                    data={"review_status": "not_needed", "auto_approved": True},
                    agent_name=self.agent_name
                )
            
            # Check for existing review
            existing_review = await self.get_existing_review(state.workflow_id)
            
            if existing_review:
                # Update existing review status
                review_data = await self.check_review_status(existing_review["review_id"])
            else:
                # Create new review request
                review_data = await self.request_review(state)
            
            # Update state with review information
            if not hasattr(state, 'review_data') or not state.review_data:
                state.review_data = {}
            state.review_data.update(review_data)
            
            return AgentResult(
                success=True,
                data=review_data,
                agent_name=self.agent_name
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                error=f"Human review process failed: {str(e)}",
                agent_name=self.agent_name
            )
    
    async def is_review_needed(self, state: ContentState) -> bool:
        """Determine if human review is needed based on content and quality scores.
        
        Args:
            state: Current content state
            
        Returns:
            True if human review is needed
        """
        # Check quality scores
        quality_scores = state.quality_scores or {}
        qa_data = getattr(state, 'qa_data', {}) or {}
        
        # Review needed if quality is below threshold
        overall_score = qa_data.get("overall_score", 0)
        if overall_score < 75:
            return True
        
        # Review needed for specific content types
        analysis_data = state.analysis_data or {}
        content_type = analysis_data.get("content_type", "")
        
        high_risk_types = ["legal_content", "medical_content", "financial_advice", "press_release"]
        if content_type in high_risk_types:
            return True
        
        # Review needed if brand compliance is low
        brand_compliance = qa_data.get("brand_compliance", {}).get("compliance_score", 100)
        if brand_compliance < 80:
            return True
        
        # Review needed if content contains sensitive topics
        if self._contains_sensitive_content(state.text_content or ""):
            return True
        
        # Check original input for review requirements
        original_input = state.original_input or {}
        if original_input.get("require_human_review", False):
            return True
        
        return False
    
    async def request_review(self, state: ContentState) -> Dict[str, Any]:
        """Request human review for content.
        
        Args:
            state: Current content state
            
        Returns:
            Review request data
        """
        # Determine review priority
        priority = self._determine_priority(state)
        
        # Calculate timeout based on priority
        timeout = self.urgent_timeout if priority == ReviewPriority.URGENT else self.default_timeout
        deadline = datetime.utcnow() + timeout
        
        # Create review request
        review_request = {
            "review_id": f"review_{state.workflow_id}_{int(datetime.utcnow().timestamp())}",
            "workflow_id": state.workflow_id,
            "content": state.text_content,
            "content_type": state.analysis_data.get("content_type") if state.analysis_data else "unknown",
            "priority": priority.value,
            "status": ReviewStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "deadline": deadline.isoformat(),
            "quality_scores": state.quality_scores or {},
            "qa_summary": self._create_qa_summary(state),
            "review_criteria": self._get_review_criteria(state),
            "reviewer_assignments": [],
            "feedback": [],
            "decision": None,
            "decision_reason": None
        }
        
        # Store review request in database
        await self._store_review_request(review_request)
        
        # Notify reviewers
        await self._notify_reviewers(review_request)
        
        return {
            "review_status": ReviewStatus.PENDING.value,
            "review_id": review_request["review_id"],
            "priority": priority.value,
            "deadline": deadline.isoformat(),
            "requested_at": datetime.utcnow().isoformat()
        }
    
    async def check_review_status(self, review_id: str) -> Dict[str, Any]:
        """Check the status of an existing review.
        
        Args:
            review_id: ID of the review to check
            
        Returns:
            Current review status data
        """
        try:
            # Get review from database
            review_data = await self._get_review_from_db(review_id)
            
            if not review_data:
                return {
                    "review_status": "not_found",
                    "error": "Review not found"
                }
            
            # Check if review has timed out
            deadline = datetime.fromisoformat(review_data["deadline"])
            if datetime.utcnow() > deadline and review_data["status"] in [ReviewStatus.PENDING.value, ReviewStatus.IN_REVIEW.value]:
                # Mark as timed out
                review_data["status"] = ReviewStatus.TIMEOUT.value
                await self._update_review_status(review_id, ReviewStatus.TIMEOUT.value, "Review timed out")
            
            return {
                "review_status": review_data["status"],
                "review_id": review_id,
                "feedback": review_data.get("feedback", []),
                "decision": review_data.get("decision"),
                "decision_reason": review_data.get("decision_reason"),
                "updated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "review_status": "error",
                "error": f"Failed to check review status: {str(e)}"
            }
    
    async def collect_feedback(self, review_id: str, reviewer_id: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Collect feedback from a reviewer.
        
        Args:
            review_id: ID of the review
            reviewer_id: ID of the reviewer
            feedback: Feedback data
            
        Returns:
            Feedback collection result
        """
        try:
            # Validate feedback
            if not self._validate_feedback(feedback):
                return {
                    "success": False,
                    "error": "Invalid feedback format"
                }
            
            # Add metadata to feedback
            feedback_entry = {
                "reviewer_id": reviewer_id,
                "feedback": feedback,
                "submitted_at": datetime.utcnow().isoformat(),
                "rating": feedback.get("rating", 0),
                "comments": feedback.get("comments", ""),
                "suggestions": feedback.get("suggestions", []),
                "approval": feedback.get("approval", False)
            }
            
            # Store feedback
            await self._store_feedback(review_id, feedback_entry)
            
            # Check if review is complete
            review_complete = await self._check_review_completion(review_id)
            
            if review_complete:
                # Process final decision
                decision_data = await self._process_final_decision(review_id)
                return {
                    "success": True,
                    "feedback_stored": True,
                    "review_complete": True,
                    "final_decision": decision_data
                }
            
            return {
                "success": True,
                "feedback_stored": True,
                "review_complete": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to collect feedback: {str(e)}"
            }
    
    async def get_existing_review(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get existing review for a workflow.
        
        Args:
            workflow_id: Workflow ID to check
            
        Returns:
            Existing review data or None
        """
        try:
            # Query database for existing review
            return await self._get_review_by_workflow_id(workflow_id)
        except Exception:
            return None
    
    def add_notification_callback(self, callback: Callable):
        """Add a notification callback function.
        
        Args:
            callback: Function to call for notifications
        """
        self.notification_callbacks.append(callback)
    
    def _determine_priority(self, state: ContentState) -> ReviewPriority:
        """Determine review priority based on content characteristics.
        
        Args:
            state: Current content state
            
        Returns:
            Review priority level
        """
        # Check quality scores
        qa_data = getattr(state, 'qa_data', {}) or {}
        overall_score = qa_data.get("overall_score", 100)
        
        if overall_score < 50:
            return ReviewPriority.URGENT
        elif overall_score < 70:
            return ReviewPriority.HIGH
        
        # Check content type
        analysis_data = state.analysis_data or {}
        content_type = analysis_data.get("content_type", "")
        
        high_priority_types = ["legal_content", "medical_content", "financial_advice"]
        if content_type in high_priority_types:
            return ReviewPriority.HIGH
        
        # Check original input priority
        original_input = state.original_input or {}
        input_priority = original_input.get("priority", "medium")
        
        priority_map = {
            "low": ReviewPriority.LOW,
            "medium": ReviewPriority.MEDIUM,
            "high": ReviewPriority.HIGH,
            "urgent": ReviewPriority.URGENT
        }
        
        return priority_map.get(input_priority, ReviewPriority.MEDIUM)
    
    def _contains_sensitive_content(self, content: str) -> bool:
        """Check if content contains sensitive topics.
        
        Args:
            content: Content to check
            
        Returns:
            True if sensitive content is detected
        """
        sensitive_keywords = [
            "legal advice", "medical advice", "financial advice",
            "investment recommendation", "diagnosis", "treatment",
            "lawsuit", "litigation", "confidential", "proprietary"
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in sensitive_keywords)
    
    def _create_qa_summary(self, state: ContentState) -> Dict[str, Any]:
        """Create a summary of QA results for reviewers.
        
        Args:
            state: Current content state
            
        Returns:
            QA summary for reviewers
        """
        qa_data = getattr(state, 'qa_data', {}) or {}
        
        return {
            "overall_score": qa_data.get("overall_score", 0),
            "quality_scores": qa_data.get("quality_scores", {}),
            "main_issues": qa_data.get("suggestions", [])[:5],
            "passed_qa": qa_data.get("passed_qa", False)
        }
    
    def _get_review_criteria(self, state: ContentState) -> List[str]:
        """Get review criteria based on content type and requirements.
        
        Args:
            state: Current content state
            
        Returns:
            List of review criteria
        """
        base_criteria = [
            "Content accuracy and factual correctness",
            "Tone and brand voice consistency",
            "Grammar and language quality",
            "Relevance to target audience",
            "Overall effectiveness"
        ]
        
        # Add specific criteria based on content type
        analysis_data = state.analysis_data or {}
        content_type = analysis_data.get("content_type", "")
        
        if content_type == "legal_content":
            base_criteria.extend([
                "Legal accuracy and compliance",
                "Appropriate disclaimers"
            ])
        elif content_type == "medical_content":
            base_criteria.extend([
                "Medical accuracy",
                "Appropriate medical disclaimers"
            ])
        elif content_type == "financial_advice":
            base_criteria.extend([
                "Financial accuracy",
                "Risk disclosures",
                "Regulatory compliance"
            ])
        
        return base_criteria
    
    def _validate_feedback(self, feedback: Dict[str, Any]) -> bool:
        """Validate feedback format.
        
        Args:
            feedback: Feedback to validate
            
        Returns:
            True if feedback is valid
        """
        required_fields = ["rating", "approval"]
        return all(field in feedback for field in required_fields)
    
    async def _store_review_request(self, review_request: Dict[str, Any]):
        """Store review request in database."""
        # Implementation would store in actual database
        # For now, this is a placeholder
        pass
    
    async def _notify_reviewers(self, review_request: Dict[str, Any]):
        """Notify reviewers about new review request."""
        for callback in self.notification_callbacks:
            try:
                await callback(review_request)
            except Exception:
                pass  # Continue with other callbacks
    
    async def _get_review_from_db(self, review_id: str) -> Optional[Dict[str, Any]]:
        """Get review data from database."""
        # Placeholder implementation
        return None
    
    async def _update_review_status(self, review_id: str, status: str, reason: str):
        """Update review status in database."""
        # Placeholder implementation
        pass
    
    async def _store_feedback(self, review_id: str, feedback_entry: Dict[str, Any]):
        """Store feedback in database."""
        # Placeholder implementation
        pass
    
    async def _check_review_completion(self, review_id: str) -> bool:
        """Check if review has enough feedback to make a decision."""
        # Placeholder implementation
        return True
    
    async def _process_final_decision(self, review_id: str) -> Dict[str, Any]:
        """Process final review decision based on collected feedback."""
        # Placeholder implementation
        return {
            "decision": "approved",
            "confidence": 0.8,
            "summary": "Content approved based on reviewer feedback"
        }
    
    async def _get_review_by_workflow_id(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get review by workflow ID."""
        # Placeholder implementation
        return None
    
    async def validate(self, state: ContentState) -> bool:
        """Validate that human review can be performed.
        
        Args:
            state: Current content state
            
        Returns:
            True if validation passes
        """
        return bool(state.workflow_id and (state.text_content or state.image_content))