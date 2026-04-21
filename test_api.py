#!/usr/bin/env python3
"""
Quick test script to verify google-genai SDK works correctly
"""
from google import genai
import os

# Test API key (replace with your actual key)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable not set")
    exit(1)

try:
    # Initialize client
    client = genai.Client(api_key=api_key)
    print("✅ Client initialized successfully")
    
    # Test simple generate_content call
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents="Say hello in one sentence"
    )
    
    print(f"✅ API call successful")
    print(f"Response type: {type(response)}")
    print(f"Response has 'text': {hasattr(response, 'text')}")
    
    if hasattr(response, "text"):
        print(f"Response text: {response.text[:100]}...")
    else:
        print(f"Response attributes: {dir(response)}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
