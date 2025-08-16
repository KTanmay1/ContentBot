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
        
        try:
            request = GenerationRequest(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7
            )
            # Use sync method for content generation (now uses real Gemini API)
            response = self.llm_service.generate_content_sync(request)
            
            # Store generated content in state
            state.text_content["generated"] = response.content
            state.text_content["prompt_used"] = prompt
            state.text_content["content_type"] = content_type
            
        except Exception as e:
            # Raise the exception instead of providing fallback content
            raise e
        
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
        
        if plan.get("length"):
            base_prompt += f"\n\nLength: {plan['length']}"
        
        return base_prompt