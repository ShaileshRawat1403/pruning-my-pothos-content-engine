import os
# Silence python-dotenv auto-loading and Chroma telemetry globally
os.environ.setdefault("PYTHON_DOTENV_DISABLE_AUTO", "true")
os.environ.setdefault("DOTENV_VERBOSE", "0")
os.environ.setdefault("CHROMA_TELEMETRY_DISABLED", "1")
os.environ.setdefault("POSTHOG_DISABLED", "1")
os.environ.setdefault("CHROMA_LOG_LEVEL", "ERROR")
from typing import List, Tuple, Dict, Any
import re
from engine.rag.vectorstore import get_store
from engine.rag.embeddings import embed_texts
import frontmatter

# ---- Config (env-overridable) ----
K_DEFAULT        = int(os.getenv("RETRIEVE_K", "6"))
MAX_PER_SOURCE   = int(os.getenv("RETRIEVE_MAX_PER_SOURCE", "2"))  # diversify evidence

# ---- Clients ----
_store    = get_store()

def _normalize_query_vec(text: str):
    vecs = embed_texts([text], normalize=True)
    if not vecs:
        return []
    return vecs[0]

def _dedup_by_source(hits: List[Dict[str, Any]], cap: int) -> List[Dict[str, Any]]:
    """Keep at most `cap` hits per source, preserving order (best first)."""
    if cap <= 0:
        return hits
    seen_counts: Dict[str, int] = {}
    out: List[Dict[str, Any]] = []
    for h in hits:
        src = h.get("source", "")
        c = seen_counts.get(src, 0)
        if c < cap:
            out.append(h)
            seen_counts[src] = c + 1
    return out

def retrieve(query: str, k: int = K_DEFAULT) -> Tuple[str, List[str]]:
    """
    Returns (context_text, unique_sources) where context_text is a newline-joined
    sequence of retrieved passages. Applies per-source cap to diversify context.
    """
    # Defensive: empty collection
    # Chroma doesn't expose a direct "count" here, so catch empty results gracefully.
    qv = _normalize_query_vec(query)
    if not qv:
        return "", []
    try:
        tmp = _store.search(qv, max(1, k * 3))
    except Exception:
        return "", []

    # Dedup by source to increase diversity
    hits = _dedup_by_source(tmp, MAX_PER_SOURCE)

    # Filter out off-topic/meta artifacts to reduce junk context
    patterns = [
        r"^\s*document:\s*",
        r"^\s*your task:\s*",
        r"i\'m sorry",
        r"in a hypothet",
        r"the greatest goodwin",
    ]
    bad = re.compile("|".join(patterns), re.I | re.M)
    filtered = []
    for h in hits:
        txt = h.get("text", "") or ""
        if not bad.search(txt):
            filtered.append(h)
    if filtered:
        hits = filtered

    # Optional dynamic exclude regex via env (e.g., provided by brief)
    try:
        ex_pat = os.getenv("RETRIEVE_EXCLUDE_REGEX")
        if ex_pat:
            ex = re.compile(ex_pat, re.I | re.M)
            hits = [h for h in hits if not ex.search(h.get("text", "") or "")]
    except Exception:
        pass

    # Prefer first-party notes in content/ over imported web pages
    def _is_first_party(src: str) -> bool:
        try:
            return isinstance(src, str) and src.startswith("content/") and "/imports/" not in src
        except Exception:
            return False
    first_party = [h for h in hits if _is_first_party(h.get("source", ""))]
    others = [h for h in hits if not _is_first_party(h.get("source", ""))]
    if first_party:
        hits = first_party + others

    # Special rule: prioritize GitHub Docs over generic GitHub repo READMEs
    def _source_host(path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                post = frontmatter.loads(f.read())
            host = post.get("source_host")
            if isinstance(host, str):
                return host.lower().strip()
        except Exception:
            pass
        return ""

    docs_pref = [h for h in hits if _source_host(h.get("source", "")) == "docs.github.com"]
    gh_repo = [h for h in hits if _source_host(h.get("source", "")) == "github.com"]
    middle = [h for h in hits if h not in docs_pref and h not in gh_repo]
    if docs_pref or gh_repo:
        hits = docs_pref + middle + gh_repo

    # Optional source prefix prioritization via env (comma-separated)
    try:
        pref = [p.strip() for p in os.getenv("RETRIEVE_SOURCE_PREFIXES", "").split(",") if p.strip()]
        if pref:
            prio = [h for h in hits if any(str(h.get("source", "")).startswith(p) for p in pref)]
            rest = [h for h in hits if h not in prio]
            if prio:
                hits = prio + rest
    except Exception:
        pass

    # Trim to k after dedup, join as context
    hits = hits[:k]
    context = "\n\n".join(h["text"] for h in hits if h.get("text"))
    sources = list(dict.fromkeys(h["source"] for h in hits if h.get("source")))

    return context, sources
