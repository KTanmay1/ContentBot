"""
Image Service for ViraLearn ContentBot.
Handles Imagen 4 API integration for image generation and processing.
"""

import asyncio
import logging
import base64
import io
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import httpx
from google.cloud import aiplatform
from google.cloud.aiplatform_v1.types import prediction_service

from config.settings import get_settings

logger = logging.getLogger(__name__)


class ImageStyle(Enum):
    """Image generation styles."""
    REALISTIC = "realistic"
    ARTISTIC = "artistic"
    CARTOON = "cartoon"
    ABSTRACT = "abstract"
    MINIMALIST = "minimalist"
    VINTAGE = "vintage"
    MODERN = "modern"


class ImageFormat(Enum):
    """Supported image formats."""
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"


@dataclass
class ImageGenerationRequest:
    """Request structure for image generation."""
    prompt: str
    style: ImageStyle = ImageStyle.REALISTIC
    aspect_ratio: str = "1:1"  # "1:1", "16:9", "4:3", "9:16"
    size: Tuple[int, int] = (1024, 1024)
    format: ImageFormat = ImageFormat.JPEG
    quality: int = 90
    seed: Optional[int] = None
    guidance_scale: float = 7.5
    num_inference_steps: int = 50


@dataclass
class ImageGenerationResponse:
    """Response structure for image generation."""
    images: List[bytes]
    metadata: Dict[str, Any]
    generation_time: float
    model: str


class ImageServiceError(Exception):
    """Custom exception for image service errors."""
    pass


class ImageService:
    """Service for interacting with Imagen 4 API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.endpoint = None
        self._initialized = False
        
        # Platform-specific aspect ratios
        self.platform_aspects = {
            "twitter": {"1:1": (1080, 1080), "16:9": (1200, 675)},
            "linkedin": {"1:1": (1200, 1200), "16:9": (1200, 628)},
            "instagram": {"1:1": (1080, 1080), "4:5": (1080, 1350)},
            "facebook": {"1:1": (1200, 1200), "16:9": (1200, 630)},
        }
    
    async def initialize(self) -> None:
        """Initialize the image service with Imagen API."""
        if self._initialized:
            return
        
        try:
            # Initialize Google Cloud AI Platform with service account credentials
            aiplatform.init(
                project=self.settings.imagen.project_id,
                location=self.settings.imagen.location
                # Uses GOOGLE_APPLICATION_CREDENTIALS environment variable
            )
            
            self.client = aiplatform.gapic.PredictionServiceClient()
            self.endpoint = f"projects/{self.settings.imagen.project_id}/locations/{self.settings.imagen.location}/publishers/google/models/{self.settings.imagen.model_name}"
            
            self._initialized = True
            logger.info(f"Image Service initialized with model: {self.settings.imagen.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Image Service: {e}")
            raise ImageServiceError(f"Image service initialization failed: {e}")
    
    async def generate_image(
        self, 
        request: ImageGenerationRequest,
        retry_count: int = 0
    ) -> ImageGenerationResponse:
        """
        Generate image using Imagen 4 API.
        
        Args:
            request: Image generation request with prompt and parameters
            retry_count: Current retry attempt (for internal use)
            
        Returns:
            ImageGenerationResponse with generated images and metadata
            
        Raises:
            ImageServiceError: If generation fails after retries
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            start_time = time.time()
            
            # Prepare the prompt with style
            enhanced_prompt = self._enhance_prompt(request.prompt, request.style)
            
            # Generate image
            response = await self._generate_with_retry(
                enhanced_prompt,
                request,
                retry_count
            )
            
            generation_time = time.time() - start_time
            
            # Process and optimize images
            processed_images = []
            for image_data in response.predictions:
                # Decode base64 image
                image_bytes = base64.b64decode(image_data)
                
                # Optimize image
                optimized_image = await self._optimize_image(
                    image_bytes, 
                    request.format, 
                    request.quality,
                    request.size
                )
                processed_images.append(optimized_image)
            
            return ImageGenerationResponse(
                images=processed_images,
                metadata={
                    "prompt": request.prompt,
                    "style": request.style.value,
                    "aspect_ratio": request.aspect_ratio,
                    "size": request.size,
                    "format": request.format.value,
                    "model": self.settings.imagen.model_name,
                },
                generation_time=generation_time,
                model=self.settings.imagen.model_name
            )
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            
            # Retry logic
            if retry_count < self.settings.imagen.max_retries:
                logger.info(f"Retrying image generation (attempt {retry_count + 1}/{self.settings.imagen.max_retries})")
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return await self.generate_image(request, retry_count + 1)
            
            raise ImageServiceError(f"Image generation failed after {self.settings.imagen.max_retries} retries: {e}")
    
    async def _generate_with_retry(
        self, 
        prompt: str, 
        request: ImageGenerationRequest,
        retry_count: int
    ) -> Any:
        """Generate image with retry logic."""
        try:
            # Prepare the request payload
            payload = {
                "instances": [{
                    "prompt": prompt,
                    "aspect_ratio": request.aspect_ratio,
                    "guidance_scale": request.guidance_scale,
                    "num_inference_steps": request.num_inference_steps,
                }]
            }
            
            if request.seed is not None:
                payload["instances"][0]["seed"] = request.seed
            
            # Make the prediction using the client
            from google.cloud.aiplatform_v1.types import PredictRequest
            from google.protobuf import json_format
            from google.protobuf.struct_pb2 import Value
            
            # Convert payload to protobuf format
            instances = []
            for instance in payload["instances"]:
                value = Value()
                json_format.ParseDict(instance, value)
                instances.append(value)
            
            predict_request = PredictRequest(
                endpoint=self.endpoint,
                instances=instances
            )
            
            # Make async prediction
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.client.predict, 
                predict_request
            )
            
            return response
            
        except asyncio.TimeoutError:
            raise ImageServiceError("Image generation request timed out")
        except Exception as e:
            raise ImageServiceError(f"Image generation failed: {e}")
    
    def _enhance_prompt(self, prompt: str, style: ImageStyle) -> str:
        """Enhance prompt with style-specific instructions."""
        style_enhancements = {
            ImageStyle.REALISTIC: "high quality, realistic, detailed, professional photography",
            ImageStyle.ARTISTIC: "artistic, creative, expressive, vibrant colors",
            ImageStyle.CARTOON: "cartoon style, animated, colorful, fun",
            ImageStyle.ABSTRACT: "abstract, geometric, modern art, conceptual",
            ImageStyle.MINIMALIST: "minimalist, clean, simple, elegant",
            ImageStyle.VINTAGE: "vintage, retro, classic, nostalgic",
            ImageStyle.MODERN: "modern, contemporary, sleek, sophisticated"
        }
        
        enhancement = style_enhancements.get(style, "")
        return f"{prompt}, {enhancement}"
    
    async def _optimize_image(
        self, 
        image_bytes: bytes, 
        format: ImageFormat, 
        quality: int,
        target_size: Tuple[int, int]
    ) -> bytes:
        """Optimize image for target format and size."""
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Resize if needed
            if image.size != target_size:
                image = image.resize(target_size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if saving as JPEG
            if format == ImageFormat.JPEG and image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save optimized image
            output_buffer = io.BytesIO()
            
            save_kwargs = {
                'optimize': True,
                'quality': quality
            }
            
            if format == ImageFormat.JPEG:
                image.save(output_buffer, 'JPEG', **save_kwargs)
            elif format == ImageFormat.PNG:
                image.save(output_buffer, 'PNG', **save_kwargs)
            elif format == ImageFormat.WEBP:
                image.save(output_buffer, 'WEBP', **save_kwargs)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return image_bytes  # Return original if optimization fails
    
    async def create_social_graphics(
        self, 
        content: str, 
        platform: str, 
        style: ImageStyle = ImageStyle.MODERN
    ) -> ImageGenerationResponse:
        """Create social media graphics with text overlay."""
        # Get platform-specific dimensions
        aspect_ratio = "1:1"  # Default
        if platform in self.platform_aspects:
            aspect_ratio = "1:1"  # Use square for text overlays
        
        size = self.platform_aspects.get(platform, {}).get(aspect_ratio, (1080, 1080))
        
        # Create a prompt for the background
        background_prompt = f"professional social media background, {style.value} style, clean, modern"
        
        request = ImageGenerationRequest(
            prompt=background_prompt,
            style=style,
            aspect_ratio=aspect_ratio,
            size=size,
            format=ImageFormat.PNG,  # Use PNG for transparency
            quality=95
        )
        
        response = await self.generate_image(request)
        
        # Add text overlay to the first image
        if response.images:
            image_with_text = await self._add_text_overlay(
                response.images[0], 
                content, 
                platform
            )
            response.images[0] = image_with_text
        
        return response
    
    async def _add_text_overlay(
        self, 
        image_bytes: bytes, 
        text: str, 
        platform: str
    ) -> bytes:
        """Add text overlay to image."""
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Create a drawing object
            draw = ImageDraw.Draw(image)
            
            # Calculate text position and size
            width, height = image.size
            font_size = min(width, height) // 20  # Responsive font size
            
            # Try to load a font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Wrap text to fit image width
            words = text.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                bbox = draw.textbbox((0, 0), test_line, font=font)
                text_width = bbox[2] - bbox[0]
                
                if text_width <= width * 0.8:  # Leave 10% margin on each side
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Calculate total text height
            line_height = font_size * 1.2
            total_text_height = len(lines) * line_height
            
            # Position text in center
            y_start = (height - total_text_height) // 2
            
            # Draw each line
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                y = y_start + i * line_height
                
                # Draw text with outline for better visibility
                outline_color = (0, 0, 0)
                text_color = (255, 255, 255)
                
                # Draw outline
                for dx in [-2, -1, 0, 1, 2]:
                    for dy in [-2, -1, 0, 1, 2]:
                        draw.text((x + dx, y + dy), line, font=font, fill=outline_color)
                
                # Draw main text
                draw.text((x, y), line, font=font, fill=text_color)
            
            # Save the image
            output_buffer = io.BytesIO()
            image.save(output_buffer, 'PNG', optimize=True)
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Text overlay failed: {e}")
            return image_bytes  # Return original if text overlay fails
    
    async def generate_content_images(
        self, 
        prompt: str, 
        style: ImageStyle,
        count: int = 1
    ) -> ImageGenerationResponse:
        """Generate multiple content images with consistent style."""
        request = ImageGenerationRequest(
            prompt=prompt,
            style=style,
            aspect_ratio="16:9",  # Good for content
            size=(1920, 1080),
            format=ImageFormat.JPEG,
            quality=90
        )
        
        # Generate multiple images
        all_images = []
        all_metadata = []
        total_time = 0
        
        for i in range(count):
            response = await self.generate_image(request)
            all_images.extend(response.images)
            all_metadata.append(response.metadata)
            total_time += response.generation_time
        
        return ImageGenerationResponse(
            images=all_images,
            metadata={
                "prompt": prompt,
                "style": style.value,
                "count": count,
                "individual_metadata": all_metadata,
                "model": self.settings.imagen.model_name,
            },
            generation_time=total_time,
            model=self.settings.imagen.model_name
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the image service."""
        try:
            if not self._initialized:
                return {"status": "not_initialized", "error": "Service not initialized"}
            
            # Test with a simple prompt
            test_request = ImageGenerationRequest(
                prompt="simple geometric shape, test image",
                style=ImageStyle.MINIMALIST,
                size=(512, 512),
                format=ImageFormat.JPEG,
                quality=80
            )
            
            response = await self.generate_image(test_request)
            
            return {
                "status": "healthy",
                "model": self.settings.imagen.model_name,
                "generation_time": response.generation_time,
                "images_generated": len(response.images)
            }
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global image service instance
image_service = ImageService()


async def get_image_service() -> ImageService:
    """Get the global image service instance."""
    if not image_service._initialized:
        await image_service.initialize()
    return image_service