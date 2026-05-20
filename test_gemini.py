import os
import google.generativeai as genai
from dotenv import load_dotenv

api_key = "AIzaSyD7INk3ZbkM9WKYKS7wmlFphTohaA4zygM"
print(f"Key loaded: {api_key[:10]}...")

try:
    genai.configure(api_key=api_key)
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print("API Error:", e)
