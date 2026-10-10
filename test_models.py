import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load the free tier key from your .env file
load_dotenv()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

print("Available Text Models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)