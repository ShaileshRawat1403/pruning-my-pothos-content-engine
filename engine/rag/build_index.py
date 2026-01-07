# engine/rag/build_index.py
import os
# Silence python-dotenv auto-loading and Chroma telemetry globally
os.environ.setdefault("PYTHON_DOTENV_DISABLE_AUTO", "true")
os.environ.setdefault("DOTENV_VERBOSE", "0")
os.environ.setdefault("CHROMA_TELEMETRY_DISABLED", "1")
os.environ.setdefault("POSTHOG_DISABLED", "1")
os.environ.setdefault("CHROMA_LOG_LEVEL", "ERROR")
import glob
import hashlib
from typing import List, Tuple
import fnmatch
import uuid

# --- Minimal .env loader ---
def _load_dotenv_file():
    path = os.path.join(os.getcwd(), ".env")
    if not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                raw = line.rstrip("\n")
                s = raw.strip()
                if not s or s.startswith("#"):
                    continue
                if "=" not in s:
                    continue
                k, v = s.split("=", 1)
                k = k.strip()
                vv = v.strip()
                if (vv.startswith('"') and vv.endswith('"')) or (vv.startswith("'") and vv.endswith("'")):
                    vv = vv[1:-1]
                else:
                    if "#" in vv:
                        vv = vv.split("#", 1)[0]
                    vv = vv.strip()
                if k and vv and k not in os.environ:
                    os.environ[k] = vv
    except Exception:
        pass

_load_dotenv_file()
from markdown import markdown
from bs4 import BeautifulSoup
from engine.rag.vectorstore import get_store
from engine.rag.embeddings import embed_texts

# ---- Config (env-overridable) ----
CONTENT_DIR   = os.getenv("CONTENT_DIR", "content")

UUID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://pruningmypothos.com/vector-chunks")

# Tunables for chunking / batching
CHUNK_SIZE      = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP   = int(os.getenv("CHUNK_OVERLAP", "150"))
EMB_BATCH_SIZE  = int(os.getenv("EMB_BATCH_SIZE", "32"))

def md_to_text(md: str) -> str:
    """Convert Markdown to plain text with minimal structure loss."""
    html = markdown(md, extensions=["extra", "sane_lists"])
    soup = BeautifulSoup(html, "html.parser")
    # Normalize whitespace (incl. non-breaking space) and strip
    return soup.get_text(" ").replace("\u00a0", " ").strip()

def chunks_with_overlap(s: str, n: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Produce overlapping chunks so context flows across boundaries."""
    s = s.strip()
    if not s:
        return []
    if n <= 0:
        return [s]
    overlap = max(0, min(overlap, n - 1))
    out: List[str] = []
    i, L = 0, len(s)
    while i < L:
        out.append(s[i : i + n])
        if i + n >= L:
            break
        i = i + n - overlap
    # Drop empty/whitespace-only chunks
    return [c.strip() for c in out if c and c.strip()]

def stable_file_id(fp: str) -> str:
    """Stable ID prefix per file to keep chunk IDs deterministic across machines."""
    rel = os.path.relpath(fp, start=CONTENT_DIR)
    return hashlib.sha1(rel.encode("utf-8", errors="ignore")).hexdigest()[:12]

def collect_docs() -> List[Tuple[str, List[str]]]:
    """Return list of (file_path, chunks[]) for all Markdown files."""
    out: List[Tuple[str, List[str]]] = []
    # Optional exclude patterns (comma-separated), defaults to skipping content/imports
    excludes_raw = os.getenv("INDEX_EXCLUDE", "content/imports/**")
    exclude_patterns = [p.strip() for p in excludes_raw.split(",") if p.strip()]
    for fp in sorted(glob.glob(f"{CONTENT_DIR}/**/*.md", recursive=True)):
        # Skip excluded paths
        rel = os.path.normpath(fp)
        if any(fnmatch.fnmatch(rel, pat) for pat in exclude_patterns):
            continue
        try:
            with open(fp, "r", encoding="utf-8") as f:
                txt = md_to_text(f.read())
        except UnicodeDecodeError:
            with open(fp, "r", encoding="latin-1", errors="ignore") as f:
                txt = md_to_text(f.read())
        chs = chunks_with_overlap(txt, CHUNK_SIZE, CHUNK_OVERLAP)
        if chs:
            out.append((fp, chs))
    return out

def main():
    file_docs = collect_docs()
    if not file_docs:
        print("No documents found in content/. Add Markdown and re-run.")
        return

    store = get_store()
    dim = None

    total_chunks = 0
    file_count = 0

    for fp, chunks in file_docs:
        file_count += 1
        file_prefix = stable_file_id(fp)

        # Delta reindex: remove any existing chunks for this file
        store.delete_by_source(fp)

        # Prepare documents & metadata
        ids   = [str(uuid.uuid5(UUID_NAMESPACE, f"{file_prefix}:{i}")) for i in range(len(chunks))]
        metas = [{"source": fp, "chunk_index": i} for i in range(len(chunks))]

        embeds: List[List[float]] = []
        for i in range(0, len(chunks), EMB_BATCH_SIZE):
            batch = chunks[i : i + EMB_BATCH_SIZE]
            vecs = embed_texts(batch, normalize=True)
            embeds.extend(vecs)

        if dim is None and embeds:
            dim = len(embeds[0])
            store.ensure_collection(dim)

        store.upsert(ids, chunks, embeds, metas)

        total_chunks += len(chunks)
        print(f"Indexed {len(chunks):4d} chunks from {fp}")

    print(f"\nDone. Indexed {total_chunks} chunks from {file_count} files.")

if __name__ == "__main__":
    main()
