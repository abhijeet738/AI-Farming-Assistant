import os

import httpx
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

url2 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent?key={key}"
data2 = {
    "model": "models/gemini-embedding-2",
    "content": {
        "parts": [{"text": "Hello world"}]
    },
    "outputDimensionality": 768
}

resp2 = httpx.post(url2, json=data2)
print("status:", resp2.status_code)
if resp2.status_code == 200:
    vec = resp2.json()["embedding"]["values"]
    print("dims:", len(vec))
