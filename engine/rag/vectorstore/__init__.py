import os

os.environ.setdefault("QDRANT_TELEMETRY_OPTOUT", "1")
os.environ.setdefault("QDRANT_DISABLE_TELEMETRY", "1")

from .chroma_store import ChromaStore
from .qdrant_store import QdrantStore


def get_store():
    backend = (os.getenv("VDB_BACKEND", "chroma") or "chroma").lower()
    if backend == "qdrant":
        return QdrantStore(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection=os.getenv("QDRANT_COLLECTION", "content"),
        )
    # default: chroma
    return ChromaStore(
        path=os.getenv("DB_DIR", "engine/.chroma"),
        collection=os.getenv("CHROMA_COLLECTION", "content"),
    )
