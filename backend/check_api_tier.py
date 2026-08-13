import asyncio
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

async def embed_dummy_text(client, key, index):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent?key={key}"
    payload = {
        "model": "models/gemini-embedding-2",
        "content": {"parts": [{"text": f"dummy text {index}"}]},
    }
    resp = await client.post(url, json=payload)
    return resp.status_code

async def test_tier():
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        print("No API key found in .env")
        return

    print("Testing API key tier by sending 25 rapid requests...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [embed_dummy_text(client, key, i) for i in range(25)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        status_codes = []
        for r in results:
            if isinstance(r, int):
                status_codes.append(r)
            else:
                status_codes.append("Error")

        print(f"Results: {status_codes}")

        if 429 in status_codes:
            print("\nResult: FREE TIER (Rate limited at 429 Too Many Requests)")
        elif all(code == 200 for code in status_codes):
            print("\nResult: PAID TIER (Successfully handled 25 rapid requests)")
        else:
            print("\nResult: UNKNOWN (Check status codes above)")

if __name__ == "__main__":
    asyncio.run(test_tier())
