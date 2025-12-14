# app/api/chat.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict

from app.agents.graph import run_ops_graph
from app.models.schemas import ChatResponse, TraceStep
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    # Previous conversation from frontend; list of {role, content}
    conversation: List[Dict[str, str]] = []


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user)  # 🔒 USER AUTHENTICATION
):
    # 🔒 Pass user_id into graph for multi-tenant isolation
    initial_state = {
        "user_message": payload.message,
        "conversation": payload.conversation,
        "user_id": current_user.id  # 🔒 USER ISOLATION
    }

    final_state = run_ops_graph(initial_state)

    reply_text = final_state.get("answer", "")

    # If a ticket was created, append info
    ticket_id = final_state.get("ticket_id")
    if ticket_id is not None:
        reply_text += (
            f"\n\n📌 I have created a ticket for this issue.\n"
            f"Ticket ID: {ticket_id}"
        )

    updated_conversation = final_state.get("conversation", [])
    
    # Get the trace from the final state
    trace_data = final_state.get("trace", [])

    return ChatResponse(
        reply=reply_text,
        conversation=updated_conversation,
        trace=trace_data,
    )