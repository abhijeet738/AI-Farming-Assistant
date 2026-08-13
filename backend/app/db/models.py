"""
SQLAlchemy ORM models for the Farming Assistant database.

Tables:
    1. farm_profiles     — Farmer's land and crop details
    2. chat_sessions     — LangGraph conversation threads
    3. chat_messages     — Individual messages in a session
    4. prediction_logs   — ML prediction audit trail
    5. farmer_memories   — Long-term agent memory per user
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _generate_uuid():
    return str(uuid.uuid4())


# ─── Table 1: Farm Profiles ────────────────────────────────────────────────

class FarmProfile(Base):
    """A farmer's land profile — linked to Supabase auth user ID."""
    __tablename__ = "farm_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_generate_uuid)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    farm_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    area_hectares: Mapped[float | None] = mapped_column(Float, nullable=True)
    soil_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    irrigation_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    crops: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # ["Rice", "Wheat"]
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_farm_profiles_user_id", "user_id"),
    )

    def __repr__(self):
        return f"<FarmProfile {self.farm_name} ({self.user_id})>"


# ─── Table 2: Chat Sessions ────────────────────────────────────────────────

class ChatSession(Base):
    """A conversation thread with the LangGraph agent."""
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_generate_uuid)
    thread_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationship
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ChatSession {self.thread_id}>"


# ─── Table 3: Chat Messages ────────────────────────────────────────────────

class ChatMessage(Base):
    """An individual message within a chat session."""
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_generate_uuid)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user / assistant / tool
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tool_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Relationship
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage {self.role}: {self.content[:50]}>"


# ─── Table 4: Prediction Logs ──────────────────────────────────────────────

class PredictionLog(Base):
    """Audit log for every ML prediction made by the system."""
    __tablename__ = "prediction_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_generate_uuid)
    user_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    service_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    request_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    def __repr__(self):
        return f"<PredictionLog {self.service_type} {'✓' if self.success else '✗'}>"


# ─── Table 5: Farmer Memories ──────────────────────────────────────────────

class FarmerMemory(Base):
    """Long-term memory store for the LangGraph agent (per user).

    Replaces InMemoryStore for persistent user profiles and preferences.
    """
    __tablename__ = "farmer_memories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_generate_uuid)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    namespace: Mapped[str] = mapped_column(String(50), nullable=False)  # profile / preferences
    key: Mapped[str] = mapped_column(String(100), nullable=False)  # location / crops / soil_type
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_farmer_memories_user_ns", "user_id", "namespace"),
        Index("ix_farmer_memories_upsert", "user_id", "namespace", "key", unique=True),
    )

    def __repr__(self):
        return f"<FarmerMemory {self.user_id}:{self.namespace}/{self.key}>"
