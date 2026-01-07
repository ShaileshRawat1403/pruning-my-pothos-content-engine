import os
import io
import time
import json
import shutil
import subprocess
import re
from typing import Any, Dict, Iterable, List, Tuple, Optional


WHITELIST_ENV_KEYS = [
    # Runtime
    "OLLAMA_URL", "GEN_MODEL", "GEN_TEMPERATURE", "GEN_SEED", "GEN_PERSONA",
    "GEN_MAX_CTX", "GEN_MAX_PREDICT",
    # Retrieval
    "RETRIEVE_K", "RETRIEVE_MAX_PER_SOURCE",
    # WP
    "WP_BASE_URL", "WP_USER", "WP_APP_PASSWORD",
    # VDB
    "VDB_BACKEND", "DB_DIR", "CHROMA_COLLECTION",
    "QDRANT_URL", "QDRANT_COLLECTION", "QDRANT_API_KEY",
    # Lint tuning
    "MINLEN_OVERVIEW", "MINLEN_WHY_IT_MATTERS", "MINLEN_PREREQUISITES",
    "MINLEN_STEPS", "MINLEN_EXAMPLES", "MINLEN_FAQS", "MINLEN_REFERENCES",
]


def run_cmd(args: List[str], env: Optional[Dict[str, str]] = None, cwd: Optional[str] = None) -> Iterable[str]:
    proc_env = os.environ.copy()
    if env:
        proc_env.update({k: str(v) for k, v in env.items() if v is not None})
    p = subprocess.Popen(
        args,
        cwd=cwd or os.getcwd(),
        env=proc_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    try:
        assert p.stdout is not None
        for line in p.stdout:
            yield line.rstrip("\n")
    finally:
        p.wait()


def list_files_glob(glob_pattern: str) -> List[str]:
    import glob
    return sorted(glob.glob(glob_pattern))


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_env_preserve_comments(path: str = ".env") -> Tuple[Dict[str, str], List[str]]:
    if not os.path.exists(path):
        return {}, []
    kv: Dict[str, str] = {}
    lines: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f.readlines():
            lines.append(raw)
            s = raw.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            kv[k.strip()] = v.strip()
    return kv, lines

def _safe_basename(candidate: Optional[str], fallback: str) -> str:
    for name in (candidate, fallback):
        if not name:
            continue
        base = re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")
        if base:
            return base
    return fallback


def _first_existing(paths: List[str]) -> str:
    for p in paths:
        if p and os.path.exists(p):
            return p
    return paths[0] if paths else ""

def artifacts_for_slug(slug: str, title: Optional[str] = None) -> Dict[str, str]:
    base = os.path.join("artifacts", slug)
    blog_dir = os.path.join(base, "blog")
    basename = _safe_basename(title, slug)
    md_candidates = [
        os.path.join(blog_dir, f"{basename}.md"),
        os.path.join(blog_dir, "latest.md"),
        os.path.join(blog_dir, "draft.md"),
    ]
    html_candidates = [
        os.path.join(blog_dir, f"{basename}.html"),
        os.path.join(blog_dir, "latest.html"),
        os.path.join(blog_dir, "draft.html"),
    ]
    if os.path.isdir(blog_dir):
        extras = sorted(
            [os.path.join(blog_dir, fn) for fn in os.listdir(blog_dir) if fn.endswith(".md") and not fn.startswith("draft_") and not fn.endswith("latest.md")],
            reverse=True,
        )
        md_candidates.extend(extras)
        extras_html = sorted(
            [os.path.join(blog_dir, fn) for fn in os.listdir(blog_dir) if fn.endswith(".html") and not fn.startswith("draft_") and not fn.endswith("latest.html")],
            reverse=True,
        )
        html_candidates.extend(extras_html)

    blog_md_path = _first_existing(md_candidates)
    blog_html_path = _first_existing(html_candidates)

    return {
        "base": base,
        "blog_md": blog_md_path,
        "blog_html": blog_html_path,
        "li_md": os.path.join(base, "social", "linkedin.md"),
        "ig_md": os.path.join(base, "social", "instagram.md"),
        "meta": os.path.join(base, "meta"),
        "index": os.path.join(base, "index.html"),
    }

def list_slugs() -> List[str]:
    if not os.path.isdir("artifacts"):
        return []
    return sorted([d for d in os.listdir("artifacts") if os.path.isdir(os.path.join("artifacts", d))])

def list_ollama_models(base: str) -> List[str]:
    """Return installed Ollama model names (empty list on error)."""
    import requests
    try:
        b = base.rstrip("/")
        r = requests.get(f"{b}/api/tags", timeout=4)
        r.raise_for_status()
        data = r.json()
        names: List[str] = []
        if isinstance(data, dict) and isinstance(data.get("models"), list):
            for m in data["models"]:
                if isinstance(m, dict):
                    name = m.get("name")
                    if name:
                        names.append(str(name))
        return names
    except Exception:
        return []
