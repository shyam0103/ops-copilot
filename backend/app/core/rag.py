# app/core/rag.py
#
# RAG helper module:
# - uses a single persistent Chroma collection
# - stores all chunks (with document_id + page + user_id in metadata)
# - provides `add_chunks` and `search` helpers

from typing import Any, Dict, List, Optional
import os
import uuid

import chromadb
from chromadb.config import Settings

# Directory where Chroma DB files are stored
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
CHROMA_DIR = os.path.abspath(CHROMA_DIR)
os.makedirs(CHROMA_DIR, exist_ok=True)

# Single persistent Chroma client
_client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=Settings(anonymized_telemetry=False),
)

_COLLECTION_NAME = "ops_docs"


def get_collection():
    """Get or create the single collection we use for all document chunks."""
    return _client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(texts: List[str], metadatas: List[Dict[str, Any]]) -> None:
    """
    Add text chunks to Chroma with metadata like:
      {"document_id": 3, "page": 1, "user_id": 5}
    """
    if not texts:
        return

    if len(texts) != len(metadatas):
        raise ValueError("texts and metadatas must have same length")

    collection = get_collection()

    ids = [str(uuid.uuid4()) for _ in texts]

    collection.add(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
    )


def search(query: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    🔒 USER-SCOPED vector search over document chunks.
    
    If user_id is provided, only return chunks belonging to that user.
    """
    collection = get_collection()

    # 🔒 Build where filter for user isolation
    where_filter = None
    if user_id is not None:
        where_filter = {"user_id": user_id}

    results = collection.query(
        query_texts=[query],
        n_results=10,  # top 10 chunks across all docs
        where=where_filter  # 🔒 USER ISOLATION
    )
    return results