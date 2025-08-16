"""Image generation agent that integrates with image service."""

import asyncio
from typing import Optional

from ..models.state_models import ContentState
from ..services.image_service import ImageService, ImageGenerationRequest, ImageStyle, ImageFormat
from .base_agent import BaseAgent, AgentResult
from ..core.error_handling import AgentException


class ImageGenerator(BaseAgent):
    """Agent responsible for generating images using image service."""
    
    def __init__(self, *, name: Optional[str] = None, image_service: Optional[ImageService] = None):
        super().__init__(name=name)
        self.image_service = image_service or ImageService()
    
    async def execute(self, state: ContentState) -> AgentResult:
        """Generate images based on the current state."""
        try:
            # Initialize image service if needed
            await self.image_service.initialize()
            
            # Extract image requirements from state
            topic = state.original_input.get("text", state.original_input.get("topic", ""))
            content_type = state.original_input.get("content_type", "blog")
            platform = state.original_input.get("platform", "general")
            
            # Get planning information if available
            plan = state.platform_content.get("plan", {})
            
            # Get text content for context if available
            text_content = state.text_content.get("generated", "")
            
            # Create image prompt based on content
            image_prompt = self._create_image_prompt(topic, content_type, platform, plan, text_content)
            
            # Determine image style based on content type and platform
            style = self._determine_image_style(content_type, platform, plan)
            
            # Create image generation request
            request = ImageGenerationRequest(
                prompt=image_prompt,
                style=style,
                aspect_ratio=self._get_aspect_ratio(platform),
                size=self._get_image_size(platform),
                format=ImageFormat.JPEG,
                quality=90
            )
            
            # Generate image using image service
            image_result = await self.image_service.generate_image(request)
            
            # Save the image to a temporary file for display
            import tempfile
            import os
            from pathlib import Path
            
            # Create temp directory if it doesn't exist
            temp_dir = Path("temp_images")
            temp_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            import uuid
            filename = f"generated_{uuid.uuid4().hex[:8]}.{request.format.value}"
            image_path = temp_dir / filename
            
            # Save the first image from the response
            if image_result.images:
                with open(image_path, 'wb') as f:
                    f.write(image_result.images[0])
                
                # Store file path and metadata in state
                state.image_content["generated"] = str(image_path)
                state.image_content["image_bytes"] = image_result.images[0]  # Keep bytes for other uses
            else:
                state.image_content["generated"] = None
                state.image_content["error"] = "No image data received"
            
            state.image_content["prompt_used"] = image_prompt
            state.image_content["content_type"] = content_type
            state.image_content["style"] = style.value
            state.image_content["platform"] = platform
            state.image_content["metadata"] = image_result.metadata
            state.image_content["generation_time"] = image_result.generation_time
            state.image_content["model"] = image_result.model
            
            return AgentResult(
                success=True,
                state=state,
                data={"image_generated": True, "prompt": image_prompt},
                message="Image generated successfully"
            )
            
        except Exception as e:
            # Handle generation errors gracefully
            state.image_content["error"] = str(e)
            state.image_content["generated"] = None
            
            raise AgentException(f"Image generation failed: {str(e)}")
    
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
    
    def _determine_image_style(self, content_type: str, platform: str, plan: dict) -> ImageStyle:
        """Determine the appropriate image style based on content and platform."""
        # Check if style is specified in plan
        if plan.get("visual_style"):
            style_mapping = {
                "professional": ImageStyle.REALISTIC,
                "creative": ImageStyle.ARTISTIC,
                "fun": ImageStyle.CARTOON,
                "modern": ImageStyle.MODERN,
                "minimal": ImageStyle.MINIMALIST,
                "vintage": ImageStyle.VINTAGE
            }
            return style_mapping.get(plan["visual_style"].lower(), ImageStyle.REALISTIC)
        
        # Default styles based on content type and platform
        if content_type == "blog":
            return ImageStyle.REALISTIC
        elif content_type == "social":
            if platform.lower() in ["instagram", "tiktok"]:
                return ImageStyle.ARTISTIC
            elif platform.lower() == "linkedin":
                return ImageStyle.REALISTIC
            else:
                return ImageStyle.MODERN
        
        return ImageStyle.REALISTIC
    
    def _get_aspect_ratio(self, platform: str) -> str:
        """Get the appropriate aspect ratio for the platform."""
        platform_ratios = {
            "instagram": "1:1",
            "twitter": "16:9",
            "linkedin": "1.91:1",
            "facebook": "16:9",
            "general": "16:9",
            "blog": "16:9"
        }
        return platform_ratios.get(platform.lower(), "16:9")
    
    def _get_image_size(self, platform: str) -> tuple:
        """Get the appropriate image size for the platform."""
        platform_sizes = {
            "instagram": (1080, 1080),
            "twitter": (1200, 675),
            "linkedin": (1200, 628),
            "facebook": (1200, 630),
            "general": (1024, 1024),
            "blog": (1200, 675)
        }
        return platform_sizes.get(platform.lower(), (1024, 1024))
    
    async def generate_multiple_variants(self, state: ContentState, count: int = 3) -> ContentState:
        """Generate multiple image variants for selection."""
        await self.image_service.initialize()
        
        topic = state.original_input.get("text", state.original_input.get("topic", ""))
        content_type = state.original_input.get("content_type", "blog")
        platform = state.original_input.get("platform", "general")
        plan = state.platform_content.get("plan", {})
        text_content = state.text_content.get("generated", "")
        
        variants = []
        style = self._determine_image_style(content_type, platform, plan)
        
        for i in range(count):
            # Create slightly different prompts for variety
            base_prompt = self._create_image_prompt(topic, content_type, platform, plan, text_content)
            variant_prompt = f"{base_prompt}\n\nVariant {i+1}: Add unique creative elements"
            
            try:
                request = ImageGenerationRequest(
                    prompt=variant_prompt,
                    style=style,
                    aspect_ratio=self._get_aspect_ratio(platform),
                    size=self._get_image_size(platform),
                    format=ImageFormat.JPEG,
                    quality=90
                )
                
                image_result = await self.image_service.generate_image(request)
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