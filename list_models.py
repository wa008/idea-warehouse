
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("gemini_api_key")
genai.configure(api_key=gemini_api_key)

for m in genai.list_models():
  if 'generateContent' in m.supported_generation_methods:
    print(m.name)
