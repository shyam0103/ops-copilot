from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.core.db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=func.now())

    # 🔐 multi-tenant ownership
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    meta_json = Column(Text, nullable=True)

    # 🔐 multi-tenant ownership (IMPORTANT for RAG)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="open")
    severity = Column(String, nullable=False, default="medium")
    created_at = Column(DateTime, default=func.now())

    # 🔐 ticket belongs to a user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
