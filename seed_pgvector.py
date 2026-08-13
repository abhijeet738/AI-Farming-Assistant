"""
One-time script to seed the Supabase pgvector table with the knowledge base.
"""

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from supabase import Client, create_client

# Load environment variables
load_dotenv()

# Import the raw knowledge documents
# We need to add the backend dir to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agent.knowledge import KNOWLEDGE_DOCUMENTS  # noqa: E402


def get_supabase_client() -> Client:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("Missing Supabase credentials in .env")
    return create_client(supabase_url, supabase_key)

async def embed_text(text: str) -> list[float]:
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Missing GOOGLE_API_KEY or GEMINI_API_KEY in .env")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent?key={key}"
    data = {
        "model": "models/gemini-embedding-2",
        "content": {"parts": [{"text": text}]},
        "outputDimensionality": 768
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=data)
        resp.raise_for_status()
        return resp.json()["embedding"]["values"]

async def seed():
    print("🌱 Starting pgvector seed script...")

    sb = get_supabase_client()

    print(f"Found {len(KNOWLEDGE_DOCUMENTS)} documents in knowledge.py")

    success_count = 0
    for namespace_tuple, doc_key, value in KNOWLEDGE_DOCUMENTS:
        try:
            content = value["text"]
            namespace_str = namespace_tuple[1] if len(namespace_tuple) > 1 else namespace_tuple[0]

            print(f"Embedding {doc_key} ({namespace_str})...")
            # 1. Embed the document text
            vector = await embed_text(content)

            # 2. Upsert to Supabase
            data = {
                "namespace": namespace_str,
                "doc_key": doc_key,
                "content": content,
                "embedding": vector,
            }

            sb.table("knowledge_embeddings").upsert(
                data,
                on_conflict="doc_key"
            ).execute()

            success_count += 1

        except Exception as e:
            print(f"❌ Error inserting {doc_key}: {e}")

    print(f"\n✅ Successfully seeded {success_count} documents to pgvector!")

if __name__ == "__main__":
    asyncio.run(seed())
