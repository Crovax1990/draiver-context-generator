import google.generativeai as genai
import os

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("GOOGLE_API_KEY not found")
else:
    genai.configure(api_key=api_key)
    print("--- Available Models ---")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"LLM: {m.name}")
            if 'embedContent' in m.supported_generation_methods:
                print(f"Embedding: {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")
