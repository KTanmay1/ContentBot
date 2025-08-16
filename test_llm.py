#!/usr/bin/env python3
"""Test script for LLM service functionality."""

import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.llm_service import get_llm_service, GenerationRequest

async def test_llm_service():
    """Test LLM service connectivity and content generation."""
    try:
        print("Testing LLM service...")
        
        # Get LLM service
        service = await get_llm_service()
        print("✅ LLM service initialized successfully")
        
        # Test content generation
        request = GenerationRequest(
            prompt="Write a short paragraph about artificial intelligence and its benefits.",
            max_tokens=100,
            temperature=0.7
        )
        
        print("🔄 Generating content...")
        response = await service.generate_content(request)
        
        print("✅ Content generated successfully")
        print(f"📝 Generated content: {response.content}")
        print(f"📊 Usage: {response.usage}")
        print(f"🤖 Model: {response.model}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm_service())
    sys.exit(0 if success else 1)