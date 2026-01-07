import os
import sys
import uuid
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Ensure project root is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from engine.utils import (
    list_files_glob,
    list_slugs,
    list_ollama_models,
    read_text,
    run_cmd,
    artifacts_for_slug,
    load_env_preserve_comments,
    WHITELIST_ENV_KEYS,
)
from engine.rag.search import retrieve
from engine.run import ollama_complete, _sanitize_context, _assert_ollama_up, _assert_model_available
from engine.rag.vectorstore import get_store
from engine.rag.build_index import (
    md_to_text,
    chunks_with_overlap,
    stable_file_id,
    UUID_NAMESPACE,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMB_BATCH_SIZE,
)
from engine.rag.embeddings import embed_texts
# Reuse UI helpers for env writes, quick health checks, and chunk counts
try:
    from ui.utils import (
        save_env_preserve_comments,
        check_ollama,
        check_wordpress,
        chunk_counts_for_paths,
        load_briefs_index,
    )  # type: ignore
except Exception:  # pragma: no cover
    save_env_preserve_comments = None  # type: ignore
    check_ollama = None  # type: ignore
    check_wordpress = None  # type: ignore
    chunk_counts_for_paths = None  # type: ignore
    load_briefs_index = None  # type: ignore

app = FastAPI(
    title="Agentic Content Engine API",
    version="0.1.0",
)

# CORS for React dev/hosted frontends (default: allow all; override via API_CORS_ORIGINS=foo,bar)
cors_origins = [o.strip() for o in os.getenv("API_CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    brief_path: str
    env: Optional[Dict[str, str]] = None


class ContentPath(BaseModel):
    path: str


class WriteContentRequest(BaseModel):
    path: str
    content: str


class ChatRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    persona: Optional[str] = None
    first_party_only: Optional[bool] = None
    allowed_domains: Optional[List[str]] = None

def get_ollama_url() -> str:
    return os.environ.get("OLLAMA_URL", "http://localhost:11434")


def _safe_content_path(rel_path: str) -> str:
    """Resolve a user-provided path within content/ to a safe absolute path."""
    base = os.path.realpath(os.path.join(ROOT_DIR, "content"))
    target = os.path.realpath(os.path.join(base, rel_path))
    if not target.startswith(base):
        raise HTTPException(status_code=400, detail="Path outside content/")
    if not target.endswith(".md"):
        target = target + ("" if target.endswith(".md") else ".md")
    return target

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/api/settings")
def get_settings():
    """Returns whitelisted settings from the .env file."""
    env_vars, _ = load_env_preserve_comments()
    
    # Also load from os.environ as a fallback
    for key in WHITELIST_ENV_KEYS:
        if key not in env_vars and key in os.environ:
            env_vars[key] = os.environ[key]

    return {key: env_vars.get(key) for key in WHITELIST_ENV_KEYS if env_vars.get(key) is not None}

@app.get("/api/briefs", response_model=List[str])
def get_briefs():
    """Returns a list of available brief YAML files."""
    return list_files_glob("briefs/*.yaml")


@app.get("/api/briefs/index")
def get_briefs_index():
    """Returns slug->metadata mapping from briefs."""
    return load_briefs_index()

@app.get("/api/briefs/{brief_path:path}")
def get_brief_content(brief_path: str):
    """Returns the content of a specific brief file."""
    # Basic security: ensure the path is within the 'briefs' directory
    # brief_path is relative to the project root, e.g. "briefs/example.yaml"
    full_path = os.path.realpath(os.path.join(ROOT_DIR, brief_path))
    
    if not full_path.startswith(os.path.join(ROOT_DIR, 'briefs')):
        raise HTTPException(status_code=400, detail="Invalid brief path")
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail=f"Brief not found at {full_path}")

    return {"content": read_text(full_path)}

@app.get("/api/artifacts", response_model=List[str])
def get_artifacts():
    """Returns a list of generated artifact slugs."""
    return list_slugs()

@app.get("/api/artifacts/{slug:path}")
def get_artifact_details(slug: str):
    """Returns details and content for a given artifact slug."""
    # Basic security
    safe_base_dir = os.path.realpath(os.path.join(ROOT_DIR, "artifacts"))
    slug_path = os.path.realpath(os.path.join(safe_base_dir, slug))
    if not slug_path.startswith(safe_base_dir):
        raise HTTPException(status_code=400, detail="Invalid artifact slug")

    paths = artifacts_for_slug(slug)
    
    def read_safe(path):
        try:
            return read_text(path)
        except Exception:
            return None

    meta_files = {}
    if os.path.isdir(paths["meta"]):
        for fn in sorted(os.listdir(paths["meta"])):
            content = read_safe(os.path.join(paths["meta"], fn))
            if content:
                meta_files[fn] = content

    return {
        "slug": slug,
        "paths": paths,
        "content": {
            "blog_md": read_safe(paths["blog_md"]),
            "linkedin_md": read_safe(paths["li_md"]),
            "instagram_md": read_safe(paths["ig_md"]),
            "meta_files": meta_files,
        }
    }


@app.get("/api/content/list")
def list_content():
    """List Markdown files under content/ with size, mtime, and estimated chunk counts."""
    base = os.path.realpath(os.path.join(ROOT_DIR, "content"))
    entries = []
    for root, _, files in os.walk(base):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            fp = os.path.realpath(os.path.join(root, fn))
            rel = os.path.relpath(fp, base)
            try:
                size = os.path.getsize(fp)
                mtime = os.path.getmtime(fp)
            except Exception:
                size = 0
                mtime = 0
            entries.append({"path": rel, "size": size, "mtime": mtime})
    # Optional chunk estimates
    if chunk_counts_for_paths:
        try:
            counts = dict(chunk_counts_for_paths([os.path.join(base, e["path"]) for e in entries]))
            for e in entries:
                e["chunks"] = counts.get(os.path.join(base, e["path"]), None)
        except Exception:
            pass
    # Sort newest first
    entries.sort(key=lambda e: e.get("mtime", 0), reverse=True)
    return entries


@app.post("/api/content/read")
def read_content(req: ContentPath):
    path = _safe_content_path(req.path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return {"path": req.path, "content": read_text(path)}


@app.post("/api/content/write")
def write_content(req: WriteContentRequest):
    path = _safe_content_path(req.path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(req.content)
    return {"status": "ok", "path": req.path}


@app.get("/api/models", response_model=List[str])
def get_models():
    """Returns a list of available Ollama models."""
    return list_ollama_models(get_ollama_url())


@app.get("/api/index/stats")
def index_stats():
    """Return quick stats about the knowledge base."""
    base = os.path.realpath(os.path.join(ROOT_DIR, "content"))
    files = [os.path.realpath(os.path.join(base, p)) for p in list_files_glob("content/**/*.md")]
    total_files = len(files)
    total_chunks = None
    top_files = []
    if chunk_counts_for_paths and files:
        try:
            counts = chunk_counts_for_paths(files)
            total_chunks = sum(c for _, c in counts)
            # top 10 by chunk count
            top = sorted(counts, key=lambda t: t[1], reverse=True)[:10]
            top_files = [
                {
                    "path": os.path.relpath(p, base),
                    "chunks": c,
                }
                for p, c in top
            ]
        except Exception:
            pass
    # heuristic last-indexed: mtime of DB dir
    db_dir = os.path.realpath(os.path.join(ROOT_DIR, os.getenv("DB_DIR", "engine/.chroma")))
    last_indexed = None
    try:
        last_indexed = os.path.getmtime(db_dir)
    except Exception:
        pass
    return {
        "total_files": total_files,
        "total_chunks": total_chunks,
        "top_files": top_files,
        "last_indexed": last_indexed,
        "vdb_backend": os.getenv("VDB_BACKEND", "chroma"),
    }

@app.post("/api/generate")
async def generate_content(req: GenerateRequest):
    """
    Runs the content generation engine for a given brief and streams the output.
    """
    # Security: Validate brief_path again
    brief_full_path = os.path.realpath(os.path.join(ROOT_DIR, req.brief_path))

    if not brief_full_path.startswith(os.path.join(ROOT_DIR, 'briefs')) or not os.path.exists(brief_full_path):
        raise HTTPException(status_code=400, detail="Invalid or non-existent brief path")

    command = [sys.executable, "-m", "engine.run", req.brief_path]
    
    async def stream_output():
        for line in run_cmd(command, env=req.env):
            yield f"data: {line}\n\n"
            
    return StreamingResponse(stream_output(), media_type="text/event-stream")


@app.post("/api/index")
async def rebuild_index():
    """Rebuild the vector index (chroma/qdrant) with streaming logs."""
    command = [sys.executable, "-m", "engine.rag.build_index"]

    async def stream_output():
        for line in run_cmd(command):
            yield f"data: {line}\n\n"

    return StreamingResponse(stream_output(), media_type="text/event-stream")


@app.post("/api/index/file")
def index_single_file(req: ContentPath):
    """Re-index a single Markdown file under content/."""
    path = _safe_content_path(req.path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    # Read markdown with fallback
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1", errors="ignore") as f:
            raw = f.read()

    plain = md_to_text(raw)
    chunks = chunks_with_overlap(plain, CHUNK_SIZE, CHUNK_OVERLAP)
    store = get_store()
    # Remove old entries for this source
    store.delete_by_source(path)
    if not chunks:
        return {"status": "ok", "chunks": 0}
    file_prefix = stable_file_id(path)
    ids = [str(uuid.uuid5(UUID_NAMESPACE, f"{file_prefix}:{i}")) for i in range(len(chunks))]
    metas = [{"source": path, "chunk_index": i} for i in range(len(chunks))]
    embeds = []
    for i in range(0, len(chunks), EMB_BATCH_SIZE):
        batch = chunks[i : i + EMB_BATCH_SIZE]
        embeds.extend(embed_texts(batch, normalize=True))
    if embeds:
        store.ensure_collection(len(embeds[0]))
    store.upsert(ids, chunks, embeds, metas)
    return {"status": "ok", "chunks": len(chunks)}


class RegenerateRequest(BaseModel):
    brief_path: str
    section: str
    min_len: int | None = None
    env: Optional[Dict[str, str]] = None


@app.post("/api/regenerate")
async def regenerate_section(req: RegenerateRequest):
    """Regenerate a single section deterministically."""
    brief_full_path = os.path.realpath(os.path.join(ROOT_DIR, req.brief_path))
    if not brief_full_path.startswith(os.path.join(ROOT_DIR, "briefs")) or not os.path.exists(brief_full_path):
        raise HTTPException(status_code=400, detail="Invalid or non-existent brief path")

    env = req.env or {}
    env.update({
        "GEN_ONLY_SECTION": req.section,
        "GEN_ONLY_SECTION_MINLEN": str(req.min_len or ""),
        "SKIP_PUBLISH": "1",
    })
    command = [sys.executable, "-m", "engine.run", req.brief_path]

    async def stream_output():
        for line in run_cmd(command, env=env):
            yield f"data: {line}\n\n"

    return StreamingResponse(stream_output(), media_type="text/event-stream")


@app.post("/api/lora/dataset")
async def build_lora_dataset():
    """Build LoRA dataset from artifacts."""
    command = [sys.executable, "tools/lora/build_dataset.py"]

    async def stream_output():
        for line in run_cmd(command):
            yield f"data: {line}\n\n"

    return StreamingResponse(stream_output(), media_type="text/event-stream")


@app.post("/api/lora/split")
async def split_lora_dataset():
    """Split LoRA dataset into train/val."""
    command = [sys.executable, "tools/lora/split_dataset.py"]

    async def stream_output():
        for line in run_cmd(command):
            yield f"data: {line}\n\n"

    return StreamingResponse(stream_output(), media_type="text/event-stream")


@app.post("/api/settings")
async def update_settings(payload: Dict[str, str]):
    """Persist whitelisted settings back to .env (preserving comments/order)."""
    if save_env_preserve_comments is None:
        raise HTTPException(status_code=500, detail="save_env_preserve_comments unavailable")
    current, raw_lines = load_env_preserve_comments()
    for k in list(payload.keys()):
        if k not in WHITELIST_ENV_KEYS:
            payload.pop(k, None)
    merged = dict(current)
    merged.update({k: v for k, v in payload.items() if v is not None})
    save_env_preserve_comments(merged, raw_lines, WHITELIST_ENV_KEYS)
    return {"status": "ok"}


@app.get("/api/ollama-check")
def api_ollama_check():
    base = get_ollama_url()
    if check_ollama:
        ok, msg = check_ollama(base)
        return {"ok": ok, "detail": msg}
    # Fallback simple check
    try:
        import requests
        r = requests.get(f"{base}/api/version", timeout=3)
        r.raise_for_status()
        return {"ok": True, "detail": r.json()}
    except Exception as e:  # pragma: no cover
        return {"ok": False, "detail": str(e)}


@app.get("/api/wp-check")
def api_wp_check():
    if check_wordpress:
        ok, msg = check_wordpress()
        return {"ok": ok, "detail": msg}
    return {"ok": False, "detail": "WordPress check helper unavailable"}


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    """Lightweight RAG chat: retrieve context and stream a concise answer with citations."""
    try:
        _assert_ollama_up()
        _assert_model_available()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama unavailable: {e}") from e
    k = req.top_k or int(os.getenv("RETRIEVE_K", "6"))
    # Optional first-party preference via env override
    prev_prefix = os.getenv("RETRIEVE_SOURCE_PREFIXES")
    if req.first_party_only:
        os.environ["RETRIEVE_SOURCE_PREFIXES"] = "content/"
    try:
        context, sources = retrieve(req.query, k=k)
    finally:
        if req.first_party_only:
            if prev_prefix is None:
                os.environ.pop("RETRIEVE_SOURCE_PREFIXES", None)
            else:
                os.environ["RETRIEVE_SOURCE_PREFIXES"] = prev_prefix
    context = _sanitize_context(context)
    prompt = (
        "You are a concise assistant. Answer using only the provided context. "
        "If the answer is missing, say so briefly. Cite sources with [1], [2] based on the reference list.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {req.query}\n\n"
        "RESPONSE:"
    )
    answer = ollama_complete(prompt, length="short")
    return {"answer": answer.strip(), "sources": sources}


import tempfile

class IngestRequest(BaseModel):
    urls: List[str]

@app.post("/api/ingest")
async def ingest_urls(req: IngestRequest):
    """
    Ingests a list of URLs and streams the output.
    """
    if not req.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tf:
        for url in req.urls:
            tf.write(url + "\n")
        tmpfile = tf.name

    command = [sys.executable, "-m", "engine.ingest", "--urls", tmpfile]
    
    async def stream_output():
        try:
            for line in run_cmd(command):
                yield f"data: {line}\n\n"
        finally:
            os.remove(tmpfile)
            
    return StreamingResponse(stream_output(), media_type="text/event-stream")


# The following is a placeholder for running the server.
# We will add a proper run command to the Makefile later.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("engine.api:app", host="0.0.0.0", port=8000, reload=True)
