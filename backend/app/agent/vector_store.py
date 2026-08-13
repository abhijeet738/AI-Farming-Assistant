"""
Supabase pgvector integration for the Knowledge Base.

Performance architecture:
  - Embedding is done once per unique query (cached in _embed_cache)
  - Similarity search is done inside Postgres via match_knowledge() RPC
    (no more fetching all rows over HTTP!)
"""

import os

import structlog
from supabase import Client, create_client

logger = structlog.get_logger()

# In-process cache: query text -> embedding vector
# Avoids calling Gemini API twice for the same question
_embed_cache: dict[str, list[float]] = {}

# Initialize Supabase client (once, at module level)
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    logger.warning("SUPABASE_URL or SUPABASE_KEY not set in environment.")
    sb_client: Client | None = None
else:
    sb_client = create_client(supabase_url, supabase_key)


import httpx


async def embed_text(text: str) -> list[float]:
    """Get the Google embedding vector."""
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


async def search_knowledge_pgvector(query: str, limit: int = 3) -> str:
    """
    Fast semantic search using Supabase pgvector.

    Flow:
      1. Check in-process embedding cache (skip Gemini call if repeated query)
      2. Embed the query via Gemini API (1 HTTP call)
      3. Call match_knowledge() Postgres RPC — similarity computed in Postgres,
         only top-K rows returned over the wire (not the full table!)
    """
    if not sb_client:
        logger.warning("Supabase client not initialized. Cannot perform pgvector search.")
        return ""

    try:
        # 1. Embed query (cached)
        if query in _embed_cache:
            query_vector = _embed_cache[query]
            logger.debug("Embedding cache hit", query=query[:50])
        else:
            query_vector = await embed_text(query)
            _embed_cache[query] = query_vector

        # 2. Call match_knowledge() RPC — Postgres does the vector search
        #    Returns only `limit` rows, not the full table.
        response = sb_client.rpc(
            "match_knowledge",
            {
                "query_embedding": query_vector,
                "match_count": limit,
            }
        ).execute()

        if not response.data:
            return ""

        # Join top-k results
        return "\n\n---\n\n".join([row["content"] for row in response.data])

    except Exception as e:
        logger.error("pgvector search failed", error=str(e))
        raise
