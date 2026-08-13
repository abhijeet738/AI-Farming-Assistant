import os

import httpx
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
resp = httpx.get(url)
models = resp.json().get("models", [])
for m in models:
    if "embed" in m["name"].lower() or "embed" in str(m.get("supportedGenerationMethods", "")).lower():
        print(m["name"])
