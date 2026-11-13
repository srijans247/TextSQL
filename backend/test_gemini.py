
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

print("Starting Gemini test...", flush=True)

load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

if not api_key:
    raise RuntimeError("Gemini API key not found.")

print("API key loaded.", flush=True)
print("Model:", model, flush=True)

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=20000)
)

print("Sending request to Gemini...", flush=True)

try:
    response = client.models.generate_content(
        model=model,
        contents="Reply with exactly: Gemini connection successful!"
    )

    print("Response received:", flush=True)
    print(response.text, flush=True)

except Exception as error:
    print("Request failed:", repr(error), flush=True)
