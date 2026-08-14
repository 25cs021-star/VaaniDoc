from pydantic import BaseModel, Field
from typing import List, Optional


class IntakeRequest(BaseModel):
    language: str = Field(..., examples=["Hindi"])
    symptoms_text: str = Field(..., min_length=1, examples=["मुझे दो दिन से बुखार और सिरदर्द है"])


class IntakeResponse(BaseModel):
    session_id: str
    language: str
    original_text: str
    symptoms: List[str]
    duration: str
    severity: str
    category: str
    summary: str
    engine: str
    created_at: str
    expires_at: str


class SessionSummary(BaseModel):
    session_id: str
    language: str
    category: str
    created_at: str
    status: str


class EndSessionResponse(BaseModel):
    session_id: str
    status: str
    ended_at: str
