import os
import math
from typing import List

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMB_MODEL = os.getenv("EMB_MODEL", "nomic-embed-text:latest")
EMB_TIMEOUT = int(os.getenv("EMB_HTTP_TIMEOUT", "120"))
EMB_FALLBACK_MODEL = os.getenv("EMB_MODEL_FALLBACK", "BAAI/bge-small-en-v1.5")
EMB_PROVIDER = os.getenv("EMB_PROVIDER", "auto").lower()  # auto | ollama | sentence

_session = requests.Session()
_FALLBACK_ENCODER = None


def _normalize(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum((x or 0.0) ** 2 for x in vec))
    if not norm:
        return vec
    return [(x or 0.0) / norm for x in vec]


def _load_fallback_encoder():
    global _FALLBACK_ENCODER
    if _FALLBACK_ENCODER is not None:
        return _FALLBACK_ENCODER
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "SentenceTransformer fallback requested but the 'sentence-transformers' package is not installed. "
            "Install it with 'pip install sentence-transformers' or upgrade Ollama to a release that supports /api/embeddings."
        ) from exc
    _FALLBACK_ENCODER = SentenceTransformer(EMB_FALLBACK_MODEL)
    return _FALLBACK_ENCODER


def _embed_via_ollama(texts: List[str], normalize: bool) -> List[List[float]]:
    url = f"{OLLAMA_URL.rstrip('/')}/api/embeddings"
    out: List[List[float]] = []
    for text in texts:
        payload = {"model": EMB_MODEL, "prompt": text}
        resp = _session.post(url, json=payload, timeout=EMB_TIMEOUT)
        if resp.status_code == 404:
            raise RuntimeError("ollama_embeddings_unsupported")
        resp.raise_for_status()
        data = resp.json()
        vec = data.get("embedding") or data.get("data")
        if not isinstance(vec, list):
            raise RuntimeError(f"Ollama embeddings response missing vector for text: {text[:40]!r}")
        emb = [float(x) for x in vec]
        if normalize:
            emb = _normalize(emb)
        out.append(emb)
    return out


def _embed_via_sentence_transformers(texts: List[str], normalize: bool) -> List[List[float]]:
    encoder = _load_fallback_encoder()
    vecs = encoder.encode(texts, normalize_embeddings=normalize)
    return vecs.tolist()


def embed_texts(texts: List[str], *, normalize: bool = True) -> List[List[float]]:
    """Return embeddings using Ollama when available, otherwise fall back to sentence-transformers."""
    if not texts:
        return []

    errors = []
    providers = []
    if EMB_PROVIDER in ("auto", "ollama"):
        providers.append("ollama")
    if EMB_PROVIDER in ("auto", "sentence"):
        providers.append("sentence")

    for provider in providers:
        try:
            if provider == "ollama":
                return _embed_via_ollama(texts, normalize)
            if provider == "sentence":
                return _embed_via_sentence_transformers(texts, normalize)
        except RuntimeError as exc:
            if provider == "ollama" and str(exc) == "ollama_embeddings_unsupported":
                errors.append(
                    "Ollama server does not expose /api/embeddings. Upgrade Ollama (>=0.3.11) "
                    "or set EMB_PROVIDER=sentence to force the local fallback."
                )
            else:
                errors.append(str(exc))
        except requests.RequestException as exc:
            errors.append(f"Ollama embeddings request failed: {exc}")

    raise RuntimeError("; ".join(errors) or "Failed to generate embeddings.")
