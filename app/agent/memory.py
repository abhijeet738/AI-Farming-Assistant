"""
Long-term memory helpers for per-user farmer profiles.

Uses LangGraph's InMemoryStore to persist farmer preferences,
crop history, and location across conversation sessions.
"""


import structlog

from app.db import crud
from app.db.database import SessionLocal

logger = structlog.get_logger()


async def load_farmer_profile(store, user_id: str) -> str:
    """Load a farmer's stored profile from the SQL database.

    Returns:
        A formatted string of known farmer details, or empty string.
    """
    if user_id == "default":
        # Skip for unauthenticated test users
        return ""

    try:
        db = SessionLocal()
        memories = crud.get_memories(db, user_id=user_id, namespace="profile")
        db.close()

        if not memories:
            return ""

        parts = []
        for mem in memories:
            data = mem.value.get("data", "")
            if data:
                parts.append(data)

        return "\n".join(parts)
    except Exception as e:
        logger.warning("Failed to load farmer profile from DB", user_id=user_id, error=str(e))
        return ""


async def save_farmer_detail(store, user_id: str, key: str, detail: str) -> None:
    """Save a specific detail about a farmer to the SQL database.

    Args:
        store: The LangGraph memory store (ignored, using DB).
        user_id: Unique identifier for the farmer.
        key: The type of detail (e.g., "location", "crops", "soil_type").
        detail: The detail string to save.
    """
    if user_id == "default":
        return

    try:
        db = SessionLocal()
        crud.save_memory(db, user_id=user_id, namespace="profile", key=key, value={"data": detail})
        db.close()
        logger.info("Saved farmer detail to DB", user_id=user_id, key=key)
    except Exception as e:
        logger.error("Failed to save farmer detail to DB", user_id=user_id, error=str(e))


async def search_knowledge(store, query: str, limit: int = 3) -> str:
    """Semantic search across the farming knowledge base.

    1. First tries to search using persistent Supabase pgvector.
    2. Falls back to ephemeral InMemoryStore if pgvector is unavailable.
    """
    try:
        from app.agent.vector_store import search_knowledge_pgvector
        pg_results = await search_knowledge_pgvector(query, limit)
        if pg_results:
            logger.info("RAG search successful via pgvector")
            return pg_results
    except Exception as e:
        logger.warning("pgvector search failed, falling back to InMemoryStore", error=str(e))

    # Fallback to InMemoryStore
    try:
        results = store.search(("knowledge",), query=query, limit=limit)
        if not results:
            return ""

        return "\n\n---\n\n".join([r.value.get("text", "") for r in results])
    except Exception as e:
        logger.warning("Knowledge search fallback failed, continuing without RAG", error=str(e))
        return ""
