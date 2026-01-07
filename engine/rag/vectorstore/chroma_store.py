from typing import List, Dict, Any
import os
import logging

# Silence python-dotenv auto-parser and Chroma telemetry before importing chromadb
os.environ.setdefault("PYTHON_DOTENV_DISABLE_AUTO", "true")
os.environ.setdefault("DOTENV_VERBOSE", "0")
os.environ.setdefault("CHROMA_TELEMETRY_DISABLED", "1")
os.environ.setdefault("POSTHOG_DISABLED", "1")
os.environ.setdefault("CHROMA_LOG_LEVEL", "ERROR")

import chromadb
from chromadb.config import Settings
logging.getLogger("chromadb").setLevel(logging.ERROR)
logging.getLogger("chromadb.telemetry").disabled = True
try:
    import chromadb.telemetry.posthog as _chroma_posthog

    def _disable_capture(*args, **kwargs):
        return None

    _chroma_posthog.capture = _disable_capture  # type: ignore[attr-defined]
except Exception:
    pass


class ChromaStore:
    def __init__(self, path: str, collection: str):
        self._client = chromadb.PersistentClient(path=path, settings=Settings(anonymized_telemetry=False))
        self._col = self._client.get_or_create_collection(collection)

    def ensure_collection(self, dim: int):
        # Chroma doesn't require dim; collection is created in __init__
        return

    def delete_by_source(self, source_path: str):
        try:
            self._col.delete(where={"source": source_path})
        except Exception:
            pass

    def upsert(self, ids: List[str], texts: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]):
        self._col.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

    def search(self, query_vector: List[float], k: int) -> List[Dict[str, Any]]:
        res = self._col.query(query_embeddings=[query_vector], n_results=max(1, k), include=["documents", "metadatas", "distances"])
        if not res or not res.get("ids") or not res["ids"][0]:
            return []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        out: List[Dict[str, Any]] = []
        for i in range(len(docs)):
            meta = metas[i] if i < len(metas) else {}
            dist = dists[i] if i < len(dists) else None
            score = None
            if dist is not None:
                # Convert distance (lower better) to score (higher better)
                try:
                    score = 1.0 - float(dist)
                except Exception:
                    score = None
            out.append({
                "text": docs[i] if i < len(docs) else "",
                "source": meta.get("source") if isinstance(meta, dict) else None,
                "score": score,
            })
        # sort by score desc if available
        out.sort(key=lambda h: (-(h["score"] if h.get("score") is not None else -1e9)))
        return out
