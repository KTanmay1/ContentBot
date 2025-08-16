#!/usr/bin/env python3
"""
Test script to verify Mistral AI integration.
"""

import sys
import os
import asyncio

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.llm_service import LLMService, GenerationRequest
from config.settings import get_settings

async def test_mistral():
    """Test Mistral AI integration."""
    print("Testing Mistral AI integration...")
    
    # Test settings
    settings = get_settings()
    print(f"Mistral API key configured: {'Yes' if settings.mistral.api_key else 'No'}")
    print(f"Mistral model: {settings.mistral.model_name}")
    
    # Test LLM service initialization
    try:
        llm_service = LLMService(provider="mistral")
        await llm_service.initialize()
        print("✅ Mistral LLM service initialized successfully")
        
        # Test content generation
        request = GenerationRequest(
            prompt="Write a short paragraph about artificial intelligence.",
            max_tokens=100,
            temperature=0.7
        )
        
        print("Testing async generation...")
        response = await llm_service.generate_content(request)
        print(f"✅ Async generation successful: {response.content[:100]}...")
        
        print("Testing sync generation...")
        sync_response = llm_service.generate_content_sync(request)
        print(f"✅ Sync generation successful: {sync_response.content[:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mistral())