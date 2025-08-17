#!/usr/bin/env python3
"""
Image Service Module

Provides image generation capabilities using HuggingFace Inference API
with Google Cloud Imagen as fallback.
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

from config.settings import get_settings

logger = logging.getLogger(__name__)

# HuggingFace imports
try:
    import requests
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    requests = None
    HUGGINGFACE_AVAILABLE = False
    logger.warning("Requests library not available. Image generation will use fallback mode.")

# Optional Google Cloud imports (fallback)
try:
    from google.cloud import aiplatform
    from google.cloud.aiplatform_v1.types import prediction_service
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    aiplatform = None
    prediction_service = None
    GOOGLE_CLOUD_AVAILABLE = False


class ImageStyle(Enum):
    """Supported image styles."""
    NONE = "none"
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


class HuggingFaceModel(Enum):
    """Available HuggingFace models for image generation."""
    STABLE_DIFFUSION_XL = "stabilityai/stable-diffusion-xl-base-1.0"
    STABLE_DIFFUSION_2_1 = "stabilityai/stable-diffusion-2-1"
    FLUX_SCHNELL = "black-forest-labs/FLUX.1-schnell"
    FLUX_DEV = "black-forest-labs/FLUX.1-dev"


@dataclass
class ImageGenerationRequest:
    """Request for image generation."""
    prompt: str
    style: ImageStyle = ImageStyle.REALISTIC
    aspect_ratio: str = "1:1"  # "1:1", "16:9", "4:3", "9:16"
    width: int = 1024
    height: int = 1024
    format: ImageFormat = ImageFormat.JPEG
    num_images: int = 1
    seed: Optional[int] = None


@dataclass
class ImageGenerationResponse:
    """Response from image generation."""
    images: List[str]  # Base64 encoded images
    model: str
    provider: str
    prompt: str
    generation_time: float = 0.0


class ImageServiceError(Exception):
    """Custom exception for image service errors."""
    pass


class ImageService:
    """Service for image generation using HuggingFace and Google Cloud fallback."""
    
    def __init__(self, provider: str = "huggingface"):
        self.settings = get_settings()
        self.provider = provider.lower()
        self.client = None
        self.endpoint = None
        self.hf_api_url = "https://api-inference.huggingface.co/models/"
        self.hf_headers = {}
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the image service with the selected provider."""
        if self._initialized:
            return
        
        if self.provider == "huggingface":
            await self._initialize_huggingface()
        elif self.provider == "google":
            await self._initialize_google_cloud()
        else:
            logger.warning(f"Unknown provider: {self.provider}. Falling back to HuggingFace.")
            self.provider = "huggingface"
            await self._initialize_huggingface()
        
        self._initialized = True
    
    async def _initialize_huggingface(self) -> None:
        """Initialize HuggingFace provider."""
        if not HUGGINGFACE_AVAILABLE:
            logger.warning("Requests library not available. Cannot initialize HuggingFace.")
            return
        
        try:
            # Set up HuggingFace API headers
            token = getattr(self.settings.huggingface, 'api_token', None) if hasattr(self.settings, 'huggingface') else None
            if token:
                self.hf_headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                logger.info("✅ HuggingFace Image Service initialized (token present)")
            else:
                # Use without auth (rate limited)
                self.hf_headers = {"Content-Type": "application/json"}
                logger.warning("HuggingFace API token not found. Using rate-limited access.")
                logger.info("✅ HuggingFace Image Service initialized (no token)")
            
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFace service: {e}")
            raise ImageServiceError(f"HuggingFace service initialization failed: {e}")
    
    async def _initialize_google_cloud(self) -> None:
        """Initialize Google Cloud provider."""
        if not GOOGLE_CLOUD_AVAILABLE:
            raise ImageServiceError("Google Cloud AI Platform not available. Please install google-cloud-aiplatform.")
        
        try:
            # Initialize Google Cloud AI Platform with service account credentials
            aiplatform.init(
                project=self.settings.imagen.project_id,
                location=self.settings.imagen.location
                # Uses GOOGLE_APPLICATION_CREDENTIALS environment variable
            )
            
            self.client = aiplatform.gapic.PredictionServiceClient()
            self.endpoint = f"projects/{self.settings.imagen.project_id}/locations/{self.settings.imagen.location}/publishers/google/models/{self.settings.imagen.model_name}"
            
            logger.info(f"Google Cloud Image Service initialized with model: {self.settings.imagen.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Image Service: {e}")
            raise ImageServiceError(f"Failed to initialize Google Cloud Image Service: {e}")
    
    async def _generate_with_huggingface(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """Generate image using HuggingFace Inference API."""
        if not HUGGINGFACE_AVAILABLE:
            raise ImageServiceError("Requests library not available for HuggingFace")
        
        start_time = time.time()
        
        try:
            # Use FLUX model as default
            model = HuggingFaceModel.FLUX_SCHNELL.value
            api_url = f"{self.hf_api_url}{model}"
            logger.debug(f"HuggingFace generation request: model={model} url={api_url}")
            
            payload = {
                "inputs": request.prompt,
                "parameters": {
                    "num_inference_steps": 4,  # Fast generation for FLUX Schnell
                    "guidance_scale": 0.0,     # FLUX Schnell doesn't use guidance
                }
            }
            
            timeout = getattr(self.settings.huggingface, 'timeout', 60) if hasattr(self.settings, 'huggingface') else 60
            response = requests.post(api_url, headers=self.hf_headers, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                # HuggingFace returns image bytes
                image_bytes = response.content
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                generation_time = time.time() - start_time
                
                return ImageGenerationResponse(
                    images=[f"data:image/{request.format.value};base64,{image_base64}"],
                    model=model,
                    provider="huggingface",
                    prompt=request.prompt,
                    generation_time=generation_time
                )
            else:
                error_msg = f"HuggingFace API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise ImageServiceError(error_msg)
                
        except Exception as e:
            logger.error(f"HuggingFace image generation failed: {e}")
            raise ImageServiceError(f"HuggingFace generation failed: {e}")
    
    async def _generate_with_google_cloud(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """Generate image using Google Cloud Imagen 4."""
        if not self._initialized:
            raise ImageServiceError("Google Cloud service not properly initialized")
        
        start_time = time.time()
        
        try:
            # Prepare the request for Imagen 4
            instances = [{
                "prompt": request.prompt,
                "sampleCount": request.num_images,
                "aspectRatio": request.aspect_ratio or "1:1",
                "safetyFilterLevel": "block_some",
                "personGeneration": "allow_adult"
            }]
            
            # Add style if specified
            if request.style and request.style != ImageStyle.NONE:
                instances[0]["style"] = request.style.value
            
            # Prepare the prediction request
            prediction_request = prediction_service.PredictRequest(
                endpoint=self.endpoint,
                instances=instances
            )
            
            # Make the prediction
            response = await self.client.predict(prediction_request)
            
            # Process the response
            images = []
            for prediction in response.predictions:
                # Imagen 4 returns base64-encoded images
                image_data = prediction.get("bytesBase64Encoded", "")
                if image_data:
                    images.append(f"data:image/{request.format.value};base64,{image_data}")
            
            if not images:
                raise ImageServiceError("No images generated")
            
            generation_time = time.time() - start_time
            
            return ImageGenerationResponse(
                images=images,
                model="imagen-4",
                provider="google_cloud",
                prompt=request.prompt,
                generation_time=generation_time
            )
            
        except Exception as e:
            logger.error(f"Google Cloud image generation failed: {e}")
            raise ImageServiceError(f"Failed to generate image with Google Cloud: {e}")
    
    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """Generate an image using the configured provider."""
        await self.initialize()
        
        if self.provider == "huggingface":
            return await self._generate_with_huggingface(request)
        elif self.provider == "google":
            return await self._generate_with_google_cloud(request)
        else:
            # Fallback to HuggingFace
            logger.warning(f"Unknown provider {self.provider}, falling back to HuggingFace")
            return await self._generate_with_huggingface(request)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the image service."""
        await self.initialize()
        
        return {
            "status": "healthy" if self._initialized else "unhealthy",
            "provider": self.provider,
            "huggingface_available": HUGGINGFACE_AVAILABLE,
            "google_cloud_available": GOOGLE_CLOUD_AVAILABLE,
            "initialized": self._initialized
        }


# Global instance
image_service = ImageService()


async def get_image_service() -> ImageService:
    """Get the global image service instance."""
    await image_service.initialize()
    return image_service