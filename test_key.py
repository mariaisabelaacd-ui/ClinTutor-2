from google import genai
import toml
import os

print("--- TESTING GEMINI 3 FLASH PREVIEW ---")

try:
    data = toml.load(".streamlit/secrets.toml")
    api_key = data["google_api"]["api_key"]
    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview", 
        contents="Say 'Hello Gemini 3'"
    )
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"FAILURE: {e}")
