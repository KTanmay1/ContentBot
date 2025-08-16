"""
LLM Service for ViraLearn ContentBot.
Handles Gemini 2.0 Flash integration with retry logic and error handling.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import time
import json

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core import retry as google_retry
import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class GenerationRequest:
    """Request structure for content generation."""
    prompt: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    system_prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class GenerationResponse:
    """Response structure for content generation."""
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str
    metadata: Dict[str, Any]


class LLMServiceError(Exception):
    """Custom exception for LLM service errors."""
    pass


class LLMService:
    """Service for interacting with Gemini 2.0 Flash API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.model = None
        self._initialized = False
        
        # Configure safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
    
    async def initialize(self) -> None:
        """Initialize the Gemini client and model."""
        if self._initialized:
            return
        
        try:
            # Configure the API key
            genai.configure(api_key=self.settings.gemini.api_key)
            
            # Initialize the model
            self.model = genai.GenerativeModel(
                model_name=self.settings.gemini.model_name,
                safety_settings=self.safety_settings,
                generation_config={
                    "temperature": self.settings.gemini.temperature,
                    "top_p": self.settings.gemini.top_p,
                    "max_output_tokens": self.settings.gemini.max_tokens,
                }
            )
            
            self._initialized = True
            logger.info(f"LLM Service initialized with model: {self.settings.gemini.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise LLMServiceError(f"LLM service initialization failed: {e}")
    
    async def generate_content(
        self, 
        request: GenerationRequest,
        retry_count: int = 0
    ) -> GenerationResponse:
        """
        Generate content using Gemini 2.0 Flash.
        
        Args:
            request: Generation request with prompt and parameters
            retry_count: Current retry attempt (for internal use)
            
        Returns:
            GenerationResponse with generated content and metadata
            
        Raises:
            LLMServiceError: If generation fails after retries
        """
        if not self._initialized:
            await self.initialize()
        
        # Prepare generation parameters
        generation_config = {
            "temperature": request.temperature or self.settings.gemini.temperature,
            "top_p": request.top_p or self.settings.gemini.top_p,
        }
        
        if request.max_tokens:
            generation_config["max_output_tokens"] = request.max_tokens
        
        # Build the prompt
        full_prompt = self._build_prompt(request)
        
        try:
            start_time = time.time()
            
            # Generate content
            response = await self._generate_with_retry(
                full_prompt, 
                generation_config,
                retry_count
            )
            
            generation_time = time.time() - start_time
            
            # Parse response
            content = response.text
            
            # Extract usage information (handle different response structures)
            usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
            
            # Try to get usage metadata if available
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0),
                }
            elif hasattr(response, 'candidates') and response.candidates:
                # Fallback: estimate tokens based on content length
                content_length = len(content)
                usage = {
                    "prompt_tokens": 0,
                    "completion_tokens": content_length // 4,  # Rough estimate
                    "total_tokens": content_length // 4,
                }
            
            return GenerationResponse(
                content=content,
                usage=usage,
                model=self.settings.gemini.model_name,
                finish_reason="stop",  # Gemini doesn't provide this directly
                metadata={
                    "generation_time": generation_time,
                    "model": self.settings.gemini.model_name,
                    "temperature": generation_config["temperature"],
                    "top_p": generation_config["top_p"],
                }
            )
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            
            # Retry logic
            if retry_count < self.settings.gemini.max_retries:
                logger.info(f"Retrying generation (attempt {retry_count + 1}/{self.settings.gemini.max_retries})")
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return await self.generate_content(request, retry_count + 1)
            
            raise LLMServiceError(f"Content generation failed after {self.settings.gemini.max_retries} retries: {e}")
    
    async def _generate_with_retry(
        self, 
        prompt: str, 
        config: Dict[str, Any],
        retry_count: int
    ) -> Any:
        """Generate content with retry logic."""
        try:
            # Create a new model instance with updated config
            model = genai.GenerativeModel(
                model_name=self.settings.gemini.model_name,
                safety_settings=self.safety_settings,
                generation_config=config
            )
            
            response = await asyncio.wait_for(
                model.generate_content_async(prompt),
                timeout=self.settings.gemini.timeout
            )
            
            return response
            
        except asyncio.TimeoutError:
            raise LLMServiceError("Generation request timed out")
        except Exception as e:
            raise LLMServiceError(f"Generation failed: {e}")
    
    def _build_prompt(self, request: GenerationRequest) -> str:
        """Build the full prompt with system message and context."""
        prompt_parts = []
        
        # Add system prompt if provided
        if request.system_prompt:
            prompt_parts.append(f"System: {request.system_prompt}")
        
        # Add context if provided
        if request.context:
            context_str = json.dumps(request.context, indent=2)
            prompt_parts.append(f"Context: {context_str}")
        
        # Add main prompt
        prompt_parts.append(f"User: {request.prompt}")
        
        return "\n\n".join(prompt_parts)
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of given text."""
        prompt = f"""
        Analyze the sentiment of the following text and provide a detailed breakdown:
        
        Text: {text}
        
        Please provide:
        1. Overall sentiment (positive, negative, neutral)
        2. Sentiment score (-1 to 1, where -1 is very negative, 1 is very positive)
        3. Emotional breakdown (joy, sadness, anger, fear, surprise, disgust)
        4. Confidence level (0-1)
        5. Key emotional indicators found in the text
        
        Respond in JSON format.
        """
        
        request = GenerationRequest(
            prompt=prompt,
            max_tokens=500,
            temperature=0.3
        )
        
        response = await self.generate_content(request)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback to simple parsing if JSON parsing fails
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "confidence": 0.5,
                "raw_response": response.content
            }
    
    async def extract_themes(self, text: str) -> List[str]:
        """Extract themes from given text."""
        prompt = f"""
        Extract the main themes and topics from the following text. 
        Return only the theme names as a comma-separated list, without explanations.
        
        Text: {text}
        """
        
        request = GenerationRequest(
            prompt=prompt,
            max_tokens=200,
            temperature=0.3
        )
        
        response = await self.generate_content(request)
        
        # Parse themes from response
        themes = [theme.strip() for theme in response.content.split(',')]
        return [theme for theme in themes if theme]
    
    async def generate_seo_keywords(self, content: str, topic: str) -> List[str]:
        """Generate SEO keywords for given content and topic."""
        prompt = f"""
        Generate 10-15 relevant SEO keywords for the following content and topic.
        Focus on long-tail keywords and include both primary and secondary keywords.
        Return only the keywords as a comma-separated list.
        
        Topic: {topic}
        Content: {content[:500]}...
        """
        
        request = GenerationRequest(
            prompt=prompt,
            max_tokens=300,
            temperature=0.4
        )
        
        response = await self.generate_content(request)
        
        # Parse keywords from response
        keywords = [kw.strip() for kw in response.content.split(',')]
        return [kw for kw in keywords if kw]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the LLM service."""
        try:
            if not self._initialized:
                return {"status": "not_initialized", "error": "Service not initialized"}
            
            # Test with a simple prompt
            test_request = GenerationRequest(
                prompt="Hello, this is a health check. Please respond with 'OK'.",
                max_tokens=10,
                temperature=0.0
            )
            
            response = await self.generate_content(test_request)
            
            return {
                "status": "healthy",
                "model": self.settings.gemini.model_name,
                "response_time": response.metadata["generation_time"],
                "test_response": response.content
            }
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global LLM service instance
llm_service = LLMService()


async def get_llm_service() -> LLMService:
    """Get the global LLM service instance."""
    if not llm_service._initialized:
        await llm_service.initialize()
    return llm_service
