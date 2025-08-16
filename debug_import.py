#!/usr/bin/env python3

import sys
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")

try:
    import google.generativeai as genai
    print("✅ google.generativeai imported successfully")
    print(f"Module location: {genai.__file__}")
except ImportError as e:
    print(f"❌ Failed to import google.generativeai: {e}")
    
try:
    import google
    print(f"✅ google package found at: {google.__file__}")
    print(f"Google package contents: {dir(google)}")
except ImportError as e:
    print(f"❌ Failed to import google package: {e}")