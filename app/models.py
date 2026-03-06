from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    response_id: str


class SessionDeleteResponse(BaseModel):
    session_id: str
    cleared: bool


class AdminStatusResponse(BaseModel):
    vector_store_id: str
    status: str
    file_count: int


class AdminSetupResponse(BaseModel):
    vector_store_id: str
    message: str


class HealthResponse(BaseModel):
    status: str
    model: str
    vector_store_configured: bool
