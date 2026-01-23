import os
# Silence python-dotenv auto-loading globally to allow comments in .env
os.environ.setdefault("PYTHON_DOTENV_DISABLE_AUTO", "true")
os.environ.setdefault("DOTENV_VERBOSE", "0")
os.environ.setdefault("CHROMA_TELEMETRY_DISABLED", "1")
os.environ.setdefault("POSTHOG_DISABLED", "1")
os.environ.setdefault("CHROMA_LOG_LEVEL", "ERROR")

import sys
import re
import json
import yaml
import requests
import datetime
import frontmatter
import numpy as np
from typing import Optional
from urllib.parse import urlparse
import re as _re

from engine.rag.embeddings import embed_texts


try:
    from engine.graph.neo4j_store import record_run  # type: ignore
except Exception:  # pragma: no cover
    record_run = None  # type: ignore

# --- Minimal .env loader (no external deps) ---
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
                # Strip inline comments unless value is quoted
                vv = v.strip()
                if (vv.startswith('"') and vv.endswith('"')) or (vv.startswith("'") and vv.endswith("'")):
                    vv = vv[1:-1]
                else:
                    # remove inline comment starting at first #
                    if "#" in vv:
                        vv = vv.split("#", 1)[0]
                    vv = vv.strip()
                if k and vv and k not in os.environ:
                    os.environ[k] = vv
    except Exception:
        pass

_load_dotenv_file()
from engine.rag.search import retrieve
from engine.tools.html import md_to_clean_html
from engine.tools.formatting import linkedin_format, instagram_format, blog_format, github_format

# Env
CURRENT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
GEN_MODEL = os.getenv("GEN_MODEL", "phi3:mini-128k")
GEN_MODEL_FALLBACK = os.getenv("GEN_MODEL_FALLBACK", "llama3.2:3b")
EMB_MODEL = os.getenv("EMB_MODEL", "nomic-embed-text:latest")

# History store for duplicate checks
HIST_DIR = "artifacts/_history"
HIST_PATH = os.path.join(HIST_DIR, "embeddings.jsonl")


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def safe_basename(title: str, slug: str) -> str:
    base = (title or slug or "draft").lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base or (slug or "draft")


def _predict_tokens_for_length(length: str) -> int:
    # Safe caps so generation doesn't hang forever while still allowing richer sections
    return {
        "short": 700,
        "medium": 1400,
        "long": 2200,
    }.get((length or "medium").lower(), 1400)


def _gen_options_from_env(length: str) -> dict:
    """Build generation options with sensible defaults; can override via .env"""
    base_cap = _predict_tokens_for_length(length)
    env_override = os.getenv("GEN_NUM_PREDICT")
    num_predict = base_cap if not env_override else min(int(env_override), base_cap)
    opts = {
        "num_ctx": int(os.getenv("GEN_NUM_CTX", "120000")),
        "num_predict": num_predict,
        # Default to deterministic sampling unless explicitly overridden
        "temperature": float(os.getenv("GEN_TEMPERATURE", "0.0")),
    }
    # Optional reproducibility: fixed seed for deterministic sampling where supported
    if os.getenv("GEN_SEED"):
        try:
            opts["seed"] = int(os.getenv("GEN_SEED"))
        except Exception:
            pass
    # Optional performance/tuning knobs (only include if set)
    if os.getenv("GEN_NUM_THREAD"):        opts["num_thread"]        = int(os.getenv("GEN_NUM_THREAD"))
    if os.getenv("GEN_NUM_BATCH"):         opts["num_batch"]         = int(os.getenv("GEN_NUM_BATCH"))
    if os.getenv("GEN_TOP_K"):             opts["top_k"]             = int(os.getenv("GEN_TOP_K"))
    if os.getenv("GEN_TOP_P"):             opts["top_p"]             = float(os.getenv("GEN_TOP_P"))
    if os.getenv("GEN_REPEAT_PENALTY"):    opts["repeat_penalty"]    = float(os.getenv("GEN_REPEAT_PENALTY"))
    if os.getenv("GEN_PRESENCE_PENALTY"):  opts["presence_penalty"]  = float(os.getenv("GEN_PRESENCE_PENALTY"))
    if os.getenv("GEN_FREQUENCY_PENALTY"): opts["frequency_penalty"] = float(os.getenv("GEN_FREQUENCY_PENALTY"))
    if os.getenv("GEN_MIROSTAT"):          opts["mirostat"]          = int(os.getenv("GEN_MIROSTAT"))
    if os.getenv("GEN_MIROSTAT_TAU"):      opts["mirostat_tau"]      = float(os.getenv("GEN_MIROSTAT_TAU"))
    if os.getenv("GEN_MIROSTAT_ETA"):      opts["mirostat_eta"]      = float(os.getenv("GEN_MIROSTAT_ETA"))
    # Global clamps to avoid OOM (apply if provided; otherwise use safe defaults)
    try:
        max_ctx = int(os.getenv("GEN_MAX_CTX", "120000"))
        max_pred = int(os.getenv("GEN_MAX_PREDICT", "3200"))
        opts["num_ctx"] = min(opts.get("num_ctx", max_ctx), max_ctx)
        opts["num_predict"] = min(opts.get("num_predict", max_pred), max_pred)
    except Exception:
        pass

    # If using Docker service 'ollama', enforce conservative caps
    try:
        from urllib.parse import urlparse as _urlparse
        host = _urlparse(CURRENT_OLLAMA_URL).hostname or ""
        if host == "ollama":
            docker_ctx = int(os.getenv("GEN_DOCKER_CTX", "4096"))
            docker_pred = int(os.getenv("GEN_DOCKER_PREDICT", "2000"))
            opts["num_ctx"] = min(opts.get("num_ctx", docker_ctx), docker_ctx)
            opts["num_predict"] = min(opts.get("num_predict", docker_pred), docker_pred)
    except Exception:
        pass
    return opts


def ollama_complete(
    prompt: str,
    *,
    length: str = "medium",
    _model: Optional[str] = None,
    _used_fallback: bool = False,
    _options_override: Optional[dict] = None,
) -> str:
    """Call Ollama with bounded tokens, long timeout, and one retry if needed.
    Fallback to /api/chat if /api/generate is not available (older/newer builds).
    """
    if _options_override is not None:
        options = dict(_options_override)
    else:
        options = _gen_options_from_env(length)
    timeout_s = int(os.getenv("GEN_HTTP_TIMEOUT", "1200"))

    model_to_use = _model or GEN_MODEL

    def _post_generate(opts, model_name: str):
        payload = {"model": model_name, "prompt": prompt, "stream": False, "options": opts}
        r = requests.post(f"{CURRENT_OLLAMA_URL}/api/generate", json=payload, timeout=timeout_s)
        r.raise_for_status()
        return r.json().get("response", "")

    def _post_chat(opts, model_name: str):
        payload = {
            "model": model_to_use,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": opts,
        }
        r = requests.post(f"{CURRENT_OLLAMA_URL}/api/chat", json=payload, timeout=timeout_s)
        if r.status_code >= 400:
            try:
                err = r.json().get("error")
            except Exception:
                err = r.text
            raise requests.HTTPError(f"/api/chat error {r.status_code}: {err}", response=r)
        r.raise_for_status()
        data = r.json()
        # Newer chat API returns a single 'message'; older returns 'messages'
        if isinstance(data, dict) and data.get("message"):
            return data["message"].get("content", "")
        if isinstance(data, dict) and data.get("messages"):
            parts = [m.get("content", "") for m in data["messages"] if isinstance(m, dict)]
            return "\n".join([p for p in parts if p]).strip()
        return ""

    try:
        return _post_generate(options, model_to_use)
    except requests.HTTPError as e:
        # Retry once with smaller cap on generate
        status = getattr(e.response, "status_code", None)
        # Prepare a conservative retry
        smaller = max(300, int(options.get("num_predict", 900) * 0.5))
        options_retry = dict(options)
        options_retry["num_predict"] = int(os.getenv("GEN_NUM_PREDICT_RETRY", str(smaller)))
        # If memory error, also shrink context window
        try:
            err_body = e.response.json().get("error", "") if e.response is not None else ""
        except Exception:
            err_body = e.response.text if getattr(e, 'response', None) is not None else ""
        if status == 500 and ("more system memory" in str(err_body).lower() or "memory" in str(err_body).lower()):
            options_retry["num_ctx"] = min(int(os.getenv("GEN_NUM_CTX", options.get("num_ctx", 4096))), 2048)
        if status == 404:
            # Fallback to chat endpoint
            try:
                return _post_chat(options_retry, model_to_use)
            except requests.HTTPError as e2:
                if getattr(e2.response, "status_code", None) == 404:
                    raise RuntimeError(
                        f"Ollama endpoints not found at {CURRENT_OLLAMA_URL} (/api/generate and /api/chat).\n"
                        "Start Ollama (ollama serve) or run Docker (make up).\n"
                        f"Then pull a model, e.g.: 'ollama pull {GEN_MODEL}'."
                    ) from e2
                raise
        # If memory error and fallback is available and not yet used, try fallback model with conservative options
        try:
            err_body = e.response.json().get("error", "") if e.response is not None else ""
        except Exception:
            err_body = e.response.text if getattr(e, 'response', None) is not None else ""
        if (status == 500 and ("more system memory" in str(err_body).lower() or "memory" in str(err_body).lower())
            and GEN_MODEL_FALLBACK and not _used_fallback):
            # Try fallback model
            fb_opts = dict(options)
            fb_opts["num_ctx"] = min(int(os.getenv("GEN_NUM_CTX", options.get("num_ctx", 4096))), 1024)
            fb_opts["num_predict"] = min(int(os.getenv("GEN_NUM_PREDICT", options.get("num_predict", 900))), 450)
            try:
                return ollama_complete(
                    prompt,
                    length=length,
                    _model=GEN_MODEL_FALLBACK,
                    _used_fallback=True,
                    _options_override=fb_opts,
                )
            except Exception:
                pass

        # Non-404: try generate again with smaller cap on the same model
        r2 = requests.post(
            f"{CURRENT_OLLAMA_URL}/api/generate",
            json={"model": model_to_use, "prompt": prompt, "stream": False, "options": options_retry},
            timeout=timeout_s,
        )
        if r2.status_code >= 400:
            try:
                err = r2.json().get("error")
            except Exception:
                err = r2.text
            raise RuntimeError(f"/api/generate error {r2.status_code}: {err}")
        r2.raise_for_status()
        return r2.json().get("response", "")
    except requests.Timeout:
        # Final fallback to chat with smaller cap
        smaller = max(400, int(options.get("num_predict", 900) * 0.6))
        options_retry = dict(options)
        options_retry["num_predict"] = int(os.getenv("GEN_NUM_PREDICT_RETRY", str(smaller)))
        return _post_chat(options_retry, model_to_use)

def _assert_ollama_up():
    global CURRENT_OLLAMA_URL

    def is_version_ok(base: str) -> bool:
        try:
            r = requests.get(f"{base}/api/version", timeout=3)
            r.raise_for_status()
            return True
        except Exception:
            return False

    # Candidate list: current URL, Docker service, host.docker.internal, then a small local port scan (11434-11444)
    bases = [CURRENT_OLLAMA_URL, "http://ollama:11434", "http://host.docker.internal:11434"]
    for host in ("localhost", "127.0.0.1"):
        for port in range(11434, 11445):
            bases.append(f"http://{host}:{port}")
    # Deduplicate while preserving order
    seen = set(); candidates = []
    for b in bases:
        if b not in seen and b:
            candidates.append(b); seen.add(b)

    for base in candidates:
        if is_version_ok(base):
            CURRENT_OLLAMA_URL = base
            os.environ["OLLAMA_URL"] = base
            print(f"Using Ollama at {CURRENT_OLLAMA_URL}")
            return

    raise RuntimeError(
        "Cannot reach Ollama endpoints (/api/generate or /api/chat). Tried: " + ", ".join(candidates) + ".\n"
        "Start Ollama (ollama serve) or run Docker (make up).\n"
        "If Ollama runs on a custom port, set OLLAMA_URL in .env (e.g., http://localhost:11435)."
    )

def _assert_model_available():
    """Ensure a compatible model tag exists; if the exact tag is missing but another tag
    for the same base model is present (e.g., 'phi3:mini-128k' vs 'phi3:mini'),
    transparently switch to the installed tag to avoid hard failures.
    """
    global CURRENT_OLLAMA_URL, GEN_MODEL
    try:
        r = requests.get(f"{CURRENT_OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
        data = r.json()
        names = []
        if isinstance(data, dict) and isinstance(data.get("models"), list):
            for m in data["models"]:
                n = m.get("name") if isinstance(m, dict) else None
                if n:
                    names.append(n)
        # If candidates list is provided, prefer those
        raw_candidates = os.getenv("GEN_MODEL_CANDIDATES", "").strip()
        candidates = [c.strip() for c in raw_candidates.split(",") if c.strip()] if raw_candidates else []
        if candidates:
            for cand in candidates:
                if cand in names:
                    os.environ["GEN_MODEL"] = cand
                    globals()["GEN_MODEL"] = cand
                    print(f"[info] Using GEN_MODEL candidate '{cand}'", flush=True)
                    return
            # Base-name match from candidates
            candidate_bases = [c.split(":")[0].strip().lower() for c in candidates]
            for n in names:
                base_n = n.split(":")[0].strip().lower()
                if base_n in candidate_bases:
                    os.environ["GEN_MODEL"] = n
                    globals()["GEN_MODEL"] = n
                    print(f"[info] Switched GEN_MODEL to installed tag '{n}' via candidates", flush=True)
                    return
        if GEN_MODEL in names:
            return
        # Try a base-name match (e.g., 'llama3.2' matches 'llama3.2:3b ')
        base = GEN_MODEL.split(":")[0].strip().lower()
        if base:
            for n in names:
                if isinstance(n, str) and n.split(":")[0].strip().lower() == base:
                    os.environ["GEN_MODEL"] = n
                    globals()["GEN_MODEL"] = n
                    print(f"[info] Switched GEN_MODEL to installed tag '{n}' (was '{base}')", flush=True)
                    return
        msg = (
            "Model not available on Ollama server.\n"
            f"Requested GEN_MODEL='{GEN_MODEL}'. Installed: {names or '[]'}.\n"
            "Fix: pull the model (e.g., 'ollama pull GEN_MODEL'), set GEN_MODEL to an installed name, or provide GEN_MODEL_CANDIDATES with a comma-separated list."
        )
        raise RuntimeError(msg)
    except requests.HTTPError as e:
        raise RuntimeError("Failed to query Ollama /api/tags for installed models.") from e


def load_prompt(system_path, user_path, **vars):
    with open(system_path, "r", encoding="utf-8") as f:
        system = f.read()
    with open(user_path, "r", encoding="utf-8") as f:
        user = f.read().format(**vars)
    return f"{system}\n\n{user}"

def _load_style_text(brief: dict) -> str:
    # Env overrides: text wins over profile
    env_style_text = os.getenv("GEN_STYLE_TEXT")
    if isinstance(env_style_text, str) and env_style_text.strip():
        return env_style_text.strip()
    env_style_profile = os.getenv("GEN_STYLE_PROFILE")
    if isinstance(env_style_profile, str) and env_style_profile.strip():
        prof_name = env_style_profile.strip()
        import glob as _glob
        matches = _glob.glob(os.path.join("engine", "styles", "**", f"{prof_name}.md"), recursive=True)
        if matches:
            with open(matches[0], "r", encoding="utf-8") as f:
                return f.read().strip()
    # order of precedence: brief.style (inline) > style_profile file > empty
    if isinstance(brief.get("style"), str) and brief["style"].strip():
        return brief["style"].strip()
    prof = brief.get("style_profile")
    if isinstance(prof, str) and prof:
        import glob as _glob
        matches = _glob.glob(os.path.join("engine", "styles", "**", f"{prof}.md"), recursive=True)
        if matches:
            with open(matches[0], "r", encoding="utf-8") as f:
                return f.read().strip()
    return ""

def _allowed_domains_from_brief(brief: dict) -> str:
    try:
        allow = brief.get("sources", {}).get("allow", [])
        if not isinstance(allow, list):
            return ""
        seen = set(); out = []
        for d in allow:
            if not isinstance(d, str):
                continue
            dd = d.strip().lower()
            if dd and dd not in seen:
                out.append(dd); seen.add(dd)
        return ", ".join(out)
    except Exception:
        return ""

def _gather_paths_from_patterns(patterns):
    paths = []
    if not patterns:
        return paths
    import glob as _glob
    for p in (patterns if isinstance(patterns, list) else [patterns]):
        if not isinstance(p, str) or not p.strip():
            continue
        matches = sorted(_glob.glob(p, recursive=True))
        if matches:
            paths.extend(matches)
        elif os.path.exists(p):
            paths.append(p)
    # De-duplicate while preserving order
    seen = set()
    out = []
    for p in paths:
        if p not in seen:
            out.append(p); seen.add(p)
    return out

def _load_style_examples_text(brief: dict, *, per_file_max=1200, total_max=2400) -> str:
    examples = brief.get("style_examples")
    if not examples:
        return ""
    texts = []
    for fp in _gather_paths_from_patterns(examples):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                t = f.read().strip()
        except UnicodeDecodeError:
            try:
                with open(fp, "r", encoding="latin-1", errors="ignore") as f:
                    t = f.read().strip()
            except Exception:
                continue
        if not t:
            continue
        if len(t) > per_file_max:
            t = t[:per_file_max]
        texts.append(f"--- {os.path.basename(fp)} ---\n{t}")
        if sum(len(x) for x in texts) >= total_max:
            break
    joined = "\n\n".join(texts)
    if len(joined) > total_max:
        return joined[:total_max]
    return joined

_CTX_STRIP_PATTERNS = [
    re.compile(r"^\s*(system|assistant|user)\s*:", re.I),
    re.compile(r"^\s*(task|instruction)s?\s*:", re.I),
    re.compile(r"^<?\s*(system|assistant|user)\s*>?$", re.I),
    re.compile(r"^\s*```"),
]

def _sanitize_context(ctx: str, *, max_chars: int = 12000) -> str:
    """Strip obvious prompt-injection markers from retrieved text before inserting into prompts."""
    if not ctx:
        return ""
    lines = []
    for ln in ctx.splitlines():
        s = ln.rstrip()
        if any(p.search(s) for p in _CTX_STRIP_PATTERNS):
            continue
        lines.append(s)
    safe = "\n".join(lines).strip()
    if len(safe) > max_chars:
        safe = safe[:max_chars]
    return safe

def _hashtags_from_tags(tags, max_n=6):
    if not tags: return ""
    cleaned = []
    for t in tags:
        t = re.sub(r"[^A-Za-z0-9_ ]+", "", str(t)).strip().replace(" ", "")
        if t:
            cleaned.append("#" + t[:40])
        if len(cleaned) >= max_n:
            break
    return " ".join(cleaned)

# Broader meta/preamble detector to block conversational or assistant-like scaffolding
_META_PAT = re.compile(
    r"^(Document:|Your task:|I\'m sorry|In a hypothet|It appears you(\'|')ve provided|It appears you have provided|I\'ll|Let me|Here is( the)?|Note:)",
    re.I | re.M,
)
_BAD_VENDOR_PAT = re.compile(r"(ShieldGemma|Command\-R7|Weaviate|Docusaurus|LangChain|Cross Encoder|MDX|React)", re.I)

# Per-run topic constraints (populated in main from brief)
_LINT_INCLUDE_TERMS: list[str] = []
# Per-run min lengths per H2 (overridable from brief)
_MIN_LEN_DEFAULTS = {
    "Overview": 180,
    "Why It Matters": 160,
    "Prerequisites": 140,
    "Steps": 200,
    "Examples": 140,
    "FAQs": 120,
    "References": 10,
}
_MIN_LEN = dict(_MIN_LEN_DEFAULTS)
# Per-run section logs for transparency
SECTION_LOGS = []

def _lint_section_text(name: str, body: str) -> tuple[bool, list[str]]:
    errs: list[str] = []
    t = (body or "").strip()
    if not t:
        return False, ["empty"]
    if _META_PAT.search(t):
        errs.append("meta_artifacts")
    if _BAD_VENDOR_PAT.search(t):
        errs.append("vendor_blurb")
    # Discourage conversational tone (first/second person) unless explicitly disabled
    try:
        if (os.getenv("LINT_BAN_CONVERSATIONAL", "1").lower() in ("1", "true", "yes")):
            if re.search(r"\b(I|we|let's|let\s+us|you|your|you're|i'm|we're)\b", t, flags=re.I):
                errs.append("conversational_tone")
    except Exception:
        pass
    # Require at least one topic keyword if provided
    if _LINT_INCLUDE_TERMS:
        if not any(kw.lower() in t.lower() for kw in _LINT_INCLUDE_TERMS):
            errs.append("missing_topic_terms")
    # Ban nested headings inside body (section bodies should not contain '#')
    for ln in t.splitlines():
        if ln.strip().startswith('#'):
            errs.append("nested_heading")
            break
    # Minimum lengths by section (characters)
    need = _MIN_LEN.get(name, 140)
    if len(t) < max(need, 100):
        errs.append("too_short")
    return (len(errs) == 0), errs

def _synthesize_section(title: str, section: str) -> str:
    # Deterministic, professional fallback content without LLM
    if section == "Overview":
        return (
            f"{title} keeps release notes, support answers, and marketing copy in sync without adding extra headcount.\n"
            "- Treat content like code: brief, branch, review, and ship.\n"
            "- Lean on first-party notes so retrieval never surfaces vendor fluff.\n"
            "- Automate guardrails so reviewers fix substance, not formatting."
        )
    if section == "Why It Matters":
        return (
            "- Fewer rewrites when every draft honors the same structure and tone.\n"
            "- Lower legal and brand risk by blocking disallowed links before publish.\n"
            "- Faster handoffs across teams because context and style live in the repo."
        )
    if section == "Prerequisites":
        return (
            "- Git repo with briefs in `briefs/` and canonical notes under `content/`.\n"
            "- Style profile (`engine/styles/*.md`) that spells out voice, hooks, and CTAs.\n"
            "- Local vector index (Chroma or Qdrant) rebuilt after every content edit.\n"
            "- Optional: WordPress credentials in `.env` for draft publishing."
        )
    if section == "Steps":
        return (
            "- Define your guardrails: allowed domains, H2 schema, personas.\n"
            "- Capture source notes and regenerate embeddings (`make index-local`).\n"
            "- Run the brief with SKIP_PUBLISH=1, inspect artifacts, and log decisions.\n"
            "- Publish once duplicate checks, lint, and references all pass."
        )
    if section == "Examples":
        return (
            "- Guardrail report showing blocked references and duplicate scores.\n"
            "- Section quality log with attempts, retries, and fallback mode.\n"
            "- Social snippet generated from the same brief with style tokens applied."
        )
    if section == "FAQs":
        return (
            "- How do we keep drafts on-topic? Bias retrieval to `content/` and cap per-source hits.\n"
            "- What if the model drifts? Regenerate the section with `make regen-section` and compare.\n"
            "- How do we adopt this across teams? Treat briefs like tickets and review in pull requests."
        )
    if section == "References":
        return (
            "- Internal notes: `content/` markdown tied to this brief.\n"
            "- Workflow guardrails: see `meta/section_quality.json` in the generated artifacts."
        )
    return ""

def _replace_section_in_md(md_text: str, section: str, new_body: str) -> str:
    lines = md_text.splitlines()
    out = []
    i = 0
    found = False
    hdr = f"## {section}"
    while i < len(lines):
        ln = lines[i]
        if not found and ln.strip() == hdr:
            found = True
            out.append(ln)
            out.append(new_body.strip())
            out.append("")
            # skip until next H2 or end
            i += 1
            while i < len(lines) and not lines[i].startswith("## "):
                i += 1
            continue
        out.append(ln)
        i += 1
    if not found:
        # append at end
        if not out or out[-1].strip() != hdr:
            out.append(hdr)
        out.append(new_body.strip())
        out.append("")
    return "\n".join(out).strip() + "\n"

def _lint_social(text: str, *, platform: str = "linkedin") -> tuple[bool, list[str]]:
    errs: list[str] = []
    t = (text or "").strip()
    if not t:
        errs.append("empty")
        return False, errs
    # meta artifacts and raw urls
    if re.search(r"^(Document:|Your task:|I\'m sorry|In a hypothet)", t, flags=re.I | re.M):
        errs.append("meta_artifacts")
    if re.search(r"https?://", t):
        errs.append("raw_urls")
    # paragraphs count
    paras = [p for p in re.split(r"\n\s*\n", t) if p.strip()]
    if not (1 <= len(paras) <= 3):
        errs.append("paragraph_count")
    # hook line length
    first = next((ln for ln in t.splitlines() if ln.strip()), "")
    if len(first) > 120:
        errs.append("hook_too_long")
    # require bold hook for LinkedIn
    if platform == "linkedin":
        s = first.strip()
        if not (s.startswith("**") and s.endswith("**")):
            errs.append("missing_bold_hook")
    # minimal length
    min_len = 80 if platform == "linkedin" else 60
    if len(t) < min_len:
        errs.append("too_short")
    # ensure hashtags presence in the tail
    tail = "\n".join(t.splitlines()[-2:])
    if "#" not in tail:
        errs.append("no_hashtags")
    return (len(errs) == 0), errs

def _strip_meta_artifacts(md: str) -> str:
    """Remove common meta artifacts and nonsense blocks the model might emit."""
    bad_patterns = [
        r"^\s*Document:\s*.*$",
        r"^\s*Your task:\s*.*$",
        r"^\s*In a hypothet.*$",
        r"^\s*I\'m sorry.*$",
        r"^\s*It appears you(\'|')ve provided.*$",
        r"^\s*It appears you have provided.*$",
        r"^\s*I\'ll\s+.*$",
        r"^\s*Let me\s+.*$",
        r"^\s*Here is( the)?\s+.*$",
        r"^\s*Note:\s+.*$",
        r"^\s*Output Format Guidelines\s*$\n.*?(?=^##\s|\Z)",
        r"^\s*Examples\s*$\n.*?(?=^##\s|\Z)",  # stray Examples blocks with junk
    ]
    out = md
    for pat in bad_patterns:
        out = re.sub(pat, "", out, flags=re.I | re.M | re.S)
    # Collapse extra blank lines introduced by removals
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out

def _enforce_char_limit(txt: str, limit: int) -> str:
    if txt is None:
        return ""
    t = txt.strip()
    if len(t) <= limit:
        return t
    # Try to preserve whole lines first
    lines = t.splitlines()
    out = []
    total = 0
    for ln in lines:
        if total + len(ln) + 1 > limit - 1:
            break
        out.append(ln)
        total += len(ln) + 1
    if not out:
        return (t[: max(0, limit - 1)] + "\u2026")
    joined = "\n".join(out).rstrip()
    if len(joined) < limit - 1:
        return joined
    return joined[: limit - 1] + "\u2026"

def _per_section_lengths(overall: str):
    o = (overall or "medium").lower()
    # Map overall length to per-section guidance
    if o == "long":
        return {
            "Overview": "short",
            "Why It Matters": "short",
            "Prerequisites": "short",
            "Steps": "medium",
            "Examples": "medium",
            "FAQs": "short",
            "References": "short",
        }
    else:  # short/medium
        return {
            "Overview": "short",
            "Why It Matters": "short",
            "Prerequisites": "short",
            "Steps": "short",
            "Examples": "short",
            "FAQs": "short",
            "References": "short",
        }

def _controls_from_brief(brief: dict) -> str:
    tokens = []
    p = str(brief.get("persona", "")).strip().lower()
    # Allow runtime override via env for quick experiments
    p = os.getenv("GEN_PERSONA", p)
    if p:
        tokens.append(f"[persona={p}]")
    return " ".join(tokens)


def _must_terms_line(brief: dict) -> str:
    terms: list[str] = []
    raw = brief.get("must_include_terms")
    if isinstance(raw, list):
        for t in raw:
            s = str(t).strip()
            if s:
                terms.append(s)
    if terms:
        unique = list(dict.fromkeys(terms))
        return "- Include each of these terms at least once: " + ", ".join(unique) + "."
    return ""


def _generate_section(title: str, section: str, brief: dict, style_text: str) -> str:
    # Retrieve context tailored to the section
    k = int(os.getenv("RETRIEVE_K", "8"))
    section_hints = {
        "Overview": "summary, definition, context",
        "Why It Matters": "benefits, impact, outcomes",
        "Prerequisites": "requirements, setup, tools",
        "Steps": "step-by-step, checklist, instructions",
        "Examples": "examples, snippets, use cases",
        "FAQs": "frequently asked questions, pitfalls",
        "References": "sources, links, further reading",
    }
    hint = section_hints.get(section, "")
    q = f"{title} {section} {hint} {brief.get('tags','')}"
    sub_context, _ = retrieve(q, k=k)
    sub_context = _sanitize_context(sub_context)

    # Pick length hint per section
    lengths = _per_section_lengths(brief.get("length", "medium"))
    sec_len = lengths.get(section, "short")

    prompt = load_prompt(
        "engine/prompts/post_system.txt",
        "engine/prompts/section_user.txt",
        title=title,
        section=section,
        audience=brief.get("audience", "general"),
        goal=brief.get("goal", "inform"),
        tone=brief.get("tone", "direct"),
        length=sec_len,
        style=style_text,
        style_examples=_load_style_examples_text(brief),
        context=sub_context,
        allowed_domains=_allowed_domains_from_brief(brief),
        no_external=str(bool(brief.get("no_external", False))),
        controls=_controls_from_brief(brief),
        must_terms_line=_must_terms_line(brief),
    )
    # Enforce lint + retry, then deterministic fallback; log reasons
    attempts = 0
    best = ""
    last_errs: list[str] = []
    while attempts < 3:
        out = ollama_complete(prompt, length=sec_len).strip()
        out = _strip_meta_artifacts(out)
        ok, errs = _lint_section_text(section, out)
        if ok:
            SECTION_LOGS.append({"section": section, "ok": True, "attempts": attempts + 1, "errs": []})
            return out
        last_errs = errs
        if len(out) > len(best):
            best = out
        attempts += 1
    # fallback: prefer deterministic synthesis unless the only failure was length
    synthesized = _synthesize_section(title, section)
    allow_best = bool(best) and (not last_errs or set(last_errs).issubset({"too_short"}))
    fb = best if allow_best else (synthesized or best or "")
    SECTION_LOGS.append({
        "section": section,
        "ok": False,
        "attempts": attempts,
        "errs": last_errs,
        "used_fallback": True,
        "fallback_mode": "best" if allow_best else "synthetic",
    })
    return fb

def _generate_fnf_section(title: str, layer: str, brief: dict, style_text: str):
    # Tailored retrieval per layer to keep context focused
    k = int(os.getenv("RETRIEVE_K", "8"))
    layer_hints = {
        "Friction": "pain points, blockers, confusion",
        "Bridge": "analogy, metaphor, everyday examples",
        "Evidence": "case study, metrics, sources, dates",
        "Implication": "roles Exec PM Writer Ops, why it matters",
        "Action": "checklist, steps, <=60 minutes",
        "Look Ahead": "risks, tradeoffs, second-order effects",
        "Reflection": "poetic reflection, time, symmetry, craft",
    }
    hint = layer_hints.get(layer, "")
    q = f"{title} {layer} {hint} {brief.get('tags','')}"
    sub_context, _ = retrieve(q, k=k)
    sub_context = _sanitize_context(sub_context)

    # Use short/medium lengths; Reflection can be short
    lengths = _per_section_lengths(brief.get("length", "medium"))
    sec_len = lengths.get(layer, "short")

    prompt = load_prompt(
        "engine/prompts/post_system.txt",
        "engine/prompts/fnf_section_user.txt",
        title=title,
        layer=layer,
        audience=brief.get("audience", "general"),
        tone=brief.get("tone", "direct"),
        style=style_text,
        style_examples=_load_style_examples_text(brief),
        context=sub_context,
        allowed_domains=_allowed_domains_from_brief(brief),
        no_external=str(bool(brief.get("no_external", False))),
        controls=_controls_from_brief(brief),
        must_terms_line=_must_terms_line(brief),
    )
    out = ollama_complete(prompt, length=sec_len).strip()
    # Parse strict JSON
    heading = body = None
    try:
        data = json.loads(out)
        heading = data.get("heading") if isinstance(data, dict) else None
        body = data.get("body") if isinstance(data, dict) else None
    except Exception:
        pass
    # Robust extraction if strict parse failed
    if not (isinstance(heading, str) and isinstance(body, str)):
        # remove code fences and wrappers
        cleaned = _re.sub(r"```[\s\S]*?```", "", out)
        cleaned = cleaned.replace("Here is the output in JSON format:", "").replace("Here is a JSON representation of the content you provided", "").strip()
        m = _re.search(r"\{[\s\S]*\}", cleaned)
        if m:
            try:
                data = json.loads(m.group(0))
                h2 = data.get("heading"); b2 = data.get("body")
                if isinstance(h2, str) and isinstance(b2, str):
                    heading, body = h2.strip(), b2.strip()
            except Exception:
                pass
    # Last resort: derive heading/body from plain text
    if not (isinstance(heading, str) and isinstance(body, str)):
        lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
        if lines:
            heading = lines[0][:80] if len(lines[0]) > 3 else f"{layer}"
            body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        else:
            heading, body = f"{layer}", ""
    body = _strip_meta_artifacts(body or "")
    return heading, body


def extract_references(md: str):
    urls = re.findall(r"https?://[^\s\)\]]+", md)
    refs_idx = md.lower().find("\n## references")
    if refs_idx != -1:
        refs_md = md[refs_idx:]
        urls = re.findall(r"https?://[^\s\)\]]+", refs_md)
    return urls

def _normalize_domains_list(domains: list[str]) -> list[str]:
    if not isinstance(domains, list):
        return []
    out = []
    for d in domains:
        norm = normalize_domain(str(d))
        if norm:
            out.append(norm)
    return list(dict.fromkeys(out))

def _sanitize_references(md: str, allowed_domains: list[str], *, no_external: bool) -> tuple[str, list[str], list[str]]:
    """Enforce allowlist by removing disallowed URLs and rebuilding References section.
    If no_external=True, remove all URLs and ensure a References H2 stub exists.
    Returns: (sanitized_text, kept_urls, found_urls)
    """
    text = md
    # Normalize URLs: strip trailing punctuation and angle brackets
    def _normalize_url(u: str) -> str:
        uu = u.strip()
        # Drop trailing >, ), ], commas or periods
        while uu and uu[-1] in (">", ")", "]", ",", "."):
            uu = uu[:-1]
        return uu

    urls_all = [ _normalize_url(u) for u in re.findall(r"https?://[^\s\)\]]+", text) ]
    allowed_set = {d for d in _normalize_domains_list(allowed_domains)}
    allow_all = len(allowed_set) == 0
    keep_urls = []
    removed_urls = []
    if no_external:
        # Remove all URLs
        for u in urls_all:
            text = text.replace(u, "")
            removed_urls.append(u)
    else:
        for u in urls_all:
            try:
                host = urlparse(u).netloc
                d = domain(host)
            except Exception:
                d = ""
            if allow_all or d in allowed_set:
                keep_urls.append(_normalize_url(u))
            else:
                text = text.replace(u, "")
                removed_urls.append(u)

    # Build References section
    refs_lines = ["## References", ""]
    if no_external:
        refs_lines.append("No external references available.")
    else:
        # Dedup preserve order
        seen = set()
        for u in keep_urls:
            if u not in seen:
                refs_lines.append(f"- {u}")
                seen.add(u)
        if len(seen) == 0:
            refs_lines.append("No external references available.")
    new_refs = "\n".join(refs_lines).strip() + "\n"

    # Replace existing References section if present; else append
    m = re.search(r"\n##\s*references\b.*", text, flags=re.I | re.S)
    if m:
        start = m.start()
        # slice before refs, add two newlines, then new refs
        text = text[:start].rstrip() + "\n\n" + new_refs
    else:
        text = text.rstrip() + "\n\n" + new_refs
    return text, keep_urls, urls_all

def _audit_references(no_external: bool, found_urls: list[str], kept_urls: list[str]) -> dict | None:
    """Return failure payload if references are insufficient given policy."""
    if no_external:
        return None
    if not found_urls:
        return {"reason": "audit_failed_references", "detail": "no_urls_found"}
    if not kept_urls:
        return {"reason": "audit_failed_references", "detail": "all_urls_filtered"}
    return None

def _dedupe_paragraphs(md: str, *, min_len: int = 60) -> str:
    """Remove repeated paragraphs to avoid duplicated content across sections.
    Keeps first occurrence; paragraphs shorter than min_len are ignored for dedupe.
    """
    paras = re.split(r"\n\s*\n", md.strip())
    seen = set()
    out = []
    for p in paras:
        norm = re.sub(r"\s+", " ", p.strip()).lower()
        # Only dedupe reasonably long blocks
        key = norm if len(norm) >= min_len else None
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        out.append(p.strip())
    return "\n\n".join(out).strip() + "\n"


def normalize_domain(value: str) -> str:
    """Return a lowercase host without scheme, port, or leading www."""
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    probe = raw if "://" in raw else f"http://{raw}"
    parsed = urlparse(probe)
    host = parsed.netloc or parsed.path or ""
    # Drop credentials and port if present
    host = host.split("@").pop()
    host = host.split(":")[0]
    host = host.strip(".")
    if host.startswith("www."):
        host = host[4:]
    return host


def domain(host: str):
    return normalize_domain(host)


def parse_domains(urls):
    ds = []
    for u in urls:
        try:
            d = domain(urlparse(u).netloc)
            if d:
                ds.append(d)
        except Exception:
            continue
    return list(dict.fromkeys(ds))


def cosine(a, b):
    a = np.asarray(a); b = np.asarray(b)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom else 0.0


def load_recent_history(n=50):
    if not os.path.exists(HIST_PATH):
        return []
    items = []
    with open(HIST_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return items[-n:]


def append_history(record):
    ensure_dir(HIST_DIR)
    with open(HIST_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def first_sentences(text: str, max_chars: int = 400):
    parts = re.split(r"(?<=[\.!?])\s+", text.strip())
    out = ""
    for p in parts:
        if not p: continue
        if len(out) + len(p) + 1 > max_chars: break
        out = (out + " " + p).strip()
        if out.count(".") >= 2: break
    return out if out else text[:max_chars]


def generate_social(brief, draft_md, out_path, run_suffix: str):
    title = brief.get("title", "")
    tags = brief.get("tags", [])
    md_no_h1 = re.sub(r"^# .*\n", "", draft_md).strip()
    summary = first_sentences(md_no_h1, 480)
    hashtags = " ".join("#" + t.replace(" ", "") for t in tags[:6])

    linkedin = f"""{title}

{summary}

{hashtags}"""
    x_body = (title + " - " + first_sentences(md_no_h1, 180)).strip()
    x_post = (x_body + " " + hashtags).strip()
    if len(x_post) > 280:
        x_post = x_post[:277] + "..."

    version_path = os.path.join(os.path.dirname(out_path), f"social_{run_suffix}.md")
    for target in (version_path, out_path):
        with open(target, "w", encoding="utf-8") as f:
            f.write("# Social Snippets\n\n")
            f.write("## LinkedIn\n\n")
            f.write(linkedin + "\n\n")
            f.write("## X/Twitter\n\n")
            f.write(x_post + "\n")

def _write_preview_index(artifacts_dir: str, slug: str, basename: str):
    blog_dir = os.path.join(artifacts_dir, "blog")
    blog_html = os.path.join(blog_dir, f"{basename}.html")
    blog_md   = os.path.join(blog_dir, f"{basename}.md")
    latest_md = os.path.join(blog_dir, "latest.md")
    legacy_md = os.path.join(blog_dir, "draft.md")
    if not os.path.exists(blog_md):
        for candidate in (latest_md, legacy_md):
            if os.path.exists(candidate):
                blog_md = candidate
                break
    latest_html = os.path.join(blog_dir, "latest.html")
    legacy_html = os.path.join(blog_dir, "draft.html")
    if not os.path.exists(blog_html):
        for candidate in (latest_html, legacy_html):
            if os.path.exists(candidate):
                blog_html = candidate
                break
    li_md     = os.path.join(artifacts_dir, "social", "linkedin.md")
    ig_md     = os.path.join(artifacts_dir, "social", "instagram.md")
    gh_md     = os.path.join(artifacts_dir, "github", "README.md")
    meta_dir  = os.path.join(artifacts_dir, "meta")

    def rel(p):
        return os.path.relpath(p, start=artifacts_dir)

    links = []
    if os.path.exists(blog_html): links.append(("Blog (HTML)", rel(blog_html)))
    if os.path.exists(blog_md):   links.append(("Blog (Markdown)", rel(blog_md)))

    # Include previous versions
    prevs = []
    blog_dir = os.path.join(artifacts_dir, "blog")
    if os.path.isdir(blog_dir):
        for fn in sorted(os.listdir(blog_dir)):
            if (fn.startswith(f"{basename}_") or fn.startswith("draft_")) and (fn.endswith(".html") or fn.endswith(".md")):
                prevs.append(os.path.join("blog", fn))
    if os.path.exists(li_md):     links.append(("LinkedIn", rel(li_md)))
    if os.path.exists(ig_md):     links.append(("Instagram", rel(ig_md)))
    if os.path.exists(gh_md):     links.append(("GitHub README", rel(gh_md)))

    meta_files = []
    if os.path.isdir(meta_dir):
        for fn in sorted(os.listdir(meta_dir)):
            meta_files.append(os.path.join("meta", fn))

    html_lines = [
        "<!doctype html>",
        "<meta charset='utf-8'>",
        f"<title>Artifacts - {slug}</title>",
        "<style>body{font-family: -apple-system, system-ui, sans-serif; padding:24px; max-width: 860px; margin:auto} code, pre{background:#f7f7f7; padding:8px; display:block; white-space:pre-wrap}</style>",
        f"<h1>Artifacts - {slug}</h1>",
        "<h2>Links</h2>",
        "<ul>",
    ]
    for label, href in links:
        html_lines.append(f"  <li><a href='{href}' target='_blank' rel='noopener'>{label}</a></li>")
    html_lines.append("</ul>")

    if prevs:
        html_lines.append("<h2>Previous Versions</h2>")
        html_lines.append("<ul>")
        for p in prevs:
            html_lines.append(f"  <li><a href='{p}' target='_blank' rel='noopener'>{p}</a></li>")
        html_lines.append("</ul>")

    # Try to read persona from blog frontmatter
    persona_val = None
    try:
        if os.path.exists(blog_md):
            with open(blog_md, "r", encoding="utf-8") as _bf:
                _raw = _bf.read()
            _post = frontmatter.loads(_raw)
            pv = _post.get("persona")
            if isinstance(pv, str) and pv.strip():
                persona_val = pv.strip()
    except Exception:
        pass

    if os.path.exists(li_md):
        try:
            with open(li_md, "r", encoding="utf-8") as f:
                li_txt = f.read()
            html_lines.append("<h2>LinkedIn Preview</h2>")
            if persona_val:
                html_lines.append(f"<div style='margin-bottom:8px'><small><strong>Persona:</strong> {persona_val}</small></div>")
            html_lines.append("<pre>" + li_txt.replace("<", "&lt;") + "</pre>")
        except Exception:
            pass
    if os.path.exists(ig_md):
        try:
            with open(ig_md, "r", encoding="utf-8") as f:
                ig_txt = f.read()
            html_lines.append("<h2>Instagram Preview</h2>")
            if persona_val:
                html_lines.append(f"<div style='margin-bottom:8px'><small><strong>Persona:</strong> {persona_val}</small></div>")
            html_lines.append("<pre>" + ig_txt.replace("<", "&lt;") + "</pre>")
        except Exception:
            pass

    if meta_files:
        html_lines.append("<h2>Meta</h2>")
        html_lines.append("<ul>")
        for mf in meta_files:
            html_lines.append(f"  <li><a href='{mf}' target='_blank' rel='noopener'>{mf}</a></li>")
        html_lines.append("</ul>")

    html = "\n".join(html_lines)
    with open(os.path.join(artifacts_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

def _gen_linkedin(brief, context: str, style_text: str, artifacts_dir: str, run_suffix: str):
    hashtags = _hashtags_from_tags(brief.get("tags", []), max_n=6)
    def _tone_for_persona(default_tone: str) -> str:
        p = (brief.get("persona") or os.getenv("GEN_PERSONA") or "").strip().lower()
        if not p:
            return default_tone
        mapping = {
            "founder": "direct, punchy, outcome-first",
            "pm": "balanced, trade-offs, rollout-focused",
            "content": "editorial, scannable, reader-first",
            "sme": "precise, technical, concise"
        }
        addon = mapping.get(p)
        if addon and addon.lower() not in (default_tone or "").lower():
            return f"{default_tone}, {addon}" if default_tone else addon
        return default_tone
    tone_val = _tone_for_persona(brief.get("tone", "direct"))
    prompt = load_prompt(
        "engine/prompts/post_system.txt",
        "engine/prompts/linkedin_user.txt",
        title=brief.get("title", ""),
        audience=brief.get("audience", "general"),
        goal=brief.get("goal", "inform"),
        tone=tone_val,
        style=style_text,
        style_examples=_load_style_examples_text(brief),
        context=context,
        hashtags=hashtags,
        allowed_domains=_allowed_domains_from_brief(brief),
        no_external=str(bool(brief.get("no_external", False))),
        controls=_controls_from_brief(brief),
        must_terms_line=_must_terms_line(brief),
    )
    attempts = 0
    body = ""
    last_errs: list[str] = []
    while attempts < 2:
        body_raw = ollama_complete(prompt, length="short").strip()
        body = _strip_meta_artifacts(body_raw)
        ok, errs = _lint_social(body, platform="linkedin")
        if ok:
            break
        last_errs = errs
        attempts += 1
    if attempts >= 2:
        # Fallback snippet
        title = brief.get("title", "")
        body = (
            f"**{title} - why it matters**\n\n"
            "-> Clear rules + lightweight AI keep your docs accurate, on-brand, and fast to ship.\n\n"
            "Next: define your style profile and allowed domains; run a deterministic draft; review; publish."
        )
    enforce = os.getenv("SOCIAL_ENFORCE", "0").lower() in ("1", "true", "yes")
    ok_final, errs_final = _lint_social(body, platform="linkedin")
    # Write meta quality log
    try:
        meta_dir = os.path.join(artifacts_dir, "meta"); ensure_dir(meta_dir)
        with open(os.path.join(meta_dir, "social_quality.json"), "a", encoding="utf-8") as f:
            json.dump({"platform": "linkedin", "attempts": attempts, "ok": ok_final, "errs": errs_final or last_errs}, f); f.write("\n")
    except Exception:
        pass
    if enforce and not ok_final:
        # Do not write file if enforcement is on and snippet still weak
        return
    body = linkedin_format(body, hashtags, limit=3000)
    body = _enforce_char_limit(body, 3000)
    social_dir = os.path.join(artifacts_dir, "social"); ensure_dir(social_dir)
    li_latest = os.path.join(social_dir, "linkedin.md")
    li_version = os.path.join(social_dir, f"linkedin_{run_suffix}.md")
    for target in (li_version, li_latest):
        with open(target, "w", encoding="utf-8") as f:
            f.write(body)

def _gen_instagram(brief, context: str, style_text: str, artifacts_dir: str, run_suffix: str):
    hashtags = _hashtags_from_tags(brief.get("tags", []), max_n=7)
    def _tone_for_persona(default_tone: str) -> str:
        p = (brief.get("persona") or os.getenv("GEN_PERSONA") or "").strip().lower()
        if not p:
            return default_tone
        mapping = {
            "founder": "punchy, outcome-first",
            "pm": "balanced, rollout-focused",
            "content": "editorial, scannable",
            "sme": "precise, technical"
        }
        addon = mapping.get(p)
        if addon and addon.lower() not in (default_tone or "").lower():
            return f"{default_tone}, {addon}" if default_tone else addon
        return default_tone
    tone_val = _tone_for_persona(brief.get("tone", "direct"))
    prompt = load_prompt(
        "engine/prompts/post_system.txt",
        "engine/prompts/instagram_user.txt",
        title=brief.get("title", ""),
        audience=brief.get("audience", "general"),
        goal=brief.get("goal", "inform"),
        tone=tone_val,
        style=style_text,
        style_examples=_load_style_examples_text(brief),
        context=context,
        hashtags=hashtags,
        allowed_domains=_allowed_domains_from_brief(brief),
        no_external=str(bool(brief.get("no_external", False))),
        controls=_controls_from_brief(brief),
        must_terms_line=_must_terms_line(brief),
    )
    attempts = 0
    body = ""
    last_errs: list[str] = []
    while attempts < 2:
        body_raw = ollama_complete(prompt, length="short").strip()
        body = _strip_meta_artifacts(body_raw)
        ok, errs = _lint_social(body, platform="instagram")
        if ok:
            break
        last_errs = errs
        attempts += 1
    if attempts >= 2:
        title = brief.get("title", "")
        body = f"{title}\n\n-> Clear rules. Fast drafts. Fewer rewrites.\n\n{_hashtags_from_tags(brief.get('tags', []), max_n=7)}"
    enforce = os.getenv("SOCIAL_ENFORCE", "0").lower() in ("1", "true", "yes")
    ok_final, errs_final = _lint_social(body, platform="instagram")
    try:
        meta_dir = os.path.join(artifacts_dir, "meta"); ensure_dir(meta_dir)
        with open(os.path.join(meta_dir, "social_quality.json"), "a", encoding="utf-8") as f:
            json.dump({"platform": "instagram", "attempts": attempts, "ok": ok_final, "errs": errs_final or last_errs}, f); f.write("\n")
    except Exception:
        pass
    if enforce and not ok_final:
        return
    body = instagram_format(body, hashtags, limit=2200)
    body = _enforce_char_limit(body, 2200)
    social_dir = os.path.join(artifacts_dir, "social"); ensure_dir(social_dir)
    ig_latest = os.path.join(social_dir, "instagram.md")
    ig_version = os.path.join(social_dir, f"instagram_{run_suffix}.md")
    for target in (ig_version, ig_latest):
        with open(target, "w", encoding="utf-8") as f:
            f.write(body)

def _gen_github_doc(brief, context: str, style_text: str, artifacts_dir: str, run_suffix: str):
    prompt = load_prompt(
        "engine/prompts/post_system.txt",
        "engine/prompts/github_user.txt",
        title=brief.get("title", ""),
        audience=brief.get("audience", "developers"),
        goal=brief.get("goal", "document"),
        tone=brief.get("tone", "direct"),
        style=style_text,
        style_examples=_load_style_examples_text(brief),
        context=context,
        allowed_domains=_allowed_domains_from_brief(brief),
        no_external=str(bool(brief.get("no_external", False))),
        controls=_controls_from_brief(brief),
        must_terms_line=_must_terms_line(brief),
    )
    md = ollama_complete(prompt, length="medium").strip()
    md = github_format(md)
    github_dir = os.path.join(artifacts_dir, "github"); ensure_dir(github_dir)
    latest_readme = os.path.join(github_dir, "README.md")
    version_readme = os.path.join(github_dir, f"README_{run_suffix}.md")
    for target in (version_readme, latest_readme):
        with open(target, "w", encoding="utf-8") as f:
            f.write(md)


def main(brief_fp: str):
    with open(brief_fp, "r", encoding="utf-8") as f:
        brief = yaml.safe_load(f)

    # Reset per-run globals so successive runs don't leak state
    SECTION_LOGS.clear()
    global _MIN_LEN, _LINT_INCLUDE_TERMS
    _MIN_LEN = dict(_MIN_LEN_DEFAULTS)
    _LINT_INCLUDE_TERMS = []

    override_outputs = os.getenv("OUTPUTS")
    if override_outputs:
        overrides = [o.strip() for o in override_outputs.split(",") if o.strip()]
        if overrides:
            brief["outputs"] = overrides

    slug = brief["slug"]
    basename = safe_basename(brief.get("title", ""), slug)
    run_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_started_at = datetime.datetime.utcnow().isoformat()

    def _record_graph(status: str, reason: Optional[str] = None):
        if record_run is None:
            return
        try:
            record_run(
                brief=brief,
                slug=slug,
                brief_path=brief_fp,
                status=status,
                reason=reason,
                started_at=run_started_at,
                finished_at=datetime.datetime.utcnow().isoformat(),
            )
        except Exception:
            pass
    skip_publish_flag = os.getenv("SKIP_PUBLISH", "0").lower() in ("1", "true", "yes") or bool(brief.get("publish", {}).get("skip", False))
    run_variant = "dryrun" if skip_publish_flag else "run"
    run_suffix = f"{run_variant}_{run_ts}"
    artifacts_dir = f"artifacts/{slug}"
    blog_dir   = os.path.join(artifacts_dir, "blog")
    meta_dir   = os.path.join(artifacts_dir, "meta")
    for d in (artifacts_dir, blog_dir, meta_dir):
        ensure_dir(d)

    # Ensure Ollama is reachable before any generation
    _assert_ollama_up()
    _assert_model_available()

    print(f"[info] Using Ollama at {CURRENT_OLLAMA_URL} with model '{GEN_MODEL}'", flush=True)
    # Optional retrieval scoping and topic lint from brief
    try:
        src_paths = brief.get("sources", {}).get("paths", [])
        if isinstance(src_paths, list) and src_paths:
            os.environ["RETRIEVE_SOURCE_PREFIXES"] = ",".join(str(x).strip() for x in src_paths if str(x).strip())
        # Exclude topic patterns if provided
        excl = brief.get("exclude_terms", [])
        safe: list[str] = []
        if isinstance(excl, list) and excl:
            safe.extend(re.escape(str(x)) for x in excl if str(x).strip())
        block_terms = []
        sources_meta = brief.get("sources") or {}
        if isinstance(sources_meta, dict):
            block_terms = sources_meta.get("block", []) or []
        if isinstance(block_terms, list) and block_terms:
            for b in block_terms:
                norm = normalize_domain(str(b))
                if norm:
                    safe.append(re.escape(norm))
        if safe:
            unique = list(dict.fromkeys(safe))
            os.environ["RETRIEVE_EXCLUDE_REGEX"] = "|".join(unique)
        # Build include-term list for section lint: title tokens + tags + optional brief.must_include_terms
        include = []
        if isinstance(brief.get("must_include_terms"), list):
            include.extend([str(x).strip() for x in brief.get("must_include_terms") if str(x).strip()])
        include.extend([str(x).strip() for x in brief.get("tags", []) if str(x).strip()])
        include.extend([w for w in re.split(r"[^A-Za-z0-9]+", brief.get("title", "")) if w])
        # Dedup + lower
        _LINT_INCLUDE_TERMS = sorted(set([w.lower() for w in include if len(w) >= 4]))[:12]
    except Exception:
        pass

    query = f"{brief['title']} {brief.get('tags','')}"
    context, _sources = retrieve(query, k=int(os.getenv("RETRIEVE_K", "8")))
    context = _sanitize_context(context)
    print("[info] Retrieved context for query.", flush=True)

    # Style guidelines
    style_text = _load_style_text(brief)

    length = os.getenv("GEN_LENGTH", brief.get("length", "medium"))

    # Override per-H2 min lengths from brief or env
    try:
        ml = brief.get("min_lengths")
        if isinstance(ml, dict):
            for k, v in ml.items():
                try:
                    if isinstance(v, int) and v > 0:
                        _MIN_LEN[str(k)] = v
                except Exception:
                    pass
        # Env overrides (e.g., MINLEN_OVERVIEW=200)
        env_map = {
            "Overview": os.getenv("MINLEN_OVERVIEW"),
            "Why It Matters": os.getenv("MINLEN_WHY_IT_MATTERS"),
            "Prerequisites": os.getenv("MINLEN_PREREQUISITES"),
            "Steps": os.getenv("MINLEN_STEPS"),
            "Examples": os.getenv("MINLEN_EXAMPLES"),
            "FAQs": os.getenv("MINLEN_FAQS"),
            "References": os.getenv("MINLEN_REFERENCES"),
        }
        for sec, val in env_map.items():
            try:
                if val is not None:
                    iv = int(str(val))
                    if iv > 0:
                        _MIN_LEN[sec] = iv
            except Exception:
                pass
    except Exception:
        pass

    # Single-section regeneration flow (surgical fix)
    only_sec = os.getenv("GEN_ONLY_SECTION", "").strip()
    if only_sec:
        # Retrieve and generate only the requested section, then patch latest draft
        print(f"[info] Regenerating single section: {only_sec}")
        # build context for query
        q = f"{brief['title']} {only_sec} {brief.get('tags','')}"
        _ = retrieve(q, k=int(os.getenv("RETRIEVE_K", "8")))
        only_sec_minlen = os.getenv("GEN_ONLY_SECTION_MINLEN")
        if only_sec_minlen:
            try:
                iv = int(str(only_sec_minlen))
                if iv > 0:
                    _MIN_LEN[only_sec] = iv
            except Exception:
                pass
        # style
        section_text = _generate_section(brief["title"], only_sec, brief, style_text)
        blog_md_path = os.path.join(blog_dir, f"{basename}.md")
        latest_md_path = os.path.join(blog_dir, "latest.md")
        legacy_md_path = os.path.join(blog_dir, "draft.md")
        regen_suffix = f"regen_{run_suffix}"
        version_md_path = os.path.join(blog_dir, f"{basename}_{regen_suffix}.md")
        body_md = f"# {brief['title']}\n\n"
        meta_in = {}
        try:
            source_candidate = blog_md_path if os.path.exists(blog_md_path) else latest_md_path
            if os.path.exists(source_candidate):
                raw = open(source_candidate, "r", encoding="utf-8").read()
                existing = frontmatter.loads(raw)
                # Use existing content only (strip old frontmatter), preserve metadata
                body_md = existing.content or body_md
                meta_in = existing.metadata or {}
        except Exception:
            pass
        patched = _replace_section_in_md(body_md, only_sec, section_text)
        # Merge metadata (prefer brief fields)
        meta_out = dict(meta_in)
        meta_out.update({
            "title": brief["title"],
            "slug": slug,
            "date": datetime.date.today().isoformat(),
            "tags": brief.get("tags", []),
            "persona": brief.get("persona"),
        })
        # Save with a single frontmatter header
        post = frontmatter.Post(patched, **meta_out)
        rendered_post = frontmatter.dumps(post)
        for target in (version_md_path, blog_md_path, latest_md_path, legacy_md_path):
            with open(target, "w", encoding="utf-8") as f:
                f.write(rendered_post)
        # Write HTML & preview
        content_html = md_to_clean_html(patched)
        html_path = os.path.join(blog_dir, f"{basename}.html")
        version_html_path = os.path.join(blog_dir, f"{basename}_{regen_suffix}.html")
        latest_html_path = os.path.join(blog_dir, "latest.html")
        legacy_html_path = os.path.join(blog_dir, "draft.html")
        for target in (version_html_path, html_path, latest_html_path, legacy_html_path):
            with open(target, "w", encoding="utf-8") as f:
                f.write(content_html)
        _write_preview_index(artifacts_dir, slug, basename)
        # Write section logs
        try:
            with open(os.path.join(meta_dir, "section_quality.json"), "w", encoding="utf-8") as f:
                json.dump(SECTION_LOGS, f, indent=2)
        except Exception:
            pass
        print(f"[ok] Regenerated section '{only_sec}'. Preview: file://{os.path.join(os.getcwd(), artifacts_dir, 'index.html')}")
        _record_graph("ok", "regen_only")
        return

    # Sectional blog generation (opt-in)
    is_sectional = (
        brief.get("blog_mode") == "sectional"
        or brief.get("sectional") is True
        or (isinstance(brief.get("blog"), dict) and brief.get("blog", {}).get("mode") == "sectional")
    )
    framework = str(brief.get("framework", "")).lower().strip()

    if is_sectional:
        print(f"[info] Sectional mode enabled (framework='{framework or 'default'}').", flush=True)
        if framework == "fnf":
            sections = [
                "Friction",
                "Bridge",
                "Evidence",
                "Implication",
                "Action",
                "Look Ahead",
                "Reflection",
            ]
        else:
            sections = [
                "Overview",
                "Why It Matters",
                "Prerequisites",
                "Steps",
                "Examples",
                "FAQs",
                "References",
            ]
        # Optional simple planner to customize sections
        # Allow disabling planner via env for reproducibility
        disable_planner = os.getenv("GEN_DISABLE_PLANNER", "0").lower() in ("1", "true", "yes")
        use_planner = (brief.get("planner") == "outline" or brief.get("agentic") is True) and not disable_planner
        if use_planner and framework != "fnf":
            try:
                outline_prompt = load_prompt(
                    "engine/prompts/post_system.txt",
                    "engine/prompts/outline_user.txt",
                    title=brief.get("title", ""),
                    audience=brief.get("audience", "general"),
                    goal=brief.get("goal", "inform"),
                    tone=brief.get("tone", "direct"),
                    style=style_text,
                    style_examples=_load_style_examples_text(brief),
                    context=context,
                    controls=_controls_from_brief(brief),
                    must_terms_line=_must_terms_line(brief),
                )
                outline = ollama_complete(outline_prompt, length="short").strip()
                data = json.loads(outline)
                secs = data.get("sections")
                if isinstance(secs, list) and secs:
                    cleaned = []
                    for s in secs:
                        s = str(s).strip()
                        if s and s.lower() not in ("introduction", "conclusion"):
                            cleaned.append(s)
                    if cleaned:
                        sections = cleaned
            except Exception:
                pass
        parts = {}
        if framework == "fnf":
            # Generate heading + body per layer
            total = len(sections)
            for idx, layer in enumerate(sections, 1):
                print(f"[gen] ({idx}/{total}) {layer}...", flush=True)
                h, b = _generate_fnf_section(brief["title"], layer, brief, style_text)
                parts[layer] = {"heading": h, "body": b}
        else:
            total = len(sections)
            for idx, s in enumerate(sections, 1):
                print(f"[gen] ({idx}/{total}) {s}...", flush=True)
                parts[s] = _generate_section(brief["title"], s, brief, style_text)

        # Assemble final Markdown
        md_lines = [f"# {brief['title']}", ""]
        used_h2 = set()
        for s in sections:
            if framework == "fnf":
                sec = parts.get(s, {})
                heading = (sec.get("heading", s) or s).strip()
                body = (sec.get("body", "") or "").strip()
                # Ensure unique H2 headings: append layer label if duplicate
                h2 = heading
                if h2 in used_h2:
                    h2 = f"{heading} ({s})"
                used_h2.add(h2)
                md_lines.append(f"## {h2}")
                md_lines.append(body)
                md_lines.append("")
            else:
                md_lines.append(f"## {s}")
                md_lines.append(parts.get(s, "").strip())
                md_lines.append("")
        draft_md = "\n".join(md_lines).strip()
        # De-duplicate repeated paragraphs across sections
        draft_md = _dedupe_paragraphs(draft_md)
        print("[info] Sections assembled.", flush=True)
    else:
        # Original single-pass generation
        prompt = load_prompt(
            "engine/prompts/post_system.txt",
            "engine/prompts/post_user.txt",
            content_type=brief.get("type", "blog"),
            title=brief["title"],
            audience=brief.get("audience", "general"),
            goal=brief.get("goal", "inform"),
            tone=brief.get("tone", "direct"),
            length=length,
            context=context,
            style=style_text,
            style_examples=_load_style_examples_text(brief),
            allowed_domains=_allowed_domains_from_brief(brief),
            no_external=str(bool(brief.get("no_external", False))),
            controls=_controls_from_brief(brief),
            must_terms_line=_must_terms_line(brief),
        )
        print("[gen] single-pass blog...", flush=True)
        draft_md = ollama_complete(prompt, length=length).strip()
        draft_md = blog_format(draft_md)

    # === Enforce citations policy (allowlist/no_external) before audit ===
    allow_domains_list = _normalize_domains_list(brief.get("sources", {}).get("allow", []) if isinstance(brief.get("sources", {}), dict) else [])
    draft_md, kept_urls, found_urls = _sanitize_references(draft_md, allow_domains_list, no_external=bool(brief.get("no_external", False)))
    draft_md = _strip_meta_artifacts(draft_md)
    print("[info] Citations sanitized and References section rebuilt.", flush=True)

    # === Audit ===
    # If no_external is true, skip URL/References requirement and only enforce minimum length.
    no_external_flag = bool(brief.get("no_external", False))
    url_count = len(kept_urls)
    min_len = int(os.getenv("AUDIT_MIN_LEN", "500"))
    ref_failure = _audit_references(no_external_flag, found_urls, kept_urls)
    if ref_failure:
        with open(os.path.join(meta_dir, "failure.json"), "w") as f:
            json.dump(ref_failure, f, indent=2)
        print("Audit fail: missing References or all filtered. Saved artifacts.")
        _record_graph("audit_failed", (ref_failure or {}).get("reason"))
        return
    # Reject meta artifacts
    if re.search(r"^(Document:|Your task:|I\'m sorry|In a hypothet)", draft_md, flags=re.I | re.M):
        with open(os.path.join(meta_dir, "failure.json"), "w") as f:
            json.dump({"reason": "audit_failed_meta_artifacts"}, f, indent=2)
        print("Audit fail: meta artifacts detected. Saved artifacts.")
        _record_graph("audit_failed", "meta_artifacts")
        return
    if no_external_flag:
        if len(draft_md) < min_len:
            with open(os.path.join(meta_dir, "failure.json"), "w") as f:
                json.dump({"reason": "audit_failed_min_requirements", "len": len(draft_md)}, f, indent=2)
            print("Audit fail: too short. Saved artifacts.")
            _record_graph("audit_failed", "min_length")
            return
    else:
        # Require at least one allowed URL and a sane length
        if url_count < 1 or len(draft_md) < min_len:
            with open(os.path.join(meta_dir, "failure.json"), "w") as f:
                json.dump({"reason": "audit_failed_min_requirements", "len": len(draft_md)}, f, indent=2)
            print("Audit fail: missing References or too short. Saved artifacts.")
            _record_graph("audit_failed", "min_requirements")
            return

    # === Guardrail 1: Allowlist enforcement ===
    allow = [d for d in allow_domains_list if d]
    if allow:
        urls = extract_references(draft_md)
        ref_domains = parse_domains(urls)
        violations = [d for d in ref_domains if d not in allow]
        if violations:
            with open(os.path.join(meta_dir, "references_violation.json"), "w") as f:
                json.dump({
                    "reason": "allowlist_violation",
                    "allowed": allow,
                    "found": ref_domains,
                    "violations": violations
                }, f, indent=2)
            print("[guard] Reference allowlist violation. Skipping publish. See meta/references_violation.json.")
            _record_graph("guard_failed", "allowlist_violation")
            return

    block = [normalize_domain(d) for d in brief.get("sources", {}).get("block", [])]
    block = [d for d in block if d]
    if block:
        urls = extract_references(draft_md)
        ref_domains = parse_domains(urls)
        blocked_hits = [d for d in ref_domains if d in block]
        if blocked_hits:
            with open(os.path.join(meta_dir, "references_blocked.json"), "w") as f:
                json.dump({
                    "reason": "blocklist_violation",
                    "blocked": block,
                    "found": ref_domains,
                    "violations": blocked_hits
                }, f, indent=2)
            print("[guard] Blocked domain detected. Skipping publish. See meta/references_blocked.json.")
            _record_graph("guard_failed", "blocklist_violation")
            return

    # Versioned artifact paths (per-run, per-mode)
    blog_dir = os.path.join(artifacts_dir, "blog")
    ensure_dir(blog_dir)
    md_path = os.path.join(blog_dir, f"{basename}.md")
    md_version_path = os.path.join(blog_dir, f"{basename}_{run_suffix}.md")
    legacy_md_path = os.path.join(blog_dir, "draft.md")
    latest_md_path = os.path.join(blog_dir, "latest.md")

    # Save markdown artifact
    post = frontmatter.Post(
        draft_md,
        **{
            "title": brief["title"],
            "slug": slug,
            "date": datetime.date.today().isoformat(),
            "tags": brief.get("tags", []),
            "persona": brief.get("persona"),
        },
    )
    rendered_post = frontmatter.dumps(post)
    for target in (md_version_path, md_path, latest_md_path, legacy_md_path):
        with open(target, "w", encoding="utf-8") as f:
            f.write(rendered_post)

    fallback_used = any(log.get("used_fallback") for log in SECTION_LOGS)
    duplicate_blocked = False

    if fallback_used:
        print("[warn] Section fallback content used; skipping duplicate check until regeneration passes lint.")
    else:
        # === Guardrail 2: Duplicate protection ===
        draft_vec = []
        try:
            vecs = embed_texts([draft_md], normalize=True)
            draft_vec = vecs[0] if vecs else []
        except Exception as exc:
            print(f"[warn] Duplicate check skipped: {exc}")

        recents = load_recent_history(n=50)
        max_sim, nearest = 0.0, None
        for r in recents:
            sim = cosine(draft_vec, r.get("vector", []))
            if sim > max_sim:
                max_sim, nearest = sim, r

        # Duplicate threshold configurable; allow bypass via env
        allow_dups = os.getenv("ALLOW_DUPLICATES", "0").lower() in ("1", "true", "yes")
        dup_thresh = 0.92
        try:
            dup_thresh = float(os.getenv("DUPLICATE_THRESHOLD", str(dup_thresh)))
        except Exception:
            pass
        if (not allow_dups) and max_sim >= dup_thresh:
            with open(os.path.join(meta_dir, "duplicate.json"), "w") as f:
                json.dump({
                    "reason": "duplicate_detected",
                    "similarity": round(max_sim, 4),
                    "nearest": {"slug": nearest.get("slug"), "title": nearest.get("title"), "date": nearest.get("date")}
                }, f, indent=2)
            print(f"Duplicate detected (cos={max_sim:.3f}). Skipping publish.")
            duplicate_blocked = True
        else:
            # Only append to history when duplicate protection passes
            append_history({
                "slug": slug,
                "title": brief.get("title"),
                "date": datetime.datetime.now().isoformat(),
                "vector": draft_vec,
            })

    if duplicate_blocked:
        _record_graph("duplicate_blocked", "duplicate_detected")
        return

    # Convert to HTML
    content_html = md_to_clean_html(draft_md)
    html_path = os.path.join(blog_dir, f"{basename}.html")
    html_version_path = os.path.join(blog_dir, f"{basename}_{run_suffix}.html")
    legacy_html_path = os.path.join(blog_dir, "draft.html")
    latest_html_path = os.path.join(blog_dir, "latest.html")
    for target in (html_version_path, html_path, latest_html_path, legacy_html_path):
        with open(target, "w", encoding="utf-8") as f:
            f.write(content_html)
    print(f"[ok] Wrote blog: {md_path} and {html_path}", flush=True)
    # Write section quality logs for transparency
    try:
        with open(os.path.join(meta_dir, "section_quality.json"), "w", encoding="utf-8") as f:
            json.dump(SECTION_LOGS, f, indent=2)
    except Exception:
        pass

    # Multi-platform outputs
    outputs = brief.get("outputs")
    if isinstance(outputs, list) and outputs:
        # normalize values like ["blog","linkedin","instagram","github_doc"]
        outs = [str(x).lower().strip() for x in outputs]
        if "linkedin" in outs:
            _gen_linkedin(brief, context, style_text, artifacts_dir, run_suffix)
        if "instagram" in outs:
            _gen_instagram(brief, context, style_text, artifacts_dir, run_suffix)
        if "github_doc" in outs or "github" in outs:
            _gen_github_doc(brief, context, style_text, artifacts_dir, run_suffix)
        print(f"[ok] Wrote social/github outputs under {artifacts_dir}/social and /github", flush=True)

    else:
        # Back-compat: generate basic social snippets if requested
        if brief.get("social", False):
            social_dir = os.path.join(artifacts_dir, "social"); ensure_dir(social_dir)
            generate_social(brief, draft_md, os.path.join(social_dir, "social.md"), run_suffix)

    # Write a simple preview index for local browsing
    _write_preview_index(artifacts_dir, slug, basename)
    print(f"[ok] Preview: file://{os.path.join(os.getcwd(), artifacts_dir, 'index.html')}", flush=True)

    # Publish if WP creds exist
    base = os.getenv("WP_BASE_URL")
    user = os.getenv("WP_USER")
    apw  = os.getenv("WP_APP_PASSWORD")
    status = brief.get("publish", {}).get("status", "draft")
    date   = brief.get("publish", {}).get("date")
    cats   = brief.get("publish", {}).get("category_ids", [])
    tag_ids = brief.get("publish", {}).get("tag_ids")  # WP expects numeric tag IDs

    # Allow skipping publish for local testing via env or brief flag
    skip_publish = os.getenv("SKIP_PUBLISH", "0").lower() in ("1", "true", "yes") or bool(brief.get("publish", {}).get("skip", False))
    if (base and user and apw) and not skip_publish:
        from engine.tools.wp_publish import WPPublisher
        if status not in ["draft", "publish", "future"]:
            status = "draft"
        wp = WPPublisher(base, user, apw)
        # Validate categories/tags as integers; skip invalid ones to avoid 400
        warnings = []
        cat_ids_clean = []
        try:
            for c in (cats or []):
                if isinstance(c, int) or (isinstance(c, str) and c.isdigit()):
                    cat_ids_clean.append(int(c))
                else:
                    warnings.append("Skipped non-integer category id: %r" % c)
        except Exception:
            pass
        tag_ids_clean = []
        if tag_ids is not None:
            try:
                for t in (tag_ids or []):
                    if isinstance(t, int) or (isinstance(t, str) and t.isdigit()):
                        tag_ids_clean.append(int(t))
                    else:
                        warnings.append("Skipped non-integer tag id: %r" % t)
            except Exception:
                pass

        try:
            res = wp.create_post(
                title=brief["title"],
                content_html=content_html,
                status=status,
                slug=slug,
                category_ids=cat_ids_clean or None,
                date=date,
                tags=tag_ids_clean or None,
            )
            with open(os.path.join(meta_dir, "publish.json"), "w") as f:
                json.dump(res, f, indent=2)
            print(f"WordPress post created: id={res.get('id')}, status={res.get('status')}")
        except Exception as e:
            # Capture server response for debugging
            err_payload = {"error": str(e)}
            try:
                import traceback as _tb
                err_payload["traceback"] = _tb.format_exc()
            except Exception:
                pass
            with open(os.path.join(meta_dir, "publish_error.json"), "w") as f:
                json.dump(err_payload, f, indent=2)
            print("[warn] WordPress publish failed. See meta/publish_error.json")
    else:
        if skip_publish:
            print("[info] Skipped publish (SKIP_PUBLISH=1). Artifacts written.")
        else:
            print("WP creds not set; skipped publishing. Artifacts written.")

    _record_graph("ok")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python engine/run.py briefs/<file>.yaml")
        sys.exit(2)
    main(sys.argv[1])
