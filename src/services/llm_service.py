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

# Try to import Google AI dependencies
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    from google.api_core import retry as google_retry
    GOOGLE_AI_AVAILABLE = True
except ImportError as e:
    genai = None
    HarmCategory = None
    HarmBlockThreshold = None
    google_retry = None
    GOOGLE_AI_AVAILABLE = False

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)

# Try to import Mistral AI dependencies
try:
    from mistralai import Mistral
    from mistralai.models import UserMessage, AssistantMessage
    MISTRAL_AI_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.warning(f"Mistral AI not available: {e}")
    logger.info("Falling back to Gemini and Hugging Face providers only")
    MISTRAL_AI_AVAILABLE = False
    Mistral = None
    UserMessage = None
    AssistantMessage = None

if not GOOGLE_AI_AVAILABLE:
    logger.warning("Google AI services not available. LLM features will use fallback mode.")


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
    """Service for LLM operations using multiple providers (Gemini, Mistral, Hugging Face)."""
    
    def __init__(self, provider: str = "gemini"):
        self.settings = get_settings()
        self.provider = provider.lower()
        self.client = None
        self.model = None
        self.mistral_client = None
        self._initialized = False
        
        # Configure safety settings if Google AI is available
        if GOOGLE_AI_AVAILABLE:
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        else:
            self.safety_settings = {}
    
    async def initialize(self) -> None:
        """Initialize the LLM service with the selected provider."""
        if self._initialized:
            return
        
        if self.provider == "gemini":
            await self._initialize_gemini()
        elif self.provider == "mistral":
            await self._initialize_mistral()
        else:
            logger.warning(f"Unknown provider: {self.provider}. Falling back to Gemini.")
            self.provider = "gemini"
            await self._initialize_gemini()
        
        self._initialized = True
    
    async def _initialize_gemini(self) -> None:
        """Initialize Gemini AI provider."""
        if not GOOGLE_AI_AVAILABLE:
            logger.warning("Google AI services not available. Cannot initialize Gemini.")
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
            
            logger.info(f"✅ Gemini LLM service initialized with model: {self.settings.gemini.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
            raise LLMServiceError(f"Gemini service initialization failed: {e}")
    
    async def _initialize_mistral(self) -> None:
        """Initialize Mistral AI provider."""
        if not MISTRAL_AI_AVAILABLE:
            logger.warning("Mistral AI services not available. Please install mistralai package.")
            return
        
        try:
            if self.settings.mistral.api_key:
                self.mistral_client = Mistral(api_key=self.settings.mistral.api_key)
                logger.info(f"✅ Mistral AI configured with model: {self.settings.mistral.model_name}")
            else:
                logger.warning("Mistral API key not found.")
                raise LLMServiceError("Mistral API key not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Mistral service: {e}")
            raise LLMServiceError(f"Mistral service initialization failed: {e}")
    
    async def generate_content(
        self, 
        request: GenerationRequest,
        retry_count: int = 0
    ) -> GenerationResponse:
        """
        Generate content using the selected provider (Gemini or Mistral).
        
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
        
        # Use the specified provider
        if self.provider == "gemini":
            if not GOOGLE_AI_AVAILABLE:
                raise LLMServiceError("Gemini AI is not available. Please install google-generativeai package.")
            if not self.settings.gemini.api_key:
                raise LLMServiceError("Gemini API key is not configured. Please set GEMINI_API_KEY environment variable.")
            return await self._generate_with_gemini(request, retry_count)
        elif self.provider == "mistral":
            if not MISTRAL_AI_AVAILABLE:
                raise LLMServiceError("Mistral AI is not available. Please install mistralai package.")
            if not self.settings.mistral.api_key:
                raise LLMServiceError("Mistral API key is not configured. Please set MISTRAL_API_KEY environment variable.")
            return await self._generate_with_mistral(request, retry_count)
        else:
            raise LLMServiceError(f"Unsupported provider: {self.provider}. Supported providers are 'gemini' and 'mistral'.")
    
    async def _generate_with_gemini(
        self, 
        request: GenerationRequest,
        retry_count: int = 0
    ) -> GenerationResponse:
        """Generate content using Gemini AI."""
        if not GOOGLE_AI_AVAILABLE or self.model is None:
            raise LLMServiceError("Gemini AI services are not available. Please check your API key and dependencies.")
        
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
            
            # Extract usage information
            usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
            
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
            error_str = str(e)
            logger.error(f"Content generation failed: {e}")
            
            # Check if it's a quota exceeded error
            is_quota_error = "quota" in error_str.lower() or "429" in error_str or "rate limit" in error_str.lower()
            
            # Retry logic for errors
            if retry_count < self.settings.gemini.max_retries:
                if is_quota_error:
                    # For quota errors, use longer backoff (60 seconds minimum)
                    backoff_time = max(60, 2 ** retry_count * 30)
                    logger.warning(f"Quota exceeded, waiting {backoff_time} seconds before retry {retry_count + 1}/{self.settings.gemini.max_retries}")
                else:
                    # For other errors, use standard exponential backoff
                    backoff_time = 2 ** retry_count
                    logger.info(f"Retrying generation (attempt {retry_count + 1}/{self.settings.gemini.max_retries}) in {backoff_time} seconds")
                
                await asyncio.sleep(backoff_time)
                return await self._generate_with_gemini(request, retry_count + 1)
            
            # Raise error after all retries exhausted
            if is_quota_error:
                raise LLMServiceError(f"Gemini API quota exceeded. Please check your billing and quota limits at https://ai.google.dev/gemini-api/docs/rate-limits")
            else:
                raise LLMServiceError(f"Content generation failed after {self.settings.gemini.max_retries} retries: {error_str}")
    
    async def _generate_with_mistral(
        self, 
        request: GenerationRequest,
        retry_count: int = 0
    ) -> GenerationResponse:
        """Generate content using Mistral AI."""
        if not MISTRAL_AI_AVAILABLE or self.mistral_client is None:
            raise LLMServiceError("Mistral AI services are not available. Please check your API key and dependencies.")
        
        try:
            start_time = time.time()
            
            # Build messages for Mistral chat format
            messages = []
            
            # Add context if provided
            user_content = request.prompt
            if request.context:
                context_str = json.dumps(request.context, indent=2)
                user_content = f"Context: {context_str}\n\nUser: {request.prompt}"
            
            if request.system_prompt:
                user_content = f"System: {request.system_prompt}\n\n{user_content}"
            
            messages.append(UserMessage(content=user_content))
            
            # Generate content
            response = self.mistral_client.chat.complete(
                model=self.settings.mistral.model_name,
                messages=messages,
                temperature=request.temperature or self.settings.mistral.temperature,
                top_p=request.top_p or self.settings.mistral.top_p,
                max_tokens=request.max_tokens or self.settings.mistral.max_tokens
            )
            
            generation_time = time.time() - start_time
            
            # Extract content and usage
            content = response.choices[0].message.content
            
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }
            
            return GenerationResponse(
                content=content,
                usage=usage,
                model=self.settings.mistral.model_name,
                finish_reason="completed",
                metadata={
                    "generation_time": generation_time,
                    "retry_count": retry_count,
                    "provider": "mistral"
                }
            )
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Mistral content generation failed: {error_str}")
            
            # Retry logic for Mistral
            if retry_count < self.settings.mistral.max_retries:
                if "rate_limit" in error_str.lower() or "429" in error_str:
                    wait_time = min(30 * (2 ** retry_count), 180)  # Exponential backoff, max 3 minutes
                    logger.info(f"Rate limit exceeded, waiting {wait_time} seconds before retry {retry_count + 1}/{self.settings.mistral.max_retries}")
                    await asyncio.sleep(wait_time)
                    return await self._generate_with_mistral(request, retry_count + 1)
            
            raise LLMServiceError(f"Mistral content generation failed after {retry_count + 1} attempts: {error_str}")
    

    
    async def _generate_with_retry(
        self, 
        prompt: str, 
        config: Dict[str, Any],
        retry_count: int
    ) -> Any:
        """Generate content with retry logic and quota handling."""
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
            error_str = str(e)
            
            # Check for quota exceeded error
            if "429" in error_str and "quota" in error_str.lower():
                logger.warning(f"Gemini quota exceeded: {error_str}")
                
                # Try fallback to Hugging Face
                try:
                    return await self._generate_with_huggingface_fallback(prompt, config)
                except Exception as fallback_error:
                    logger.error(f"Hugging Face fallback failed: {fallback_error}")
                    raise LLMServiceError(f"Both Gemini and Hugging Face failed. Gemini: {error_str}, HF: {fallback_error}")
            
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
    
    def generate_content_sync(self, request: GenerationRequest) -> GenerationResponse:
        """Synchronous content generation for all providers."""
        if not self._initialized:
            # Initialize synchronously
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a new thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.initialize())
                        future.result()
                else:
                    asyncio.run(self.initialize())
            except Exception as e:
                logger.error(f"Failed to initialize LLM service: {e}")
                raise LLMServiceError(f"LLM service initialization failed: {e}")
        
        if self.provider == "gemini":
            return self._generate_content_sync_gemini(request)
        elif self.provider == "mistral":
            return self._generate_content_sync_mistral(request)
        else:
            raise LLMServiceError(f"Synchronous generation not supported for provider: {self.provider}")
    
    def _generate_content_sync_gemini(self, request: GenerationRequest) -> GenerationResponse:
        """Synchronous content generation using Gemini API."""
        # Check if Google AI is available
        if not GOOGLE_AI_AVAILABLE or self.model is None:
            raise LLMServiceError("Google AI services are not available. Please check your API key and dependencies.")
        
        try:
            # Build the prompt
            full_prompt = self._build_prompt(request)
            
            # Prepare generation parameters
            generation_config = {
                "temperature": request.temperature or self.settings.gemini.temperature,
                "top_p": request.top_p or self.settings.gemini.top_p,
            }
            
            if request.max_tokens:
                generation_config["max_output_tokens"] = request.max_tokens
            
            # Generate content synchronously
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            content = response.text
            
            # Extract usage information
            usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
            
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0),
                }
            
            return GenerationResponse(
                content=content,
                usage=usage,
                model="gemini-2.0-flash-exp",
                finish_reason="completed",
                metadata={"sync_generation": True, "timestamp": time.time()}
            )
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Sync Gemini content generation failed: {e}")
            raise LLMServiceError(f"Synchronous Gemini content generation failed: {error_str}")
    
    def _generate_content_sync_mistral(self, request: GenerationRequest) -> GenerationResponse:
        """Synchronous content generation using Mistral API."""
        if not MISTRAL_AI_AVAILABLE or self.mistral_client is None:
            raise LLMServiceError("Mistral AI services are not available. Please check your API key and dependencies.")
        
        try:
            # Use a new event loop in a separate thread for Streamlit compatibility
            import asyncio
            import concurrent.futures
            import threading
            
            def run_in_new_loop():
                """Run the async method in a new event loop."""
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(self._generate_with_mistral(request, 0))
                finally:
                    new_loop.close()
            
            # Execute in a separate thread to avoid event loop conflicts
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_new_loop)
                return future.result(timeout=60)  # 60 second timeout
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Sync Mistral content generation failed: {e}")
            raise LLMServiceError(f"Synchronous Mistral content generation failed: {error_str}")
    
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
