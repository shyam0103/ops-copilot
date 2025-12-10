# app/models/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any


class TicketCreate(BaseModel):
    title: str
    description: str
    severity: str = "medium"  # optional field


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    severity: str
    created_at: datetime

    class Config:
        from_attributes = True  # pydantic v2 equivalent of orm_mode = True


# NEW: TraceStep model for frontend
class TraceStep(BaseModel):
    node: str
    description: str
    doc_ids: List[int] | None = None


# Existing model for conversation messages (assuming it was missing but required by ChatResponse)
# Replicating structure implied by graph.py and chat.py
class MessageSchema(BaseModel):
    role: str
    content: str


# Extended ChatResponse to include optional trace
class ChatResponse(BaseModel):
    reply: str
    # Assuming this should use MessageSchema for strong typing,
    # but based on current usage (List[Dict[str, str]]), we'll use that for consistency
    conversation: List[Dict[str, str]]  # Updated conversation
    trace: List[TraceStep] | None = None