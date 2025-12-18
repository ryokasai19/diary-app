import google.generativeai as genai
import sys
import os

# 1. Check Python & Library Location
print(f"🐍 Python Path: {sys.executable}")
print(f"📚 Library Version: {genai.__version__}")

# 2. Setup Key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # PASTE YOUR KEY HERE FOR THE TEST
    api_key = "YOUR_ACTUAL_API_KEY_HERE" 

genai.configure(api_key=api_key)

# 3. List Available Models
print("\n📋 AVAILABLE MODELS:")
try:
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(f" - {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")