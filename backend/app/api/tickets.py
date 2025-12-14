# app/api/tickets.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.models.db_models import Ticket
from app.models.schemas import TicketCreate, TicketOut
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter(tags=["tickets"])


@router.post("/tickets", response_model=TicketOut)
def create_ticket(
    payload: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 🔒 Create ticket with user_id
    ticket = Ticket(
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        status="open",
        user_id=current_user.id  # 🔒 USER ISOLATION
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/tickets", response_model=List[TicketOut])
def list_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 🔒 Only return tickets belonging to current user
    tickets = (
        db.query(Ticket)
        .filter(Ticket.user_id == current_user.id)  # 🔒 USER ISOLATION
        .order_by(Ticket.created_at.desc())
        .all()
    )
    return tickets