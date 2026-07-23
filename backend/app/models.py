from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime,
    Enum, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    username   = Column(String(80), unique=True, nullable=False)
    password   = Column(String(255), nullable=False)
    full_name  = Column(String(150))
    role       = Column(Enum("superadmin", "admin"), nullable=False, default="admin")
    is_active  = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)

    sessions = relationship("AdminSession", back_populates="user", cascade="all, delete-orphan")


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=False)
    token      = Column(String(100), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("AdminUser", back_populates="sessions")


class Intent(Base):
    __tablename__ = "intents"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    intent_name   = Column(String(100), unique=True, nullable=False)
    patterns      = Column(Text, comment="JSON array of patterns")
    response_text = Column(Text, comment="Response text")
    quick_replies = Column(Text, comment="JSON array of quick replies")
    created_at    = Column(DateTime, default=datetime.now)
    updated_at    = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ConversationLog(Base):
    __tablename__ = "conversation_logs"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    session_id      = Column(String(100), nullable=False)
    user_message    = Column(Text, nullable=False)
    bot_response    = Column(Text, nullable=False)
    intent_detected = Column(String(100))
    confidence      = Column(Float)
    response_time   = Column(Float)
    feedback        = Column(Integer, comment="1=positif, -1=negatif, 0=netral/null")
    timestamp       = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_session", "session_id"),
        Index("idx_intent", "intent_detected"),
        Index("idx_ts", "timestamp"),
    )
