"""Content Planner Agent for ViraLearn ContentBot.

This agent is responsible for creating content strategies and planning
content structure based on input analysis and requirements.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models.state_models import ContentState
from ..services.llm_service import LLMService
from .base_agent import BaseAgent, AgentResult
from ..core.error_handling import AgentException


class ContentPlanner(BaseAgent):
    """Agent for planning content strategy and structure."""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """Initialize the Content Planner agent.
        
        Args:
            llm_service: LLM service for content planning
        """
        super().__init__()
        self.llm_service = llm_service or LLMService()
        self.agent_name = "ContentPlanner"
    
    def execute(self, state: ContentState) -> ContentState:
        """Execute content planning based on analysis results.
        
        Args:
            state: Current content state with analysis data
            
        Returns:
            Updated ContentState with content plan
        """
        try:
            # Get analysis data
            analysis_data = state.analysis_data or {}
            original_input = state.original_input or {}
            
            # Create content strategy
            import asyncio
            try:
                strategy = asyncio.run(self.create_strategy(analysis_data, original_input))
                
                # Plan content structure
                content_plan = asyncio.run(self.plan_content(strategy, analysis_data))
                
                # Generate content outline
                outline = asyncio.run(self.generate_outline(content_plan, analysis_data))
            except RuntimeError:
                # If we're already in an event loop, raise the exception
                raise AgentException("Content planning failed: Cannot run async methods in sync context")
            
            # Create platform-specific adaptations
            platform_plans = self.create_platform_plans(content_plan, analysis_data)
            
            # Compile planning results
            planning_data = {
                "strategy": strategy,
                "content_plan": content_plan,
                "outline": outline,
                "platform_plans": platform_plans,
                "planned_at": datetime.utcnow().isoformat()
            }
            
            # Update state with planning results
            if not state.platform_content:
                state.platform_content = {}
            state.platform_content.update(planning_data)
            
            return state
            
        except Exception as e:
            raise AgentException(f"Content planning failed: {str(e)}")
    
    async def create_strategy(self, analysis_data: Dict[str, Any], original_input: Dict[str, Any]) -> Dict[str, Any]:
        """Create content strategy based on analysis.
        
        Args:
            analysis_data: Results from input analysis
            original_input: Original input requirements
            
        Returns:
            Content strategy dictionary
        """
        try:
            themes = analysis_data.get("themes", [])
            sentiment = analysis_data.get("sentiment", {})
            target_audience = analysis_data.get("target_audience", {})
            content_type = analysis_data.get("content_type", "general_content")
            
            prompt = f"""
            Create a content strategy based on the following analysis:
            - Themes: {', '.join(themes)}
            - Sentiment: {sentiment.get('polarity', 'neutral')}
            - Content Type: {content_type}
            - Target Audience: {target_audience}
            - Original Request: {original_input.get('text', '')}
            
            Respond with a JSON object containing:
            - "objective": main goal of the content
            - "key_messages": list of 3-5 key messages
            - "tone": recommended tone (formal, casual, professional, etc.)
            - "approach": content approach (educational, promotional, informational, etc.)
            - "success_metrics": how to measure success
            """
            
            response = await self.llm_service.generate_text(prompt)
            
            import json
            try:
                strategy = json.loads(response)
                return strategy
            except json.JSONDecodeError as e:
                raise AgentException(f"Failed to parse strategy JSON: {e}")
                
        except Exception as e:
            raise AgentException(f"Failed to create content strategy: {e}")
    
    async def plan_content(self, strategy: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Plan detailed content structure.
        
        Args:
            strategy: Content strategy
            analysis_data: Analysis results
            
        Returns:
            Detailed content plan
        """
        try:
            content_type = analysis_data.get("content_type", "general_content")
            themes = analysis_data.get("themes", [])
            keywords = analysis_data.get("keywords", [])
            
            prompt = f"""
            Create a detailed content plan based on:
            - Strategy: {strategy}
            - Content Type: {content_type}
            - Themes: {', '.join(themes)}
            - Keywords: {', '.join(keywords[:10])}
            
            Respond with a JSON object containing:
            - "structure": content structure (introduction, body, conclusion, etc.)
            - "word_count": recommended word count
            - "sections": list of main sections with descriptions
            - "call_to_action": recommended call-to-action
            - "seo_focus": primary SEO keywords to target
            """
            
            response = await self.llm_service.generate_text(prompt)
            
            import json
            try:
                content_plan = json.loads(response)
                return content_plan
            except json.JSONDecodeError as e:
                raise AgentException(f"Failed to parse content plan JSON: {e}")
                
        except Exception as e:
            raise AgentException(f"Failed to plan content: {e}")
    
    async def generate_outline(self, content_plan: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed content outline.
        
        Args:
            content_plan: Content plan
            analysis_data: Analysis results
            
        Returns:
            Content outline
        """
        try:
            sections = content_plan.get("sections", [])
            themes = analysis_data.get("themes", [])
            
            prompt = f"""
            Create a detailed outline based on:
            - Content Plan: {content_plan}
            - Themes: {', '.join(themes)}
            
            Respond with a JSON object containing:
            - "title": suggested title
            - "subtitle": optional subtitle
            - "introduction": introduction outline
            - "main_points": list of main points with sub-points
            - "conclusion": conclusion outline
            - "estimated_length": estimated content length
            """
            
            response = await self.llm_service.generate_text(prompt)
            
            import json
            try:
                outline = json.loads(response)
                return outline
            except json.JSONDecodeError as e:
                raise AgentException(f"Failed to parse outline JSON: {e}")
                
        except Exception as e:
            raise AgentException(f"Failed to generate outline: {e}")
    
    def create_platform_plans(self, content_plan: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create platform-specific content adaptations.
        
        Args:
            content_plan: Base content plan
            analysis_data: Analysis results
            
        Returns:
            Platform-specific plans
        """
        content_type = analysis_data.get("content_type", "general_content")
        target_audience = analysis_data.get("target_audience", {})
        
        platform_plans = {
            "blog": self._create_blog_plan(content_plan, analysis_data),
            "social_media": self._create_social_plan(content_plan, analysis_data),
            "email": self._create_email_plan(content_plan, analysis_data),
            "website": self._create_website_plan(content_plan, analysis_data)
        }
        
        return platform_plans
    
    def _create_blog_plan(self, content_plan: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create blog-specific content plan."""
        return {
            "format": "long-form article",
            "word_count": content_plan.get("word_count", 1500),
            "seo_optimization": True,
            "include_images": True,
            "meta_description": "Auto-generated based on content",
            "tags": analysis_data.get("keywords", [])[:5]
        }
    
    def _create_social_plan(self, content_plan: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create social media content plan."""
        return {
            "platforms": ["twitter", "linkedin", "facebook", "instagram"],
            "post_variations": {
                "twitter": {"character_limit": 280, "hashtags": 3},
                "linkedin": {"character_limit": 1300, "professional_tone": True},
                "facebook": {"character_limit": 500, "engagement_focus": True},
                "instagram": {"character_limit": 300, "visual_focus": True}
            },
            "posting_schedule": "staggered over 24 hours"
        }
    
    def _create_email_plan(self, content_plan: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create email marketing plan."""
        return {
            "format": "newsletter",
            "subject_line": "Auto-generated from content",
            "preview_text": "Auto-generated preview",
            "sections": ["header", "main_content", "call_to_action", "footer"],
            "personalization": True
        }
    
    def _create_website_plan(self, content_plan: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create website content plan."""
        return {
            "page_type": "landing_page",
            "seo_optimized": True,
            "mobile_responsive": True,
            "load_time_optimized": True,
            "conversion_focused": True
        }
    

    
    async def validate(self, state: ContentState) -> bool:
        """Validate that content planning can be performed.
        
        Args:
            state: Current content state
            
        Returns:
            True if validation passes
        """
        # Check if analysis data exists
        return bool(state.analysis_data and state.original_input)