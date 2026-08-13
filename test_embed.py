import os

import httpx
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={key}"

data = {
    "model": "models/text-embedding-004",
    "content": {
        "parts": [{"text": "Hello world"}]
    }
}

resp = httpx.post(url, json=data)
print("status:", resp.status_code)

url2 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={key}"
data2 = {
    "model": "models/gemini-embedding-001",
    "content": {
        "parts": [{"text": "Hello world"}]
    }
}

resp2 = httpx.post(url2, json=data2)
print("status2:", resp2.status_code)
if resp2.status_code == 200:
    vec = resp2.json()["embedding"]["values"]
    print("dims:", len(vec))
