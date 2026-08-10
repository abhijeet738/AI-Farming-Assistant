"""
Supabase pgvector integration for the Knowledge Base.
"""

import json
import os
import structlog
from supabase import create_client, Client
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = structlog.get_logger()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

if not supabase_url or not supabase_key:
    logger.warning("SUPABASE_URL or SUPABASE_ANON_KEY not set in environment.")
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
    Semantic search using Supabase pgvector.
    
    1. Embeds the user query (1 API call)
    2. Performs cosine similarity search in Postgres via RPC (if defined) or direct matching
    """
    if not sb_client:
        logger.warning("Supabase client not initialized. Cannot perform pgvector search.")
        return ""
        
    try:
        # 1. Embed the query
        query_vector = await embed_text(query)
        
        # 2. Search Supabase
        # Supabase Python client doesn't support direct vector math in select() 
        # unless using a Postgres function (RPC). But we can fetch all and sort, 
        # or we should create a match_knowledge function in Supabase.
        # For simplicity, if we don't have an RPC, we fetch and use cosine sim locally, 
        # BUT the right way is via RPC. Let's try calling an RPC first.
        
        # Wait, the migration script didn't create a match_knowledge function.
        # Let's fallback to retrieving all KB docs (there are only 15) and calculating 
        # similarity in Python if we can't do it via RPC, or I'll provide the RPC script.
        # Actually, let's just fetch all and do a quick sort in Python to save adding another SQL step.
        # For 15 docs, fetching them all is instantaneous.
        
        response = sb_client.table("knowledge_embeddings").select("doc_key, content, embedding").execute()
        
        if not response.data:
            return ""
            
        import numpy as np
        
        # Helper to calculate cosine similarity
        def cosine_similarity(v1, v2):
            return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            
        query_np = np.array(query_vector)
        
        # Calculate scores
        results = []
        for row in response.data:
            # Parse the embedding string from Supabase (usually format "[0.1, 0.2, ...]")
            try:
                emb_str = row["embedding"]
                if isinstance(emb_str, str):
                    emb = json.loads(emb_str)
                else:
                    emb = emb_str
                score = cosine_similarity(query_np, np.array(emb))
                results.append((score, row["content"]))
            except Exception as ex:
                logger.warning(f"Error parsing embedding for {row.get('doc_key')}: {ex}")
                
        # Sort by highest score first
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Get top-k
        top_results = results[:limit]
        
        return "\n\n---\n\n".join([r[1] for r in top_results])
        
    except Exception as e:
        logger.error("pgvector search failed", error=str(e))
        raise
