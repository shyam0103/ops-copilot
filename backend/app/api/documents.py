# app/api/documents.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import os
from pypdf import PdfReader
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.models.db_models import Document, Chunk
from app.models.user import User
from app.core.rag import add_chunks
from app.core.llm_client import LLMClient
from app.core.security import get_current_user

router = APIRouter(tags=["documents"])

UPLOAD_DIR = "./uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def extract_pdf_text(path: str) -> List[str]:
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return pages


def is_image_file(filename: str, content_type: str) -> bool:
    """Check if the file is an image based on extension or content type."""
    image_extensions = {".png", ".jpg", ".jpeg"}
    image_content_types = {"image/png", "image/jpeg"}
    
    ext = os.path.splitext(filename.lower())[1]
    return ext in image_extensions or content_type in image_content_types


def is_pdf_file(filename: str, content_type: str) -> bool:
    """Check if the file is a PDF based on extension or content type."""
    return filename.lower().endswith(".pdf") or content_type == "application/pdf"


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Determine file type
    is_image = is_image_file(file.filename, file.content_type or "")
    is_pdf = is_pdf_file(file.filename, file.content_type or "")
    
    if not is_image and not is_pdf:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF, PNG, JPG, and JPEG files are allowed."
        )
    
    # Save file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # 🔒 Insert into documents table with user_id
    doc = Document(
        name=file.filename,
        path=file_path,
        user_id=current_user.id  # 🔒 USER ISOLATION
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    chunk_texts = []
    metadatas = []

    if is_pdf:
        # Handle PDF files (existing logic)
        pages = extract_pdf_text(file_path)
        chunk_texts = [page for page in pages if page.strip()]
        metadatas = [
            {
                "document_id": doc.id,
                "page": idx,
                "source": "pdf",
                "user_id": current_user.id  # 🔒 USER ISOLATION IN METADATA
            }
            for idx in range(len(chunk_texts))
        ]
    
    elif is_image:
        # Handle image files with Gemini Vision
        llm_client = LLMClient()
        text = llm_client.extract_image_text(file_path)
        
        if text.strip():
            chunk_texts = [text]
            metadatas = [
                {
                    "document_id": doc.id,
                    "page": 0,
                    "source": "image",
                    "filename": file.filename,
                    "user_id": current_user.id  # 🔒 USER ISOLATION IN METADATA
                }
            ]

    # Insert chunks into Chroma + SQLite
    if chunk_texts:
        add_chunks(chunk_texts, metadatas)

        # Also store chunk rows in SQLite
        for idx, text in enumerate(chunk_texts):
            # For images, use the metadata we already created; for PDFs use page idx
            meta_info = {"page": metadatas[idx].get("page", idx)}
            if is_image:
                meta_info["source"] = "image"
                meta_info["filename"] = file.filename
            
            chunk = Chunk(
                document_id=doc.id,
                content=text,
                meta_json=str(meta_info),
                user_id=current_user.id  # 🔒 USER ISOLATION
            )
            db.add(chunk)

    db.commit()
    return {"message": "uploaded", "document_id": doc.id, "chunks": len(chunk_texts)}