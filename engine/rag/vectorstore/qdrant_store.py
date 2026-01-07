from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue


class QdrantStore:
    def __init__(self, url: str, api_key: str, collection: str):
        self._client = QdrantClient(url=url, api_key=api_key)
        self._collection = collection

    def ensure_collection(self, dim: int):
        try:
            self._client.get_collection(self._collection)
        except Exception:
            self._client.recreate_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    def delete_by_source(self, source_path: str):
        try:
            self._client.delete(
                collection_name=self._collection,
                points_selector=Filter(must=[FieldCondition(key="source", match=MatchValue(value=source_path))]),
            )
        except Exception:
            pass

    def upsert(self, ids: List[str], texts: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]):
        points = []
        for pid, text, vec, meta in zip(ids, texts, embeddings, metadatas):
            points.append(PointStruct(id=pid, vector=vec, payload={"text": text, **meta}))
        self._client.upsert(collection_name=self._collection, points=points)

    def search(self, query_vector: List[float], k: int) -> List[Dict[str, Any]]:
        res = self._client.search(collection_name=self._collection, query_vector=query_vector, limit=max(1, k * 3), with_payload=True, with_vectors=False)
        out: List[Dict[str, Any]] = []
        for sp in res:
            payload = sp.payload or {}
            out.append({
                "text": payload.get("text", ""),
                "source": payload.get("source"),
                "score": sp.score,
            })
        out.sort(key=lambda h: (-(h["score"] if h.get("score") is not None else -1e9)))
        return out

