# app/core/rag.py
#
# RAG helper module:
# - uses a single persistent Chroma collection
# - stores all chunks (with document_id + page in metadata)
# - provides `add_chunks` and `search` helpers

from typing import Any, Dict, List
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
      {"document_id": 3, "page": 1}
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


def search(query: str) -> Dict[str, Any]:
    """
    Simple vector search over all document chunks.

    We intentionally ask for more results (n_results=10) so that
    when there are multiple documents, we don't get stuck only
    on the very first one.
    """
    collection = get_collection()

    results = collection.query(
        query_texts=[query],
        n_results=10,  # top 10 chunks across all docs
    )
    return results
