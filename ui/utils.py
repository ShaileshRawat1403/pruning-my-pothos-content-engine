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


def write_text(path: str, data: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)


def append_jsonl(path: str, record: Dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        import json as _json
        f.write(_json.dumps(record, ensure_ascii=False) + "\n")


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


def save_env_preserve_comments(new_kv: Dict[str, str], raw_lines: List[str], whitelist: List[str], path: str = ".env"):
    # backup
    ts = time.strftime("%Y%m%d-%H%M%S")
    if os.path.exists(path):
        shutil.copy2(path, f"{path}.bak-{ts}")

    keys_set = set(whitelist)
    updated_lines: List[str] = []
    seen: set[str] = set()
    for raw in raw_lines:
        s = raw.strip()
        if s and not s.startswith("#") and "=" in s:
            k, _ = s.split("=", 1)
            k = k.strip()
            if k in keys_set and k in new_kv:
                updated_lines.append(f"{k}={new_kv[k]}\n")
                seen.add(k)
                continue
        updated_lines.append(raw)
    # append any new whitelisted keys not present
    for k in whitelist:
        if k in new_kv and k not in seen:
            updated_lines.append(f"{k}={new_kv[k]}\n")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)


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


def _strip_front_matter(md: str) -> str:
    try:
        import frontmatter as _frontmatter
        post = _frontmatter.loads(md)
        return post.content or md
    except Exception:
        return md


def _markdown_to_plain(md: str) -> str:
    from markdown import markdown as _markdown
    from bs4 import BeautifulSoup as _BS

    html = _markdown(md, extensions=["extra", "sane_lists"])
    soup = _BS(html, "html.parser")
    return soup.get_text(" ").replace("\u00a0", " ").strip()


def _chunk_plain_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    s = text.strip()
    if not s:
        return []
    if chunk_size <= 0:
        return [s]
    overlap = max(0, min(overlap, chunk_size - 1))
    out: List[str] = []
    idx, length = 0, len(s)
    while idx < length:
        out.append(s[idx: idx + chunk_size])
        if idx + chunk_size >= length:
            break
        idx = idx + chunk_size - overlap
    return [c.strip() for c in out if c and c.strip()]


def chunk_counts_for_paths(paths: List[str], chunk_size: int = 900, overlap: int = 150) -> List[Tuple[str, int]]:
    stats: List[Tuple[str, int]] = []
    for path in paths:
        try:
            md = read_text(path)
        except Exception:
            continue
        body = _strip_front_matter(md)
        try:
            plain = _markdown_to_plain(body)
        except Exception:
            plain = body
        count = len(_chunk_plain_text(plain, chunk_size, overlap))
        stats.append((path, count))
    return stats


def list_slugs() -> List[str]:
    if not os.path.isdir("artifacts"):
        return []
    return sorted([d for d in os.listdir("artifacts") if os.path.isdir(os.path.join("artifacts", d))])


def load_briefs_index() -> Dict[str, Dict[str, Any]]:
    """Return slug-indexed metadata (title, tags, path) from briefs."""
    import yaml

    index: Dict[str, Dict[str, Any]] = {}
    for path in list_files_glob("briefs/*.yaml"):
        try:
            data = yaml.safe_load(read_text(path)) or {}
        except Exception:
            continue
        slug = data.get("slug")
        if not slug:
            continue
        tags = data.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        elif not isinstance(tags, list):
            tags = []
        clean_tags = [str(t).strip() for t in tags if str(t).strip()]
        index[slug] = {
            "title": data.get("title") or slug,
            "tags": clean_tags,
            "path": path,
        }
    return index


def check_ollama(base: str) -> Tuple[bool, str]:
    import requests
    try:
        r = requests.get(f"{base}/api/version", timeout=3)
        ok = r.status_code == 200
        return ok, (r.text if ok else f"HTTP {r.status_code}")
    except Exception as e:
        return False, str(e)


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


def check_wordpress(base: str) -> Tuple[bool, str]:
    import requests
    try:
        r = requests.get(f"{base.rstrip('/')}/wp-json/", timeout=5)
        ok = r.status_code == 200
        return ok, (r.text[:200] if ok else f"HTTP {r.status_code}")
    except Exception as e:
        return False, str(e)
