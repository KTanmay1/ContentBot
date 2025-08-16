#!/usr/bin/env python3
"""Debug script for LLM service."""

import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.llm_service import LLMService, GOOGLE_AI_AVAILABLE, GenerationRequest
from config.settings import get_settings

async def debug_llm():
    print(f"GOOGLE_AI_AVAILABLE: {GOOGLE_AI_AVAILABLE}")
    
    settings = get_settings()
    print(f"Gemini API key configured: {'Yes' if settings.gemini.api_key else 'No'}")
    print(f"Gemini model: {settings.gemini.model_name}")
    
    if not GOOGLE_AI_AVAILABLE:
        print("❌ Google AI not available - this is the issue!")
        return
    
    service = LLMService()
    print("🔄 Initializing LLM service...")
    
    try:
        await service.initialize()
        print("✅ LLM service initialized")
        
        # Test generation
        request = GenerationRequest(
            prompt="Say hello",
            max_tokens=10
        )
        
        response = await service.generate_content(request)
        print(f"✅ Content generated: {response.content}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_llm())