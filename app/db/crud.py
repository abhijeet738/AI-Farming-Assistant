"""
CRUD operations for all database models.

Each function takes a SQLAlchemy Session and performs
create/read/update/delete operations on the database.
"""

import time
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.db.models import (
    FarmProfile, ChatSession, ChatMessage,
    PredictionLog, FarmerMemory,
)
import structlog

logger = structlog.get_logger()


# ═══════════════════════════════════════════════════════════════════════════
# Farm Profiles
# ═══════════════════════════════════════════════════════════════════════════

def create_farm_profile(db: Session, user_id: str, **kwargs) -> FarmProfile:
    """Create a new farm profile for a user."""
    profile = FarmProfile(user_id=user_id, **kwargs)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    logger.info("Farm profile created", user_id=user_id, profile_id=profile.id)
    return profile


def get_farm_profiles(db: Session, user_id: str) -> List[FarmProfile]:
    """Get all farm profiles for a user."""
    stmt = select(FarmProfile).where(FarmProfile.user_id == user_id)
    return list(db.scalars(stmt).all())


def get_farm_profile(db: Session, profile_id: str, user_id: str) -> Optional[FarmProfile]:
    """Get a specific farm profile (with ownership check)."""
    stmt = select(FarmProfile).where(
        and_(FarmProfile.id == profile_id, FarmProfile.user_id == user_id)
    )
    return db.scalars(stmt).first()


def update_farm_profile(db: Session, profile_id: str, user_id: str, **kwargs) -> Optional[FarmProfile]:
    """Update a farm profile."""
    profile = get_farm_profile(db, profile_id, user_id)
    if not profile:
        return None
    for key, value in kwargs.items():
        if hasattr(profile, key) and value is not None:
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


def delete_farm_profile(db: Session, profile_id: str, user_id: str) -> bool:
    """Delete a farm profile."""
    profile = get_farm_profile(db, profile_id, user_id)
    if not profile:
        return False
    db.delete(profile)
    db.commit()
    return True


# ═══════════════════════════════════════════════════════════════════════════
# Chat Sessions
# ═══════════════════════════════════════════════════════════════════════════

def create_chat_session(db: Session, thread_id: str, user_id: str, title: str = None) -> ChatSession:
    """Create a new chat session."""
    session = ChatSession(thread_id=thread_id, user_id=user_id, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_chat_sessions(db: Session, user_id: str, limit: int = 20) -> List[ChatSession]:
    """Get recent chat sessions for a user, ordered by last activity."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.last_active_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_chat_session_by_thread(db: Session, thread_id: str) -> Optional[ChatSession]:
    """Get a chat session by thread_id."""
    stmt = select(ChatSession).where(ChatSession.thread_id == thread_id)
    return db.scalars(stmt).first()


def touch_chat_session(db: Session, thread_id: str):
    """Update the last_active_at timestamp of a chat session."""
    session = get_chat_session_by_thread(db, thread_id)
    if session:
        from datetime import datetime, timezone
        session.last_active_at = datetime.now(timezone.utc)
        db.commit()


# ═══════════════════════════════════════════════════════════════════════════
# Chat Messages
# ═══════════════════════════════════════════════════════════════════════════

def add_chat_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    tool_calls: dict = None,
    tool_results: dict = None,
) -> ChatMessage:
    """Add a message to a chat session."""
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        tool_calls=tool_calls,
        tool_results=tool_results,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_chat_messages(db: Session, session_id: str, limit: int = 50) -> List[ChatMessage]:
    """Get messages for a chat session, ordered chronologically."""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


# ═══════════════════════════════════════════════════════════════════════════
# Prediction Logs
# ═══════════════════════════════════════════════════════════════════════════

def log_prediction(
    db: Session,
    service_type: str,
    request_data: dict,
    response_data: dict,
    latency_ms: float,
    success: bool = True,
    user_id: str = None,
) -> PredictionLog:
    """Log an ML prediction for analytics and auditing."""
    log = PredictionLog(
        user_id=user_id,
        service_type=service_type,
        request_data=request_data,
        response_data=response_data,
        latency_ms=latency_ms,
        success=success,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_prediction_stats(db: Session, user_id: str = None) -> dict:
    """Get aggregated prediction statistics."""
    from sqlalchemy import func
    query = select(
        PredictionLog.service_type,
        func.count().label("total"),
        func.avg(PredictionLog.latency_ms).label("avg_latency"),
        func.sum(PredictionLog.success.cast(type_=None)).label("success_count"),
    ).group_by(PredictionLog.service_type)

    if user_id:
        query = query.where(PredictionLog.user_id == user_id)

    results = db.execute(query).all()
    return {
        row.service_type: {
            "total": row.total,
            "avg_latency_ms": round(float(row.avg_latency or 0), 2),
            "success_rate": round((row.success_count or 0) / max(row.total, 1) * 100, 1),
        }
        for row in results
    }


# ═══════════════════════════════════════════════════════════════════════════
# Farmer Memories (Long-term Agent Memory)
# ═══════════════════════════════════════════════════════════════════════════

def save_memory(db: Session, user_id: str, namespace: str, key: str, value: dict) -> FarmerMemory:
    """Save or update a memory entry for a user (upsert)."""
    stmt = select(FarmerMemory).where(
        and_(
            FarmerMemory.user_id == user_id,
            FarmerMemory.namespace == namespace,
            FarmerMemory.key == key,
        )
    )
    existing = db.scalars(stmt).first()

    if existing:
        existing.value = value
        from datetime import datetime, timezone
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        memory = FarmerMemory(user_id=user_id, namespace=namespace, key=key, value=value)
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory


def get_memories(db: Session, user_id: str, namespace: str = None) -> List[FarmerMemory]:
    """Get all memories for a user, optionally filtered by namespace."""
    stmt = select(FarmerMemory).where(FarmerMemory.user_id == user_id)
    if namespace:
        stmt = stmt.where(FarmerMemory.namespace == namespace)
    return list(db.scalars(stmt).all())


def get_memory(db: Session, user_id: str, namespace: str, key: str) -> Optional[FarmerMemory]:
    """Get a specific memory entry."""
    stmt = select(FarmerMemory).where(
        and_(
            FarmerMemory.user_id == user_id,
            FarmerMemory.namespace == namespace,
            FarmerMemory.key == key,
        )
    )
    return db.scalars(stmt).first()


def delete_memory(db: Session, user_id: str, namespace: str, key: str) -> bool:
    """Delete a specific memory entry."""
    memory = get_memory(db, user_id, namespace, key)
    if not memory:
        return False
    db.delete(memory)
    db.commit()
    return True
