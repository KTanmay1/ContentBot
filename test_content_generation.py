#!/usr/bin/env python3
"""Test script to verify content generation is working properly."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.text_generator import TextGenerator
from src.models.state_models import ContentState, WorkflowStatus
from datetime import datetime

def test_content_generation():
    """Test content generation with proper input structure."""
    print("Testing content generation...")
    
    # Create test input data (matching Streamlit structure)
    input_data = {
        "text": "The benefits of artificial intelligence in healthcare",
        "target_audience": "General Public",
        "tone": "Professional",
        "word_count": 500,
        "content_type": "blog"
    }
    
    # Create content state
    state = ContentState(
        workflow_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        original_input=input_data,
        status=WorkflowStatus.INITIATED
    )
    
    print(f"Input topic: {input_data['text']}")
    print(f"Content type: {input_data['content_type']}")
    
    # Initialize text generator
    text_generator = TextGenerator()
    
    # Generate content
    try:
        result_state = text_generator.execute(state)
        
        print("\n=== GENERATION RESULTS ===")
        print(f"Generated content: {result_state.text_content.get('generated', 'NO CONTENT')}")
        print(f"Content type: {result_state.text_content.get('content_type', 'UNKNOWN')}")
        print(f"Error (if any): {result_state.text_content.get('error', 'None')}")
        
        if result_state.text_content.get('generated'):
            print("\n✅ Content generation SUCCESSFUL!")
            return True
        else:
            print("\n❌ Content generation FAILED - no content generated")
            return False
            
    except Exception as e:
        print(f"\n❌ Content generation FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_content_generation()
    sys.exit(0 if success else 1)