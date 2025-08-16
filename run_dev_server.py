#!/usr/bin/env python3
"""Development server script for ViraLearn Content Agent API."""
# Step 18: Add development server script for local testing.
# Why: Provides easy way to run the API locally for development and testing,
# completing Phase 3 deployment readiness.

import uvicorn
from src.api.main import create_app

if __name__ == "__main__":
    # Create app with debug mode for development
    app = create_app(debug=True)
    
    # Run development server
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info",
    )
