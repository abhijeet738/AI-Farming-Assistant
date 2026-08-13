"""
Ingestion Script: .pkl Knowledge Base → Supabase pgvector

File stats:
  - Source text : ~992,283 characters
  - Chunks      : ~1,696 (1000 char, 200 overlap)
  - Est. time   : ~30-35 minutes (Gemini free-tier rate limit)

Source : /Users/abhijeetraj/Downloads/merged_document.pkl
Target : Supabase `knowledge_embeddings` table (via pgvector)

Pipeline:
  1. Load the LangChain Document from the .pkl file
  2. Split it into ~1000-char chunks with 200-char overlap
  3. Embed each chunk with Gemini Embedding API (768-dim)
  4. Upsert every chunk into Supabase
"""

import asyncio
import hashlib
import os
import pickle
import time
from pathlib import Path

import httpx
import structlog
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from supabase import create_client

# ── Load environment ──────────────────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
logger = structlog.get_logger()

PKL_PATH = os.getenv("PKL_PATH", "merged_document.pkl")
CHUNK_SIZE = 1000  # characters
CHUNK_OVERLAP = 200  # characters

# ── Supabase client ───────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "❌ SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in your .env file."
    )

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Gemini embedding helper ───────────────────────────────────────────────────
async def embed_text(text: str) -> list[float]:
    """Get a 768-dim embedding vector from the Gemini API."""
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Missing GOOGLE_API_KEY or GEMINI_API_KEY in .env")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-embedding-2:embedContent?key={key}"
    )
    payload = {
        "model": "models/gemini-embedding-2",
        "content": {"parts": [{"text": text}]},
        "outputDimensionality": 768,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()["embedding"]["values"]


# ── Upsert one chunk to Supabase ──────────────────────────────────────────────
def upsert_chunk(doc_key: str, content: str, embedding: list[float]):
    """Upsert a text chunk + vector into the knowledge_embeddings table."""
    sb.table("knowledge_embeddings").upsert(
        {
            "doc_key":   doc_key,
            "namespace": ["knowledge", "books"],
            "content":   content,
            "embedding": embedding,
        },
        on_conflict="doc_key",
    ).execute()


# ── Main ingestion pipeline ───────────────────────────────────────────────────
async def main():
    # 1. Load the .pkl file
    logger.info("Loading .pkl file", path=PKL_PATH)
    with open(PKL_PATH, "rb") as f:
        doc = pickle.load(f)

    raw_text = doc.page_content
    sources  = doc.metadata.get("original_sources", [])
    logger.info(
        "Loaded document",
        text_length=len(raw_text),
        num_sources=len(sources),
    )
    print(f"\n📄 Total text length : {len(raw_text):,} characters")
    print(f"📚 Original sources  : {len(sources)} PDFs\n")

    # 2. Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(raw_text)
    print(f"✂️  Split into {len(chunks)} chunks "
          f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})\n")

    # 3. Fetch existing keys to skip re-uploading
    existing_data = sb.table("knowledge_embeddings").select("doc_key").execute()
    existing_keys = {row["doc_key"] for row in existing_data.data}
    print(f"⏭️  Found {len(existing_keys)} chunks already in database. Skipping them...\n")

    # 4. Embed + upsert each chunk
    success = 0
    failed  = 0
    skipped = 0

    for i, chunk in enumerate(chunks):
        # Stable, deterministic key based on content hash
        doc_key = "pkl_" + hashlib.md5(chunk.encode()).hexdigest()[:12]

        if doc_key in existing_keys:
            skipped += 1
            continue

        max_retries = 5
        for attempt in range(max_retries):
            try:
                print(f"[{i+1}/{len(chunks)}] Embedding chunk {doc_key}... (Attempt {attempt+1})", end=" ")
                embedding = await embed_text(chunk)
                upsert_chunk(doc_key, chunk, embedding)
                print("✅")
                success += 1
                break  # Success, break out of retry loop

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait_time = 15 * (2 ** attempt)  # 15s, 30s, 60s, etc.
                    print(f"⚠️ 429 Rate Limit hit! Sleeping for {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ FAILED: {e}")
                    logger.error("Chunk embedding failed", chunk_index=i, error=str(e))
                    failed += 1
                    break

            except Exception as e:
                print(f"❌ FAILED: {e}")
                logger.error("Chunk embedding failed", chunk_index=i, error=str(e))
                failed += 1
                await asyncio.sleep(2)
                break

    # 5. Summary
    print(f"\n{'='*50}")
    print(f"✅ Successfully ingested : {success} chunks")
    print(f"⏭️  Skipped (already in DB): {skipped} chunks")
    print(f"❌ Failed                : {failed} chunks")
    print(f"📦 Total in Supabase     : {success} new knowledge vectors")
    print(f"{'='*50}")
    print("\n🎉 Done! Your RAG knowledge base is now populated with real book content.")


if __name__ == "__main__":
    asyncio.run(main())
