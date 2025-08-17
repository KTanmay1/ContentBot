"""Text generation agent that integrates with LLM service."""

from typing import Optional

from src.models.state_models import ContentState
from src.services.llm_service import LLMService, GenerationRequest
from .base_agent import BaseAgent


class TextGenerator(BaseAgent):
    """Agent responsible for generating text content using LLM service."""
    
    def __init__(self, *, name: Optional[str] = None, llm_service: Optional[LLMService] = None, provider: str = "gemini"):
        super().__init__(name=name)
        self.llm_service = llm_service or LLMService(provider=provider)
    
    def execute(self, state: ContentState) -> ContentState:
        """Generate text content based on the current state."""
        # Extract LLM model preference from input
        llm_model = state.original_input.get("llm_model", "gemini")
        
        # Update LLM service provider if different from current
        if self.llm_service.provider != llm_model:
            self.llm_service = LLMService(provider=llm_model)
        
        # Ensure LLM service is initialized
        if not self.llm_service._initialized:
            import asyncio
            try:
                asyncio.run(self.llm_service.initialize())
            except RuntimeError:
                # If we're in an event loop, try sync initialization
                pass
        
        # Extract content requirements from state
        content_type = state.original_input.get("content_type", "blog")
        topic = state.original_input.get("text", state.original_input.get("topic", ""))
        platform = state.original_input.get("platform", "general")
        
        # Get planning information if available
        plan = state.platform_content.get("plan", {})
        
        # Generate content using LLM service
        if content_type == "blog":
            prompt = self._create_blog_prompt(topic, plan)
        elif content_type == "social":
            prompt = self._create_social_prompt(topic, platform, plan)
        else:
            prompt = self._create_general_prompt(topic, plan)
        
        # Determine max_tokens based on content length preference
        max_tokens = self._get_max_tokens_for_length(state.original_input.get("length", "medium"))
        
        try:
            request = GenerationRequest(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.7
            )
            # Use sync method for content generation (now uses real Gemini API)
            response = self.llm_service.generate_content_sync(request)
            
            # Store generated content in state
            state.text_content["generated"] = response.content
            state.text_content["prompt_used"] = prompt
            state.text_content["content_type"] = content_type
            
        except Exception as e:
            # Provide fallback content when LLM service fails
            fallback_content = self._generate_fallback_content(topic, content_type, platform)
            state.text_content["generated"] = fallback_content
            state.text_content["prompt_used"] = prompt
            state.text_content["content_type"] = content_type
            state.text_content["fallback_used"] = True
            state.text_content["error"] = str(e)
        
        return state
    
    def _create_blog_prompt(self, topic: str, plan: dict) -> str:
        """Create a prompt for blog content generation."""
        base_prompt = f"Write a comprehensive blog post about: {topic}"
        
        if plan.get("outline"):
            base_prompt += f"\n\nFollow this outline: {plan['outline']}"
        
        if plan.get("tone"):
            base_prompt += f"\n\nTone: {plan['tone']}"
        
        if plan.get("target_audience"):
            base_prompt += f"\n\nTarget audience: {plan['target_audience']}"
        
        return base_prompt
    
    def _create_social_prompt(self, topic: str, platform: str, plan: dict) -> str:
        """Create a prompt for social media content generation."""
        base_prompt = f"Create a {platform} post about: {topic}"
        
        # Platform-specific guidelines
        if platform.lower() == "twitter":
            base_prompt += "\n\nKeep it under 280 characters. Use relevant hashtags."
        elif platform.lower() == "linkedin":
            base_prompt += "\n\nMake it professional and engaging. Include a call-to-action."
        elif platform.lower() == "instagram":
            base_prompt += "\n\nMake it visually appealing and include relevant hashtags."
        
        if plan.get("hashtags"):
            base_prompt += f"\n\nSuggested hashtags: {plan['hashtags']}"
        
        return base_prompt
    
    def _create_general_prompt(self, topic: str, plan: dict) -> str:
        """Create a general content generation prompt."""
        base_prompt = f"Create content about: {topic}"
        
        if plan.get("format"):
            base_prompt += f"\n\nFormat: {plan['format']}"
        
        return base_prompt
    
    def _generate_fallback_content(self, topic: str, content_type: str, platform: str) -> str:
        """Generate fallback content when LLM service is unavailable."""
        if content_type == "blog":
            return f"""# {topic}

This is a comprehensive blog post about {topic}. 

## Introduction
{topic} is an important topic that deserves careful consideration and analysis.

## Key Points
- Understanding the fundamentals of {topic}
- Exploring the implications and applications
- Best practices and recommendations

## Conclusion
In conclusion, {topic} represents a significant area of interest that continues to evolve and impact various aspects of our work and daily lives.

*Note: This content was generated using fallback mode due to service unavailability.*"""
        
        elif content_type == "social":
            if platform.lower() == "twitter":
                return f"Exploring the fascinating world of {topic}! 🚀 What are your thoughts? #AI #Technology #Innovation"
            elif platform.lower() == "linkedin":
                return f"Sharing insights on {topic}. This emerging field continues to shape how we approach modern challenges. What's your experience with {topic}? Let's discuss in the comments."
            else:
                return f"Excited to share some thoughts on {topic}! 💡 This topic has so much potential. #innovation #technology"
        
        else:
            return f"""Content about {topic}

This content explores the key aspects of {topic}, providing valuable insights and practical information for readers interested in this subject.

Key highlights:
- Overview of {topic}
- Important considerations
- Practical applications

*Note: This content was generated using fallback mode due to service unavailability.*"""

    # NEW: Map length preference to sensible max_tokens defaults
    def _get_max_tokens_for_length(self, length_pref: str) -> int:
        length_map = {
            "short": 700,
            "medium": 1500,
            "long": 2500,
            "comprehensive": 4000,
            "very_long": 5000,
        }
        # Fallback to medium if unknown
        return length_map.get(str(length_pref).lower(), 1500)