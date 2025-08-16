"""Content Planner Agent for ViraLearn ContentBot.

This agent is responsible for creating content strategies and planning
content structure based on input analysis and requirements.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models.state_models import ContentState
from ..services.llm_service import LLMService
from .base_agent import BaseAgent, AgentResult


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
    
    async def execute(self, state: ContentState) -> AgentResult:
        """Execute content planning based on analysis results.
        
        Args:
            state: Current content state with analysis data
            
        Returns:
            AgentResult with content plan
        """
        try:
            # Get analysis data
            analysis_data = state.analysis_data or {}
            original_input = state.original_input or {}
            
            # Create content strategy
            strategy = await self.create_strategy(analysis_data, original_input)
            
            # Plan content structure
            content_plan = await self.plan_content(strategy, analysis_data)
            
            # Generate content outline
            outline = await self.generate_outline(content_plan, analysis_data)
            
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
            if not state.planning_data:
                state.planning_data = {}
            state.planning_data.update(planning_data)
            
            return AgentResult(
                success=True,
                data=planning_data,
                agent_name=self.agent_name
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                error=f"Content planning failed: {str(e)}",
                agent_name=self.agent_name
            )
    
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
            except json.JSONDecodeError:
                return self._create_strategy_fallback(analysis_data, original_input)
                
        except Exception:
            return self._create_strategy_fallback(analysis_data, original_input)
    
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
            except json.JSONDecodeError:
                return self._plan_content_fallback(strategy, analysis_data)
                
        except Exception:
            return self._plan_content_fallback(strategy, analysis_data)
    
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
            except json.JSONDecodeError:
                return self._generate_outline_fallback(content_plan, analysis_data)
                
        except Exception:
            return self._generate_outline_fallback(content_plan, analysis_data)
    
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
    
    def _create_strategy_fallback(self, analysis_data: Dict[str, Any], original_input: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback strategy creation."""
        content_type = analysis_data.get("content_type", "general_content")
        sentiment = analysis_data.get("sentiment", {}).get("polarity", "neutral")
        
        return {
            "objective": f"Create engaging {content_type} content",
            "key_messages": analysis_data.get("themes", ["informative", "engaging", "valuable"]),
            "tone": "professional" if sentiment == "neutral" else sentiment,
            "approach": "informational",
            "success_metrics": ["engagement", "readability", "relevance"]
        }
    
    def _plan_content_fallback(self, strategy: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback content planning."""
        content_type = analysis_data.get("content_type", "general_content")
        
        word_count_map = {
            "blog_post": 1500,
            "social_media": 100,
            "email_marketing": 500,
            "product_content": 300,
            "general_content": 800
        }
        
        return {
            "structure": ["introduction", "main_content", "conclusion"],
            "word_count": word_count_map.get(content_type, 800),
            "sections": [
                {"name": "Introduction", "description": "Hook and overview"},
                {"name": "Main Content", "description": "Core information"},
                {"name": "Conclusion", "description": "Summary and call-to-action"}
            ],
            "call_to_action": "Learn more",
            "seo_focus": analysis_data.get("keywords", [])[:3]
        }
    
    def _generate_outline_fallback(self, content_plan: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback outline generation."""
        themes = analysis_data.get("themes", [])
        
        return {
            "title": f"Content about {', '.join(themes[:2]) if themes else 'Various Topics'}",
            "subtitle": "Comprehensive guide and insights",
            "introduction": "Brief overview and context setting",
            "main_points": [
                {"point": theme, "sub_points": ["Definition", "Examples", "Benefits"]}
                for theme in themes[:3]
            ],
            "conclusion": "Summary of key takeaways and next steps",
            "estimated_length": content_plan.get("word_count", 800)
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