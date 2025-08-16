"""Image generation agent that integrates with image service."""

from typing import Optional

from src.models.state_models import ContentState
from src.services.image_service import ImageService
from .base_agent import BaseAgent


class ImageGenerator(BaseAgent):
    """Agent responsible for generating images using image service."""
    
    def __init__(self, *, name: Optional[str] = None, image_service: Optional[ImageService] = None):
        super().__init__(name=name)
        self.image_service = image_service or ImageService()
    
    def execute(self, state: ContentState) -> ContentState:
        """Generate images based on the current state."""
        # Extract image requirements from state
        topic = state.original_input.get("topic", "")
        content_type = state.original_input.get("content_type", "blog")
        platform = state.original_input.get("platform", "general")
        
        # Get planning information if available
        plan = state.platform_content.get("plan", {})
        
        # Get text content for context if available
        text_content = state.text_content.get("generated", "")
        
        # Create image prompt based on content
        image_prompt = self._create_image_prompt(topic, content_type, platform, plan, text_content)
        
        try:
            # Generate image using image service
            image_result = self.image_service.generate_image(image_prompt)
            
            # Store generated image information in state
            state.image_content["generated"] = image_result
            state.image_content["prompt_used"] = image_prompt
            state.image_content["content_type"] = content_type
            
        except Exception as e:
            # Handle generation errors gracefully
            state.image_content["error"] = str(e)
            state.image_content["generated"] = None
        
        return state
    
    def _create_image_prompt(self, topic: str, content_type: str, platform: str, plan: dict, text_content: str) -> str:
        """Create a prompt for image generation."""
        base_prompt = f"Create an image for content about: {topic}"
        
        # Add content type specific requirements
        if content_type == "blog":
            base_prompt += "\n\nStyle: Professional, blog header image"
        elif content_type == "social":
            base_prompt += f"\n\nStyle: Social media image for {platform}"
            
            # Platform-specific image requirements
            if platform.lower() == "instagram":
                base_prompt += "\n\nAspect ratio: Square (1:1), vibrant and eye-catching"
            elif platform.lower() == "twitter":
                base_prompt += "\n\nAspect ratio: 16:9, clean and professional"
            elif platform.lower() == "linkedin":
                base_prompt += "\n\nAspect ratio: 1.91:1, professional and business-oriented"
        
        # Add planning information
        if plan.get("visual_style"):
            base_prompt += f"\n\nVisual style: {plan['visual_style']}"
        
        if plan.get("color_scheme"):
            base_prompt += f"\n\nColor scheme: {plan['color_scheme']}"
        
        if plan.get("mood"):
            base_prompt += f"\n\nMood: {plan['mood']}"
        
        # Add context from text content if available
        if text_content and len(text_content) > 50:
            # Extract key themes from text content (simplified)
            base_prompt += f"\n\nContext: Create an image that complements this content theme"
        
        # Add general requirements
        base_prompt += "\n\nRequirements: High quality, professional, relevant to the topic"
        
        return base_prompt
    
    def generate_multiple_variants(self, state: ContentState, count: int = 3) -> ContentState:
        """Generate multiple image variants for selection."""
        topic = state.original_input.get("topic", "")
        content_type = state.original_input.get("content_type", "blog")
        platform = state.original_input.get("platform", "general")
        plan = state.platform_content.get("plan", {})
        text_content = state.text_content.get("generated", "")
        
        variants = []
        
        for i in range(count):
            # Create slightly different prompts for variety
            base_prompt = self._create_image_prompt(topic, content_type, platform, plan, text_content)
            variant_prompt = f"{base_prompt}\n\nVariant {i+1}: Add unique creative elements"
            
            try:
                image_result = self.image_service.generate_image(variant_prompt)
                variants.append({
                    "image": image_result,
                    "prompt": variant_prompt,
                    "variant_id": i+1
                })
            except Exception as e:
                variants.append({
                    "error": str(e),
                    "prompt": variant_prompt,
                    "variant_id": i+1
                })
        
        state.image_content["variants"] = variants
        return state