from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class LoginResponse(BaseModel):
    success: bool
    token: str
    user: dict

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)


# ── Chat ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    message: str
    quick_replies: list[str]
    intent: str
    confidence: float
    response_time: float
    entities: dict

class FeedbackRequest(BaseModel):
    feedback: int = Field(..., ge=-1, le=1)


# ── Intents ───────────────────────────────────────────────────────────────

class IntentCreate(BaseModel):
    intent_name: str = Field(..., min_length=1, pattern=r"^[a-z_]+$")
    patterns: list[str] = Field(..., min_length=1)
    response_text: str = Field(..., min_length=1)
    quick_replies: Optional[list[str]] = []

class IntentUpdate(BaseModel):
    intent_name: str = Field(..., min_length=1, pattern=r"^[a-z_]+$")
    patterns: list[str] = Field(..., min_length=1)
    response_text: str = Field(..., min_length=1)
    quick_replies: Optional[list[str]] = []


# ── Users ─────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1)
    role: str = "admin"

class UserUpdate(BaseModel):
    full_name: str = Field(..., min_length=1)
    role: str = "admin"


# ── Training ──────────────────────────────────────────────────────────────

class TrainingTestRequest(BaseModel):
    message: str = Field(..., min_length=1)
