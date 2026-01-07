from __future__ import annotations
from __future__ import annotations

import os
import re
import sys
import argparse
import datetime as _dt
import yaml
import requests
import frontmatter
from urllib.parse import urlparse
from bs4 import BeautifulSoup

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

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
GEN_MODEL  = os.getenv("GEN_MODEL", "phi3:mini-128k")

CONTENT_DIR = os.getenv("CONTENT_DIR", "content")
IMPORT_DIR  = os.path.join(CONTENT_DIR, "imports")


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def slugify(text: str) -> str:
    t = re.sub(r"[^A-Za-z0-9\-\_]+", "-", text.strip().lower())
    t = re.sub(r"-+", "-", t).strip("-")
    return t or "doc"


def _github_to_raw(u: str) -> str | None:
    try:
        p = urlparse(u)
        if p.netloc != "github.com":
            return None
        parts = [x for x in p.path.split("/") if x]
        if len(parts) < 2:
            return None
        owner, repo = parts[0], parts[1]
        # /owner/repo → try README.md on main then master
        if len(parts) == 2:
            for branch in ("main", "master"):
                raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
                try:
                    rr = requests.get(raw, timeout=6, headers={"User-Agent": "pm-pothos-ingest/1.0"})
                    if rr.status_code == 200 and rr.text:
                        return raw
                except Exception:
                    pass
            return None
        # /owner/repo/blob/<branch>/<path>
        if len(parts) >= 4 and parts[2] == "blob":
            branch = parts[3]
            file_path = "/".join(parts[4:])
            return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
        # /owner/repo/tree/<branch>/<dir> → attempt README.md in dir on branch
        if len(parts) >= 4 and parts[2] == "tree":
            branch = parts[3]
            dir_path = "/".join(parts[4:])
            return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{dir_path}/README.md"
    except Exception:
        return None
    return None


def fetch_url(url: str, timeout=30) -> tuple[str, str]:
    # Prefer raw content for GitHub to avoid page chrome
    raw = _github_to_raw(url)
    target = raw or url
    r = requests.get(target, timeout=timeout, headers={"User-Agent": "pm-pothos-ingest/1.0"})
    r.raise_for_status()
    return r.text, r.url


def clean_html(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "svg", "nav", "footer", "form", "aside"]):
        tag.decompose()
    return soup


def html_to_markdown(soup: BeautifulSoup) -> str:
    # Minimal HTML → Markdown pass with common blocks
    out = []

    def text_of(el):
        return el.get_text(" ", strip=True)

    def handle(el):
        name = getattr(el, "name", None)
        if name is None:
            return
        if name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(name[1])
            out.append("#" * level + " " + text_of(el))
            out.append("")
        elif name in ["p", "blockquote"]:
            txt = text_of(el)
            if txt:
                if name == "blockquote":
                    out.append("> " + txt)
                else:
                    out.append(txt)
                out.append("")
        elif name in ["ul", "ol"]:
            for li in el.find_all("li", recursive=False):
                out.append("- " + text_of(li))
            out.append("")
        elif name == "pre":
            code = el.get_text("\n", strip=False)
            out.append("```\n" + code.rstrip() + "\n```")
            out.append("")
        elif name == "table":
            # Skip complex tables; extract text rows
            rows = []
            for tr in el.find_all("tr", recursive=False):
                cells = [text_of(td) for td in tr.find_all(["td", "th"], recursive=False)]
                if cells:
                    rows.append(" | ".join(cells))
            if rows:
                out.extend(rows)
                out.append("")
        # Links handled implicitly as text; keep URLs inline where obvious

    body = soup.body or soup
    # If article-like container exists, prefer it
    art = body.find(["article", "main"])
    root = art or body
    for el in root.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote", "ul", "ol", "pre", "table"], recursive=True):
        handle(el)

    md = "\n".join(out).strip()
    # Collapse excessive blank lines
    lines = []
    blank = 0
    for ln in md.splitlines():
        if ln.strip() == "":
            blank += 1
            if blank <= 1:
                lines.append("")
        else:
            blank = 0
            lines.append(ln.rstrip())
    return "\n".join(lines).strip()


def extract_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(" ", strip=True)
    return "Untitled"


def _build_options(num_predict: int, temperature: float):
    opts = {"num_predict": num_predict, "temperature": temperature}
    # Optional shared knobs via env
    if os.getenv("GEN_NUM_CTX"):            opts["num_ctx"]            = int(os.getenv("GEN_NUM_CTX"))
    if os.getenv("GEN_NUM_THREAD"):         opts["num_thread"]         = int(os.getenv("GEN_NUM_THREAD"))
    if os.getenv("GEN_NUM_BATCH"):          opts["num_batch"]          = int(os.getenv("GEN_NUM_BATCH"))
    if os.getenv("GEN_TOP_K"):              opts["top_k"]              = int(os.getenv("GEN_TOP_K"))
    if os.getenv("GEN_TOP_P"):              opts["top_p"]              = float(os.getenv("GEN_TOP_P"))
    if os.getenv("GEN_REPEAT_PENALTY"):     opts["repeat_penalty"]     = float(os.getenv("GEN_REPEAT_PENALTY"))
    if os.getenv("GEN_PRESENCE_PENALTY"):   opts["presence_penalty"]   = float(os.getenv("GEN_PRESENCE_PENALTY"))
    if os.getenv("GEN_FREQUENCY_PENALTY"):  opts["frequency_penalty"]  = float(os.getenv("GEN_FREQUENCY_PENALTY"))
    if os.getenv("GEN_MIROSTAT"):           opts["mirostat"]           = int(os.getenv("GEN_MIROSTAT"))
    if os.getenv("GEN_MIROSTAT_TAU"):       opts["mirostat_tau"]       = float(os.getenv("GEN_MIROSTAT_TAU"))
    if os.getenv("GEN_MIROSTAT_ETA"):       opts["mirostat_eta"]       = float(os.getenv("GEN_MIROSTAT_ETA"))
    return opts

def ollama_complete(prompt: str, *, num_predict: int = 256, temperature: float = 0.2, timeout: int = 120) -> str:
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": GEN_MODEL, "prompt": prompt, "stream": False, "options": _build_options(num_predict, temperature)},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except Exception:
        return ""


def enrich_text(md_text: str) -> dict:
    prompt = (
        "You are an editorial assistant. Read the text and return JSON with keys: "
        "title (<=100 chars), summary (2 sentences), tags (3-7 short tags).\n\nTEXT:\n" + md_text[:4000]
    )
    resp = ollama_complete(prompt, num_predict=300)
    try:
        data = yaml.safe_load(resp) if resp.strip().startswith("{") is False else None
        if not data:
            import json as _json
            data = _json.loads(resp)
        # Normalize
        out = {}
        if "title" in data: out["title"] = str(data["title"])[:100]
        if "summary" in data: out["summary"] = str(data["summary"]).strip()
        if "tags" in data:
            tags = data["tags"]
            if isinstance(tags, str):
                tags = [t.strip() for t in re.split(r",|;|\n", tags) if t.strip()]
            if isinstance(tags, list):
                out["tags"] = [str(t)[:40] for t in tags][:7]
        return out
    except Exception:
        return {}


def write_markdown(md_text: str, meta: dict, out_path: str):
    post = frontmatter.Post(md_text, **meta)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))


def ingest_url(url: str, *, tags=None, enrich=False, force=False) -> str:
    html, final_url = fetch_url(url)
    soup = clean_html(html)
    title = extract_title(soup)
    md = html_to_markdown(soup)

    # front matter
    dt = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    host = urlparse(final_url).netloc
    base_slug = slugify(title) or slugify(host)
    ensure_dir(IMPORT_DIR)
    out_path = os.path.join(IMPORT_DIR, base_slug + ".md")
    if os.path.exists(out_path) and not force:
        return out_path

    meta = {
        "title": title,
        "source_url": final_url,
        "retrieved": dt,
        "tags": tags or [],
        "source_host": host,
        "license": "unknown"
    }
    if enrich:
        add = enrich_text(md)
        for k, v in add.items():
            # don't overwrite explicitly provided tags
            if k == "tags" and meta.get("tags"):
                continue
            meta[k] = v

    write_markdown(md, meta, out_path)
    return out_path


def run_from_urls_file(urls_file: str, *, add_tags=None, enrich=False, force=False):
    with open(urls_file, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]
    for u in lines:
        try:
            p = ingest_url(u, tags=add_tags, enrich=enrich, force=force)
            print(f"Saved: {p}")
        except Exception as e:
            print(f"Failed: {u} -> {e}")


def run_from_yaml(yaml_file: str, *, enrich=False, force=False):
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    entries = data if isinstance(data, list) else data.get("sources", [])
    for item in entries:
        if isinstance(item, str):
            url, tags = item, []
        elif isinstance(item, dict):
            url = item.get("url"); tags = item.get("tags", [])
        else:
            continue
        if not url: continue
        try:
            p = ingest_url(url, tags=tags, enrich=enrich, force=force)
            print(f"Saved: {p}")
        except Exception as e:
            print(f"Failed: {url} -> {e}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Ingest web sources into content/imports as Markdown with metadata.")
    ap.add_argument("--urls", help="Path to a plain text file with one URL per line")
    ap.add_argument("--yaml", help="Path to a YAML file with a list of {url,tags}")
    ap.add_argument("--tag", action="append", dest="tags", help="Additional tag(s) for all ingested items")
    ap.add_argument("--enrich", action="store_true", help="Use LLM to generate summary/tags/title suggestions")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files if present")
    args = ap.parse_args(argv)

    if not args.urls and not args.yaml:
        print("Usage: python -m engine.ingest --urls sources/urls.txt [--tag t1 --tag t2] [--enrich]")
        sys.exit(2)

    ensure_dir(IMPORT_DIR)
    add_tags = args.tags or []
    if args.urls:
        run_from_urls_file(args.urls, add_tags=add_tags, enrich=args.enrich, force=args.force)
    if args.yaml:
        run_from_yaml(args.yaml, enrich=args.enrich, force=args.force)


if __name__ == "__main__":
    main()
