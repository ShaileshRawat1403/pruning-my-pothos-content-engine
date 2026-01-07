import os
import sys
import json
import time
import streamlit as st
from typing import Any, Dict

# Guard against noisy torch telemetry/class lookup warnings in certain builds
try:
    import torch
    if getattr(torch, "classes", None) is not None:
        from types import SimpleNamespace
        cls_dict = getattr(torch.classes, "__dict__", None)
        if not (isinstance(cls_dict, dict) and "__path__" in cls_dict):
            setattr(torch.classes, "__path__", SimpleNamespace(_path=None))  # type: ignore[attr-defined]
except Exception:
    pass

# Silence telemetry clients in embedded libraries (Chromadb, PostHog)
os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")
os.environ.setdefault("CHROMA_TELEMETRY_DISABLED", "1")
os.environ.setdefault("POSTHOG_DISABLED", "1")

# Ensure project root is on sys.path so `ui.*` imports resolve when running as a script
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ui.utils import (
    run_cmd, list_files_glob, read_text, write_text,
    load_env_preserve_comments, save_env_preserve_comments, WHITELIST_ENV_KEYS,
    list_slugs, artifacts_for_slug, load_briefs_index,
    check_ollama, check_wordpress, append_jsonl, list_ollama_models,
    chunk_counts_for_paths,
)


MODEL_PRESETS = [
    ("phi3:mini-128k", "Long-context default"),
    ("llama3.2:3b", "Balanced smaller option"),
    ("llama3:8b-instruct-q4", "Larger llama on capable hardware"),
]

MODEL_CANDIDATE_HINTS = [
    ("phi3:mini-128k,llama3.2:3b", "Speed-first with llama safety net"),
    ("llama3.2:3b,phi3:mini-128k", "Balanced default with fast fallback"),
]

BRIEF_TEMPLATE_HINTS = [
    {
        "label": "Docs-as-Code Governance Checklist",
        "title": "Docs-as-Code Governance Checklist for SMBs",
        "slug": "docs-as-code-governance-checklist",
        "tags": "docs-as-code,governance,smbs",
        "persona": "content",
        "style_profile": "pruningmypothos",
        "blog_mode": True,
        "planner": True,
        "no_external": True,
        "allowed": "pruningmypothos.com\ngitlab.com\ndocs.github.com",
        "outputs": ["blog", "linkedin"],
        "publish_status": "draft",
    },
    {
        "label": "AI Governance Playbook Launch",
        "title": "AI Content Governance Playbook for SMB Teams",
        "slug": "ai-content-governance-playbook-smb",
        "tags": "ai-governance,smbs,playbook",
        "persona": "founder",
        "style_profile": "pruningmypothos",
        "blog_mode": True,
        "planner": True,
        "no_external": False,
        "allowed": "pruningmypothos.com\nnist.gov\nopenpolicy.gov",
        "outputs": ["blog", "linkedin", "instagram"],
        "publish_status": "draft",
    },
]

LORA_SECTION_PRESETS = [
    {
        "label": "Docs-as-Code Overview",
        "title": "Docs-as-Code Governance Checklist for SMBs",
        "h2": "Overview",
        "persona": "content",
        "body": (
            "Docs-as-code governance keeps every team on the same version of the playbook:\n"
            "- Add pull-request templates for every doc change\n"
            "- Require reviewers to check customer impact\n"
            "- Archive stale runbooks after each quarter close"
        ),
    },
    {
        "label": "AI Governance Why It Matters",
        "title": "AI Content Governance Playbook for SMB Teams",
        "h2": "Why It Matters",
        "persona": "founder",
        "body": (
            "Without lightweight governance, AI content drifts quickly:\n"
            "- Risky claims creep into product pages\n"
            "- Sales decks lose their source-of-truth citations\n"
            "- Support teams work from inconsistent answers"
        ),
    },
]

LORA_POST_PRESETS = [
    {
        "label": "Docs-as-Code Full Post",
        "title": "Docs-as-Code Governance Checklist for SMBs",
        "persona": "content",
        "body": (
            "# Overview\n"
            "Docs-as-code governance creates a shared workflow between product, engineering, and docs.\n\n"
            "# Why It Matters\n"
            "- Prevents stale runbooks from confusing customer teams\n"
            "- Makes audits easier with pull-request history\n\n"
            "# Prerequisites\n"
            "- Git repo for documentation\n"
            "- Review checklist for each release\n\n"
            "# Steps\n"
            "1. Tag owners for every doc set.\n"
            "2. Automate linting with CI.\n"
            "3. Schedule quarterly stale-content reviews.\n\n"
            "# Examples\n"
            "- Support KB refresh tied to each release.\n\n"
            "# FAQs\n"
            "**How often should teams meet?** Weekly standups keep doc debt visible.\n\n"
            "# References\n"
            "- pruningmypothos.com/docs-governance-guide\n"
        ),
    },
    {
        "label": "AI Governance Briefing",
        "title": "AI Content Governance Playbook for SMB Teams",
        "persona": "founder",
        "body": (
            "# Overview\n"
            "AI moves fast, so governance has to keep up without adding heavy process.\n\n"
            "# Why It Matters\n"
            "- Reduces the risk of compliance gaps in outbound content\n"
            "- Keeps customer-facing teams aligned on approved language\n\n"
            "# Prerequisites\n"
            "- Lightweight content review board\n"
            "- Inventory of AI-assisted assets\n\n"
            "# Steps\n"
            "1. Map high-risk content journeys.\n"
            "2. Stand up draft review checklists.\n"
            "3. Track AI usage in a shared log.\n\n"
            "# Examples\n"
            "- Weekly audit of AI-generated support macros.\n\n"
            "# FAQs\n"
            "**Do we need legal sign-off every time?** No - focus on the high-risk launches.\n\n"
            "# References\n"
            "- pruningmypothos.com/ai-governance-starter\n"
        ),
    },
]


st.set_page_config(page_title="Content Engine UI", layout="wide")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Manrope:wght@400;500;600;700&display=swap');
    :root {
      --accent: #0ea5e9;
      --accent-2: #f97316;
      --accent-3: #8b5cf6;
      --bg-card: rgba(255, 255, 255, 0.9);
      --bg-soft: #f4f7fb;
      --text: #0f172a;
      --muted: #475569;
      --shadow: 0 14px 40px rgba(15, 23, 42, 0.16);
    }
    @keyframes bgShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    @keyframes floaty { 0% { transform: translateY(0px);} 50% { transform: translateY(-8px);} 100% { transform: translateY(0px);} }
    html, body, [class*="css"]  { font-family: 'Manrope', 'Space Grotesk', system-ui, -apple-system, sans-serif; }
    body {
      background: radial-gradient(circle at 20% 20%, rgba(14,165,233,0.14), transparent 26%),
                  radial-gradient(circle at 80% 10%, rgba(249,115,22,0.12), transparent 22%),
                  radial-gradient(circle at 60% 80%, rgba(139,92,246,0.12), transparent 24%),
                  linear-gradient(120deg, #eef2ff 0%, #f7fbff 55%, #fef7f1 100%);
      background-size: 160% 160%;
      animation: bgShift 24s ease-in-out infinite;
    }
    .block-container { max-width: 1280px; padding-top: 16px; padding-bottom: 24px; }
    .glass { position: fixed; inset: 0; pointer-events: none; overflow: hidden; z-index: -1; }
    .blob { position: absolute; width: 340px; height: 340px; border-radius: 50%; filter: blur(100px); opacity: 0.5; animation: floaty 14s ease-in-out infinite; }
    .blob.blue { background: rgba(14,165,233,0.22); top: 10%; left: -8%; }
    .blob.orange { background: rgba(249,115,22,0.18); top: 4%; right: -6%; animation-duration: 16s; }
    .blob.purple { background: rgba(139,92,246,0.20); bottom: 6%; right: 12%; animation-duration: 18s; }
    /* Cards */
    .card { background: var(--bg-card); border-radius: 16px; padding: 18px 20px; box-shadow: var(--shadow); border: 1px solid rgba(15,23,42,0.05); animation: fadeInUp .35s ease both; backdrop-filter: blur(4px); }
    .card + .card { margin-top: 18px; }
    @keyframes fadeInUp { from { transform: translateY(10px); opacity: .0;} to { transform: translateY(0); opacity: 1;} }
    /* Tabs */
    .stTabs [role="tablist"] { gap: 6px; padding-bottom: 6px; }
    .stTabs [role="tab"] { background: rgba(255,255,255,0.7); border-radius: 14px 14px 0 0; padding: 10px 14px; border: 1px solid rgba(15,23,42,0.05); box-shadow: 0 8px 16px rgba(15,23,42,0.06); }
    .stTabs [role="tab"][aria-selected="true"] { background: linear-gradient(135deg, rgba(14,165,233,0.18), rgba(139,92,246,0.18)); color: #0f172a; }
    /* Badges */
    .badge-row { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin: 6px 0 14px 0; }
    .badge { display:inline-flex; align-items:center; padding:6px 12px; border-radius:999px; background: var(--bg-soft); color: var(--muted); font-size:12px; border:1px solid rgba(15,23,42,0.12); letter-spacing: 0.01em; }
    .badge.accent { background: rgba(14,165,233,.12); color: #075985; border-color: rgba(14,165,233,.25); box-shadow: 0 0 0 1px rgba(14,165,233,0.18); }
    .badge.highlight { background: rgba(249,115,22,.12); color: #9a3d00; border-color: rgba(249,115,22,.35); }
    @keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(91,140,255,.2);} 50% { box-shadow: 0 0 0 6px rgba(91,140,255,.08);} }
    /* Buttons */
    .stButton>button { background: linear-gradient(135deg, var(--accent), #8b5cf6); color: #fff; border: none; border-radius: 12px; padding: 0.6rem 1.05rem; transition: transform .08s ease, box-shadow .2s ease; box-shadow: 0 10px 24px rgba(15,23,42,.18); }
    .stButton>button:hover { box-shadow: 0 12px 26px rgba(14,165,233,.22); transform: translateY(-1px); }
    .stButton>button:active { transform: translateY(0); }
    /* Inputs */
    .stTextInput>div>div>input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"]>div { border-radius: 12px; border-color: rgba(15,23,42,0.12); }
    /* Sections */
    .section-title { font-size: 1.1rem; color: var(--text); margin: 0 0 8px 0; }
    .muted { color: var(--muted); }
    .hero { background: rgba(255,255,255,0.9); border:1px solid rgba(15,23,42,0.05); box-shadow: var(--shadow); border-radius: 14px; padding: 12px 14px; backdrop-filter: blur(6px); }
    .hero h1 { margin-bottom: 6px; }
    .divider-soft { height:1px; background: linear-gradient(90deg, transparent, rgba(14,165,233,0.32), transparent); margin: 6px 0 12px 0;}
    .toolbar { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:6px;}
    .pill { padding:6px 10px; border-radius:12px; border:1px solid rgba(15,23,42,0.08); background: #fff; box-shadow: 0 2px 8px rgba(15,23,42,0.05);}
    /* Expander polish */
    div[data-testid="stExpander"] { border: 1px solid rgba(15,23,42,0.05); border-radius: 12px; background: rgba(255,255,255,0.4); }
    </style>
    <div class="glass">
      <div class="blob blue"></div>
      <div class="blob orange"></div>
      <div class="blob purple"></div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.title("Co-Da")
st.markdown("AI-powered (Content + Data) Engine")

if "global_model" not in st.session_state:
    st.session_state.global_model = os.getenv("GEN_MODEL", "phi3:mini-128k")
if "global_fallback" not in st.session_state:
    st.session_state.global_fallback = os.getenv("GEN_MODEL_FALLBACK", "llama3.2:3b")


def cached_ollama_models(base: str) -> list[str]:
    return list_ollama_models(base)


@st.cache_data(show_spinner=False, ttl=10)
def cached_slugs() -> list[str]:
    return list_slugs()


@st.cache_data(show_spinner=False, ttl=10)
def cached_briefs_index() -> Dict[str, Dict[str, Any]]:
    return load_briefs_index()


def _refresh_models_cache():
    # No caching now; this is kept for future hook
    pass


def _default_model() -> str:
    base = os.getenv("OLLAMA_URL", "http://localhost:11434")
    models = cached_ollama_models(base)
    val = st.session_state.get("global_model") or os.getenv("GEN_MODEL", "phi3:mini-128k")
    if models and val not in models:
        val = models[0]
        st.session_state.global_model = val
    return val


def _default_fallback() -> str:
    base = os.getenv("OLLAMA_URL", "http://localhost:11434")
    models = cached_ollama_models(base)
    val = st.session_state.get("global_fallback") or os.getenv("GEN_MODEL_FALLBACK", "llama3.2:3b")
    if models and val not in models:
        val = models[1] if len(models) > 1 else models[0]
        st.session_state.global_fallback = val
    return val


hero_md = f"""
<div class='hero'>
  <div class='badge-row'>
    <span class='badge accent'>model: {_default_model()}</span>
    <span class='badge highlight'>fallback: {_default_fallback()}</span>
    <span class='badge'>temp {os.getenv('GEN_TEMPERATURE','0.0')} · seed {os.getenv('GEN_SEED','42')}</span>
    {f"<span class='badge'>candidates: {os.getenv('GEN_MODEL_CANDIDATES','')}</span>" if os.getenv('GEN_MODEL_CANDIDATES','') else ''}
  </div>
</div>
"""
summary_text = f"Active model: {_default_model()} | fallback: {_default_fallback()} | temp {os.getenv('GEN_TEMPERATURE','0.0')} | seed {os.getenv('GEN_SEED','42')}"
st.caption(summary_text)

with st.expander("Model & runtime settings", expanded=False):
    st.markdown(hero_md, unsafe_allow_html=True)

    active_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    if st.button("Refresh models", key="btn_refresh_models", help="Re-query /api/tags"):
        st.rerun()
    models = cached_ollama_models(active_url)
    if models:
        # Auto-align defaults to installed models if env/session values are missing or stale
        if _default_model() not in models and models:
            st.session_state.global_model = models[0]
        if _default_fallback() not in models and models:
            st.session_state.global_fallback = models[1] if len(models) > 1 else models[0]
    else:
        st.info("No models detected via /api/tags; check OLLAMA_URL or pull a model.", icon="⚠️")

    with st.form("model_switcher"):
        colh1, colh2, colh3 = st.columns([1.2, 1.2, 0.6])
        with colh1:
            primary_opts = models if models else []
            try:
                idx = primary_opts.index(_default_model())
            except ValueError:
                idx = 0 if primary_opts else -1
            primary_choice = st.selectbox(
                "Installed primary",
                options=primary_opts if primary_opts else ["(none detected)"],
                index=idx if idx >= 0 else 0,
                key="hero_model_select",
            )
            primary_custom = st.text_input("Or type model tag", value=_default_model(), key="hero_model_custom")
        with colh2:
            fb_opts = models if models else []
            try:
                fb_idx = fb_opts.index(_default_fallback())
            except ValueError:
                fb_idx = 0 if fb_opts else -1
            fallback_choice = st.selectbox(
                "Installed fallback",
                options=fb_opts if fb_opts else ["(none detected)"],
                index=fb_idx if fb_idx >= 0 else 0,
                key="hero_fb_select",
            )
            fallback_custom = st.text_input("Or type fallback tag", value=_default_fallback(), key="hero_fb_custom")
        with colh3:
            temp = os.getenv("GEN_TEMPERATURE", "0.0")
            seed = os.getenv("GEN_SEED", "42")
            st.markdown(f"<div class='pill'>temp {temp} · seed {seed}</div>", unsafe_allow_html=True)
            st.caption("Tweak in Settings or per-run.")
        submitted = st.form_submit_button("Apply models")
        if submitted:
            chosen_primary = primary_custom.strip() or primary_choice
            chosen_fallback = fallback_custom.strip() or fallback_choice
            st.session_state.global_model = chosen_primary
            st.session_state.global_fallback = chosen_fallback
            st.session_state.opt_gen_model = chosen_primary
            st.session_state.opt_gen_model_fallback = chosen_fallback
            st.success(f"Active model set to {chosen_primary} (fallback {chosen_fallback})")
            st.rerun()


def section_ingest():
    st.header("Ingest")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.caption("Tip: GitHub links are auto-converted to raw content for cleaner Markdown.")
    tabs = st.tabs(["Web URLs", "Files", "Paste", "Structured YAML", "Convert", "GitHub"])

    def _show_chunk_counts(saved: list[str]):
        stats = chunk_counts_for_paths(saved)
        if not stats:
            return
        st.markdown("**Chunk counts**")
        for path, count in stats:
            rel = os.path.relpath(path, os.getcwd()) if os.path.isabs(path) else path
            st.write(f"{rel} -> {count} chunk{'s' if count != 1 else ''}")

    # Web URLs tab
    with tabs[0]:
        st.subheader("Add URLs")
        urls_text = st.text_area(
            "URLs (one per line)",
            height=140,
            placeholder="https://github.com/microsoft/LoRA\nhttps://docusaurus.io/docs/",
            key="ing_urls_text",
        )
        st.caption("We'll fetch pages and store clean Markdown under content/imports/.")
        if st.button("Ingest URLs", key="btn_ingest_urls"):
            urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
            if urls:
                import tempfile
                with tempfile.NamedTemporaryFile("w", delete=False) as tf:
                    for u in urls:
                        tf.write(u + "\n")
                    tmpfile = tf.name
                saved_paths: list[str] = []
                with st.status("Ingesting URLs...", expanded=True):
                    for line in run_cmd([os.sys.executable, "-m", "engine.ingest", "--urls", tmpfile]):
                        st.write(line)
                        if line.startswith("Saved: "):
                            saved_paths.append(line.split("Saved: ", 1)[1].strip())
                st.success("Done")
                if saved_paths:
                    _show_chunk_counts(saved_paths)
            else:
                st.warning("No URLs provided.")
        st.divider()
        if st.button("Rebuild Index", key="btn_rebuild_index_urls"):
            with st.status("Indexing...", expanded=True):
                for line in run_cmd([os.sys.executable, "-m", "engine.rag.build_index"]):
                    st.write(line)
            st.success("Index rebuilt")

    # Files tab
    with tabs[1]:
        st.subheader("Upload Markdown Files")
        up_md = st.file_uploader("Upload .md", type=["md"], accept_multiple_files=True, key="ing_upload_md")
        if up_md and st.button("Save .md to content/", key="btn_save_md"):
            saved = []
            for f in up_md:
                out = os.path.join("content", f.name)
                write_text(out, f.getvalue().decode("utf-8"))
                saved.append(out)
            st.success(f"Saved {len(saved)} file(s) to content/")
            if saved:
                _show_chunk_counts(saved)
        st.divider()
        st.subheader("Upload PDFs / Text")
        up_pdf = st.file_uploader("Upload .pdf", type=["pdf"], key="ing_upload_pdf2")
        if up_pdf and st.button("Extract PDF -> content/", key="btn_pdf_extract2"):
            try:
                from pdfminer.high_level import extract_text
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tf:
                    tf.write(up_pdf.getvalue())
                    tmp_pdf = tf.name
                text = extract_text(tmp_pdf) or ""
                title = os.path.splitext(up_pdf.name)[0]
                md = f"# {title}\n\n" + text.strip()
                path = os.path.join("content", title + ".md")
                write_text(path, md)
                st.success(f"Extracted and saved to {path}")
                _show_chunk_counts([path])
            except Exception as e:
                st.error(f"Failed to extract PDF: {e}")
        up_txt = st.file_uploader("Upload .txt", type=["txt"], key="ing_upload_txt2")
        if up_txt and st.button("Save .txt -> content/", key="btn_txt_save2"):
            try:
                text = up_txt.getvalue().decode("utf-8", errors="ignore")
                title = os.path.splitext(up_txt.name)[0]
                md = f"# {title}\n\n" + text.strip()
                path = os.path.join("content", title + ".md")
                write_text(path, md)
                st.success(f"Saved to {path}")
                _show_chunk_counts([path])
            except Exception as e:
                st.error(f"Failed to save text: {e}")

    # Paste tab
    with tabs[2]:
        st.subheader("Paste Markdown/Text")
        paste_title = st.text_input(
            "Filename (we'll add .md)", value="pasted-note", key="ing_paste_title2", help="Use letters, numbers, dashes."
        )
        paste_body = st.text_area(
            "Markdown/Text",
            height=200,
            value="# Example Note\n\n- Point one\n- Point two\n\n## Why It Matters\nShort, skimmable notes help reuse.",
            key="ing_paste_body2",
        )
        if st.button("Save to content/", key="btn_paste_save2"):
            if paste_body.strip():
                fn = paste_title.strip() or "pasted-note"
                if not fn.endswith(".md"):
                    fn += ".md"
                path = os.path.join("content", fn)
                write_text(path, paste_body)
                st.success(f"Saved to {path}")
                _show_chunk_counts([path])
            else:
                st.warning("Nothing to save.")

    # Structured YAML tab
    with tabs[3]:
        st.subheader("Ingest sources.yaml")
        st.caption("Use this to ingest multiple sources with tags/titles.")
        sample_yaml = """- url: https://github.com/microsoft/LoRA
  title: Microsoft LoRA
  tags: [lora, finetuning]
- url: https://docusaurus.io/docs
  title: Docusaurus Docs
  tags: [docs, static-site]
"""
        yaml_body = st.text_area("sources.yaml content", height=180, key="ing_yaml_body2", value=sample_yaml)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Ingest pasted YAML", key="btn_ingest_yaml_text2"):
                if yaml_body.strip():
                    import tempfile
                    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml") as tf:
                        tf.write(yaml_body)
                        tmp = tf.name
                    saved_paths: list[str] = []
                    with st.status("Ingesting YAML...", expanded=True):
                        for line in run_cmd([os.sys.executable, "-m", "engine.ingest", "--yaml", tmp]):
                            st.write(line)
                            if line.startswith("Saved: "):
                                saved_paths.append(line.split("Saved: ", 1)[1].strip())
                    st.success("Done")
                    if saved_paths:
                        _show_chunk_counts(saved_paths)
                else:
                    st.warning("Nothing to ingest.")
        with c2:
            if st.button("Ingest sources/sources.yaml", key="btn_ingest_yaml_file"):
                path = "sources/sources.yaml"
                if os.path.exists(path):
                    saved_paths: list[str] = []
                    with st.status("Ingesting YAML file...", expanded=True):
                        for line in run_cmd([os.sys.executable, "-m", "engine.ingest", "--yaml", path]):
                            st.write(line)
                            if line.startswith("Saved: "):
                                saved_paths.append(line.split("Saved: ", 1)[1].strip())
                    st.success("Done")
                    if saved_paths:
                        _show_chunk_counts(saved_paths)
                else:
                    st.warning("sources/sources.yaml not found")

    # Convert tab
    with tabs[4]:
        st.subheader("Convert HTML -> Markdown")
        st.caption("For local HTML fragments; prefer URLs in Web tab when possible.")
        up_html = st.file_uploader("Upload .html", type=["html"], key="ing_upload_html2")
        if up_html and st.button("Convert & Save", key="btn_html_convert2"):
            try:
                import engine.ingest as eng_ingest
                from bs4 import BeautifulSoup
                html = up_html.getvalue().decode("utf-8", errors="ignore")
                soup = BeautifulSoup(html, "html.parser")
                md = eng_ingest.html_to_markdown(soup)
                name = os.path.splitext(up_html.name)[0] + ".md"
                path = os.path.join("content", name)
                write_text(path, md)
                st.success(f"Converted and saved to {path}")
                _show_chunk_counts([path])
            except Exception as e:
                st.error(f"Failed to convert HTML: {e}")

    # GitHub helper tab
    with tabs[5]:
        st.subheader("Ingest from GitHub")
        st.caption("Fetch README or a specific file from a GitHub repo using raw content.")
        gh_input = st.text_input(
            "Repo or URL",
            value="",
            placeholder="owner/repo or https://github.com/owner/repo",
            key="ing_github_repo",
            help="Paste a GitHub repo slug or full URL."
        )
        c_gh1, c_gh2 = st.columns(2)
        with c_gh1:
            gh_branch = st.text_input(
                "Branch (optional)",
                value="",
                placeholder="main",
                key="ing_github_branch",
                help="Defaults to the repo's main branch."
            )
        with c_gh2:
            gh_path = st.text_input(
                "Path in repo (optional)",
                value="",
                placeholder="docs/README.md",
                key="ing_github_path",
                help="Pick a specific file when you do not want the README."
            )
        if st.button("Ingest from GitHub", key="btn_ingest_github"):
            def to_raw(u: str, branch: str, path: str) -> str:
                u = (u or "").strip()
                b = (branch or "").strip()
                p = (path or "").strip().lstrip("/")
                if u.startswith("http"):
                    return u
                if p:
                    bb = b or "main"
                    return f"https://raw.githubusercontent.com/{u}/{bb}/{p}"
                bb = b or "main"
                return f"https://raw.githubusercontent.com/{u}/{bb}/README.md"
            url = to_raw(gh_input, gh_branch, gh_path)
            import tempfile
            with tempfile.NamedTemporaryFile("w", delete=False) as tf:
                tf.write(url + "\n")
                tmpfile = tf.name
            saved_paths: list[str] = []
            with st.status("Ingesting from GitHub...", expanded=True):
                for line in run_cmd([os.sys.executable, "-m", "engine.ingest", "--urls", tmpfile]):
                    st.write(line)
                    if line.startswith("Saved: "):
                        saved_paths.append(line.split("Saved: ", 1)[1].strip())
            st.success("Done")
            if saved_paths:
                _show_chunk_counts(saved_paths)
    st.markdown('</div>', unsafe_allow_html=True)


def section_index():
    st.header("Index")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if st.button("Rebuild Index", key="btn_rebuild_index"):
        with st.status("Indexing...", expanded=True) as s:
            for line in run_cmd([os.sys.executable, "-m", "engine.rag.build_index"]):
                st.write(line)
        st.success("Index rebuilt")
    st.markdown('</div>', unsafe_allow_html=True)


def section_generate():
    st.header("Generate")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    briefs = list_files_glob("briefs/*.yaml")
    brief_path = st.selectbox("Brief", briefs)
    if brief_path:
        raw = read_text(brief_path)
        new_raw = st.text_area("Brief YAML", value=raw, height=300)
        colA, colB = st.columns(2)
        with colA:
            if st.button("Save Brief", key="btn_save_brief"):
                write_text(brief_path, new_raw)
                st.success("Saved.")

        with colB:
            st.write("Run Options")
            deterministic = st.checkbox("Deterministic (temp=0, seed=42)", value=True)
            skip_publish = st.checkbox("Skip Publish", value=True)
            temp_default = float(os.getenv("GEN_TEMPERATURE", "0.0"))
            seed_default = int(os.getenv("GEN_SEED", "42"))
            temp_slider = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=temp_default,
                step=0.05,
                help="Lower = steadier outputs. Disabled when deterministic is checked.",
                disabled=deterministic,
            )
            seed_value = st.number_input("Seed", min_value=0, value=seed_default, step=1, disabled=deterministic)
            max_predict_default = max(512, min(8192, int(os.getenv("GEN_MAX_PREDICT", "3200") or 3200)))
            max_predict = st.slider(
                "Max tokens (GEN_MAX_PREDICT)",
                min_value=512,
                max_value=8192,
                step=128,
                value=max_predict_default,
                help="Upper bound for generation length.",
            )
            model_preset = st.selectbox(
                "Quick model fill",
                options=["Keep current"] + [f"{name} - {desc}" for name, desc in MODEL_PRESETS],
                index=0,
                key="opt_model_preset",
                help="Apply a suggested generator model string."
            )
            available_models = cached_ollama_models(os.getenv("OLLAMA_URL", "http://localhost:11434"))
            if model_preset != "Keep current":
                selected_model = model_preset.split(" - ", 1)[0]
                st.session_state.opt_gen_model = selected_model
            model_default = _default_model()
            fallback_default = _default_fallback()
            model = st.text_input(
                "GEN_MODEL",
                value=model_default,
                key="opt_gen_model",
                placeholder="phi3:mini-128k",
                help="Name of the Ollama model to run (e.g., phi3:mini-128k)."
            )
            fallback_model = st.text_input(
                "GEN_MODEL_FALLBACK (optional)",
                value=fallback_default,
                key="opt_gen_model_fallback",
                placeholder="llama3.2:3b",
                help="Used automatically if the primary model runs out of memory or is missing."
            )
            st.session_state.global_model = model
            st.session_state.global_fallback = fallback_model
            if available_models:
                try:
                    idx_model = available_models.index(model) + 1 if model in available_models else 0
                except Exception:
                    idx_model = 0
                choice = st.selectbox(
                    "Installed Ollama models",
                    options=["(keep typed)"] + available_models,
                    index=idx_model,
                    key="opt_gen_model_installed",
                    help="Detected via /api/tags; choose an option to overwrite GEN_MODEL."
                )
                if choice != "(keep typed)":
                    model = choice
                    st.session_state.global_model = choice
            model_cand_preset = st.selectbox(
                "Candidate hints",
                options=["Keep current"] + [f"{val} - {desc}" for val, desc in MODEL_CANDIDATE_HINTS],
                index=0,
                key="opt_model_cand_hint",
                help="Populate GEN_MODEL_CANDIDATES with a proven shortlist."
            )
            if model_cand_preset != "Keep current":
                selected_cands = model_cand_preset.split(" - ", 1)[0]
                st.session_state.opt_gen_model_cands = selected_cands
            model_cands = st.text_input(
                "GEN_MODEL_CANDIDATES (comma-separated)",
                value=os.getenv("GEN_MODEL_CANDIDATES", ""),
                key="opt_gen_model_cands",
                placeholder="phi3:mini-128k,llama3.2:3b",
                help="Comma-separated fallbacks evaluated when rank-and-sample is enabled."
            )
            retrieve_cap = st.number_input(
                "RETRIEVE_MAX_PER_SOURCE",
                min_value=1,
                max_value=5,
                value=int(os.getenv("RETRIEVE_MAX_PER_SOURCE", "1")),
                help="How many chunks to pull from each source during retrieval."
            )
            persona = st.selectbox("Persona (override)", ["", "founder", "pm", "content", "sme"], index=0, key="opt_persona")
            enforce_social = st.checkbox("Enforce Social Rules (block weak saves)", value=True, key="opt_enforce_social")

            env = {"GEN_MODEL": model, "RETRIEVE_MAX_PER_SOURCE": str(retrieve_cap)}
            if model_cands.strip():
                env["GEN_MODEL_CANDIDATES"] = model_cands.strip()
            if fallback_model.strip():
                env["GEN_MODEL_FALLBACK"] = fallback_model.strip()
            if deterministic:
                env.update({"GEN_TEMPERATURE": "0.0", "GEN_SEED": "42"})
            else:
                env.update({"GEN_TEMPERATURE": str(temp_slider), "GEN_SEED": str(seed_value)})
            if skip_publish:
                env.update({"SKIP_PUBLISH": "1"})
            if max_predict:
                env.update({"GEN_MAX_PREDICT": str(int(max_predict))})
            if persona:
                env.update({"GEN_PERSONA": persona})
            if enforce_social:
                env.update({"SOCIAL_ENFORCE": "1"})

            if st.button("Generate Draft", key="btn_generate_draft"):
                with st.status("Generating...", expanded=True) as s:
                    for line in run_cmd([os.sys.executable, "-m", "engine.run", brief_path], env=env):
                        st.write(line)
                st.success("Done. Check Preview tab.")
    st.markdown('</div>', unsafe_allow_html=True)


def section_preview():
    st.header("Preview")
    st.markdown('<div class="card">', unsafe_allow_html=True)

    slugs = cached_slugs()
    if not slugs:
        st.info("Generate a draft to see previews here.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    briefs_index = cached_briefs_index()
    slug_catalog: Dict[str, Dict[str, Any]] = {}
    category_pool: set[str] = set()

    for slug in slugs:
        meta = briefs_index.get(slug, {})
        tags = list(meta.get("tags") or [])  # type: ignore[arg-type]
        if not tags:
            tags = ["Uncategorized"]
        for tag in tags:
            category_pool.add(tag)
        slug_catalog[slug] = {
            "title": meta.get("title") or slug,
            "tags": tags,
            "path": meta.get("path"),
        }

    category_options = ["All content"] + sorted(category_pool, key=lambda s: s.lower())
    selected_category = st.selectbox(
        "Category",
        options=category_options,
        index=0,
        key="preview_category",
    )

    filtered_slugs = [
        slug for slug in slugs
        if selected_category == "All content" or selected_category in slug_catalog[slug]["tags"]
    ]

    if not filtered_slugs:
        st.info("No topics available for this category yet.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    def _topic_label(slug: str) -> str:
        meta = slug_catalog.get(slug, {})
        title = meta.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
        return slug

    selected_slug = st.selectbox(
        "Topic",
        options=filtered_slugs,
        format_func=_topic_label,
        key="preview_topic",
    )

    selected_meta = slug_catalog.get(selected_slug, {})
    brief_path = selected_meta.get("path") if isinstance(selected_meta.get("path"), str) else None
    paths = artifacts_for_slug(selected_slug, selected_meta.get("title"))
    st.caption(f"Artifacts live under `artifacts/{selected_slug}`")

    tab_labels = [
        "Blog Draft (Markdown)",
        "Blog Preview (HTML)",
        "Social Snippets",
        "Quality & Meta",
    ]
    t_md, t_html, t_social, t_meta = st.tabs(tab_labels)

    blog_md_content = None
    if os.path.exists(paths["blog_md"]):
        try:
            import frontmatter as _fm
            _post = _fm.loads(read_text(paths["blog_md"]))
            blog_md_content = str(_post)
        except Exception:
            blog_md_content = read_text(paths["blog_md"])  # fallback raw

    with t_md:
        if blog_md_content:
            st.markdown(blog_md_content)
            import re as _re
            if brief_path:
                st.caption("Regenerate a single section (deterministic output)")
                # Pull style/length defaults from the brief if present
                brief_style = None
                brief_length = None
                try:
                    import yaml as _yaml
                    brief_data = _yaml.safe_load(read_text(brief_path)) or {}
                    brief_style = brief_data.get("style_profile")
                    brief_length = brief_data.get("length")
                except Exception:
                    pass
                style_profiles = [os.path.splitext(os.path.basename(p))[0] for p in list_files_glob("engine/styles/**/*.md")]
                style_default = brief_style if brief_style in style_profiles else (style_profiles[0] if style_profiles else None)
                length_options = ["short", "medium", "long"]
                length_default = brief_length if isinstance(brief_length, str) and brief_length in length_options else "medium"
                sections = [m.group(1).strip() for m in _re.finditer(r"^##\s+(.+)$", blog_md_content, flags=_re.M)]
                if sections:
                    sec = st.selectbox("Section", options=sections, key="regen_section")
                    colr1, colr2, colr3 = st.columns(3)
                    with colr1:
                        persona = st.selectbox("Persona", ["", "founder", "pm", "content", "sme"], index=0, key="regen_persona")
                    with colr2:
                        style_choice = st.selectbox(
                            "Style profile (optional)",
                            options=["(brief default)"] + style_profiles if style_profiles else ["(brief default)"],
                            index=(["(brief default)"] + style_profiles).index(style_default) if style_default in style_profiles else 0,
                            key="regen_style_profile",
                            help="Overrides the brief style for this section only."
                        )
                        if style_choice and style_choice != "(brief default)":
                            try:
                                style_path = os.path.join("engine", "styles", f"{style_choice}.md")
                                if os.path.exists(style_path):
                                    with open(style_path, "r", encoding="utf-8") as sf:
                                        st.text_area("Style preview", sf.read().strip(), height=140, key="regen_style_preview")
                            except Exception:
                                st.caption("Style preview unavailable.")
                    with colr3:
                        model = st.text_input("Model", value=_default_model(), key="regen_model")
                    with st.expander("Tone & length tweaks", expanded=False):
                        tone_hint = st.text_input("Tone / style hint (optional)", value="", key="regen_tone_hint")
                        length_choice = st.selectbox(
                            "Length target",
                            options=["(brief default)"] + length_options,
                            index=(["(brief default)"] + length_options).index(length_default) if length_default in length_options else 0,
                            key="regen_length_choice",
                            help="Adjusts generation length guidance."
                        )
                        min_len_val = st.slider(
                            "Min characters for this section",
                            min_value=80,
                            max_value=6000,
                            value=600,
                            step=20,
                            key="regen_minlen_chars",
                            help="Hard lower bound passed to the generator for this H2."
                        )
                    if st.button("Regenerate Section", key="btn_regen_section"):
                        env = {
                            "GEN_ONLY_SECTION": sec,
                            "SKIP_PUBLISH": "1",
                            "GEN_TEMPERATURE": "0.0",
                            "GEN_SEED": "42",
                            "GEN_MODEL": model,
                        }
                        # Optional overrides
                        if style_choice and style_choice != "(brief default)":
                            env["GEN_STYLE_PROFILE"] = style_choice
                        if tone_hint.strip():
                            env["GEN_STYLE_TEXT"] = tone_hint.strip()
                        if length_choice and length_choice != "(brief default)":
                            env["GEN_LENGTH"] = length_choice
                        if min_len_val:
                            env["GEN_ONLY_SECTION_MINLEN"] = str(int(min_len_val))
                        if persona:
                            env["GEN_PERSONA"] = persona
                        with st.status(f"Regenerating section '{sec}'...", expanded=True):
                            for line in run_cmd([os.sys.executable, "-m", "engine.run", brief_path], env=env):
                                st.write(line)
                        st.success("Section regenerated. Refresh this tab to see updates.")
        else:
            st.info("No blog markdown found for this topic yet.")

    with t_html:
        if os.path.exists(paths["blog_html"]):
            st.markdown(f"[Open preview in browser]({paths['blog_html']})")
        else:
            st.info("No rendered HTML found for this topic yet.")

    with t_social:
        li_path = paths.get("li_md")
        ig_path = paths.get("ig_md") or os.path.join(os.path.dirname(paths["li_md"]), "instagram.md")
        has_social = False
        if li_path and os.path.exists(li_path):
            has_social = True
            st.subheader("LinkedIn")
            st.code(read_text(li_path))
        if ig_path and os.path.exists(ig_path):
            has_social = True
            st.subheader("Instagram")
            st.code(read_text(ig_path))
        if not has_social:
            st.info("No social snippets found for this topic yet.")

    with t_meta:
        if os.path.isdir(paths["meta"]):
            sq = os.path.join(paths["meta"], "section_quality.json")
            if os.path.exists(sq):
                st.subheader("Section Quality")
                st.code(read_text(sq))
            so = os.path.join(paths["meta"], "social_quality.json")
            if os.path.exists(so):
                st.subheader("Social Quality")
                st.code(read_text(so))
            st.subheader("All Meta Files")
            for fn in sorted(os.listdir(paths["meta"])):
                p = os.path.join(paths["meta"], fn)
                st.write(f"{fn}")
                try:
                    st.code(read_text(p))
                except Exception:
                    st.write("(binary or unreadable)")
        else:
            st.info("No meta directory found for this topic yet.")

    st.markdown('</div>', unsafe_allow_html=True)


def section_publish():
    st.header("Publish")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    import yaml, json as _json, time as _time
    # Read creds directly from .env (live), fallback to process env
    _kv_env, _ = load_env_preserve_comments(".env")
    base = (_kv_env.get("WP_BASE_URL") or os.getenv("WP_BASE_URL") or "").strip()
    user = (_kv_env.get("WP_USER") or os.getenv("WP_USER") or "").strip()
    apw  = (_kv_env.get("WP_APP_PASSWORD") or os.getenv("WP_APP_PASSWORD") or "").strip()
    ok_creds = bool(base and user and apw)
    st.write(f"WordPress: {'OK' if ok_creds else 'Missing creds'} - {base or '(no base URL)'}")

    briefs = list_files_glob("briefs/*.yaml")
    brief_path = st.selectbox("Brief to publish", briefs, key="pub_brief")
    if brief_path:
        raw = read_text(brief_path)
        try:
            data = yaml.safe_load(raw) or {}
        except Exception:
            data = {}
        current_status = ((data.get('publish') or {}).get('status')) or 'draft'
        slug = data.get('slug') or '(unknown)'
        st.write(f"Slug: {slug}")
        col1, col2, col3 = st.columns([1,1,2])
        with col1:
            status = st.selectbox("Status", ["draft", "publish", "future"], index=["draft","publish","future"].index(current_status), key="pub_status")
        with col2:
            regen = st.checkbox("Regenerate before publish", value=True, key="pub_regen")
        with col3:
            schedule = st.checkbox("Schedule (set date/time)", value=(current_status=="future"), key="pub_sched")
        pub_date_iso = None
        if schedule:
            d = st.date_input("Date", key="pub_date")
            t = st.time_input("Time", key="pub_time")
            try:
                pub_date_iso = f"{d.isoformat()}T{t.strftime('%H:%M:%S')}"
            except Exception:
                pub_date_iso = None

        st.caption("Dry run skips WordPress publish; Publish writes a draft/publish/future post via REST.")
        cols = st.columns(2)
        with cols[0]:
            if st.button("Dry Run (Skip Publish)", key="btn_pub_dry"):
                # Ensure brief has chosen status/date even in dry run (for parity)
                try:
                    data.setdefault('publish', {})['status'] = status
                    if pub_date_iso:
                        data['publish']['date'] = pub_date_iso
                    # Save
                    write_text(brief_path, yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
                except Exception:
                    pass
                with st.status("Running dry run...", expanded=True):
                    env = {"SKIP_PUBLISH":"1"}
                    for line in run_cmd([os.sys.executable, "-m", "engine.run", brief_path], env=env):
                        st.write(line)
                st.success("Dry run complete. Check Preview tab.")
        with cols[1]:
            disabled = not ok_creds
            if st.button("Publish", key="btn_pub_real", disabled=disabled):
                if not ok_creds:
                    st.error("WordPress credentials missing in .env")
                else:
                    # Update brief publish fields
                    try:
                        data.setdefault('publish', {})['status'] = status
                        # Remove skip if present
                        if 'skip' in data['publish']:
                            data['publish'].pop('skip', None)
                        if pub_date_iso:
                            data['publish']['date'] = pub_date_iso
                        write_text(brief_path, yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
                    except Exception:
                        pass
                    with st.status("Publishing...", expanded=True):
                        for line in run_cmd([os.sys.executable, "-m", "engine.run", brief_path]):
                            st.write(line)
                    # Try to show publish result
                    meta_dir = os.path.join("artifacts", slug or "", "meta")
                    pub_json = os.path.join(meta_dir, "publish.json")
                    err_json = os.path.join(meta_dir, "publish_error.json")
                    _time.sleep(0.5)
                    if os.path.exists(pub_json):
                        try:
                            st.subheader("Publish Result")
                            st.code(read_text(pub_json))
                        except Exception:
                            pass
                    elif os.path.exists(err_json):
                        st.subheader("Publish Error")
                        st.code(read_text(err_json))
                    else:
                        st.info("No publish meta found; check logs above.")
    st.markdown('</div>', unsafe_allow_html=True)


def section_settings():
    st.header("Settings (.env)")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    kv, raw_lines = load_env_preserve_comments(".env")
    edited: Dict[str, str] = {}
    cols = st.columns(2)
    with cols[0]:
        st.subheader("Runtime")
        edited["OLLAMA_URL"] = st.text_input("OLLAMA_URL", value=kv.get("OLLAMA_URL", "http://localhost:11434"), key="env_OLLAMA_URL")
        installed_models = cached_ollama_models(edited["OLLAMA_URL"])
        edited["GEN_MODEL"] = st.text_input("GEN_MODEL", value=kv.get("GEN_MODEL", "phi3:mini-128k"), key="env_GEN_MODEL")
        if installed_models:
            try:
                idx = installed_models.index(edited["GEN_MODEL"]) + 1
            except ValueError:
                idx = 0
            choice = st.selectbox(
                "Installed models (/api/tags)",
                options=["(keep typed)"] + installed_models,
                index=idx,
                key="env_GEN_MODEL_installed",
                help="Pick a pulled model (e.g., phi3:mini-128k) to overwrite GEN_MODEL."
            )
            if choice != "(keep typed)":
                edited["GEN_MODEL"] = choice
                st.session_state.env_GEN_MODEL = choice
        edited["GEN_MODEL_FALLBACK"] = st.text_input(
            "GEN_MODEL_FALLBACK (optional)",
            value=kv.get("GEN_MODEL_FALLBACK", "phi3:mini-128k"),
            key="env_GEN_MODEL_FALLBACK",
            help="Used when the primary model is missing or OOMs; keep phi3 for long-context rescue."
        )
        edited["GEN_MODEL_CANDIDATES"] = st.text_input("GEN_MODEL_CANDIDATES (comma-separated)", value=kv.get("GEN_MODEL_CANDIDATES", ""), key="env_GEN_MODEL_CANDIDATES")
        temp_val = float(kv.get("GEN_TEMPERATURE", "0.0") or 0.0)
        edited["GEN_TEMPERATURE"] = f"{st.slider('GEN_TEMPERATURE', min_value=0.0, max_value=1.0, step=0.05, value=temp_val, key='env_GEN_TEMPERATURE'):.2f}"
        seed_val = int(kv.get("GEN_SEED", "42") or 42)
        edited["GEN_SEED"] = str(st.number_input("GEN_SEED", min_value=0, value=seed_val, step=1, key="env_GEN_SEED"))
        edited["GEN_MAX_CTX"] = st.text_input("GEN_MAX_CTX", value=kv.get("GEN_MAX_CTX", "120000"), key="env_GEN_MAX_CTX")
        max_pred_val = int(kv.get("GEN_MAX_PREDICT", "3200") or 3200)
        max_pred_val = min(8192, max(512, max_pred_val))
        edited["GEN_MAX_PREDICT"] = str(st.slider("GEN_MAX_PREDICT", min_value=512, max_value=8192, step=128, value=max_pred_val, key="env_GEN_MAX_PREDICT"))
        st.subheader("Retrieval")
        rk_val = int(kv.get("RETRIEVE_K", "8") or 8)
        edited["RETRIEVE_K"] = str(st.slider("RETRIEVE_K", min_value=1, max_value=15, value=rk_val, step=1, key="env_RETRIEVE_K"))
        rps_val = int(kv.get("RETRIEVE_MAX_PER_SOURCE", "1") or 1)
        edited["RETRIEVE_MAX_PER_SOURCE"] = str(st.slider("RETRIEVE_MAX_PER_SOURCE", min_value=1, max_value=5, value=rps_val, step=1, key="env_RETRIEVE_MAX_PER_SOURCE"))
    with cols[1]:
        st.subheader("WordPress")
        edited["WP_BASE_URL"] = st.text_input("WP_BASE_URL", value=kv.get("WP_BASE_URL", ""), key="env_WP_BASE_URL")
        edited["WP_USER"] = st.text_input("WP_USER", value=kv.get("WP_USER", ""), key="env_WP_USER")
        edited["WP_APP_PASSWORD"] = st.text_input("WP_APP_PASSWORD", value=kv.get("WP_APP_PASSWORD", ""), type="password", key="env_WP_APP_PASSWORD")
        st.subheader("Vector DB")
        vdb_default = kv.get("VDB_BACKEND", "qdrant")
        vdb_backend_value = st.text_input(
            "VDB_BACKEND",
            value=vdb_default,
            key="env_VDB_BACKEND",
            help="Use 'qdrant' for the local API server (recommended) or 'chroma' for in-process fallback."
        ).strip() or "qdrant"
        edited["VDB_BACKEND"] = vdb_backend_value
        if vdb_backend_value.lower() == "qdrant":
            edited["QDRANT_URL"] = st.text_input(
                "QDRANT_URL",
                value=kv.get("QDRANT_URL", "http://localhost:6333"),
                key="env_QDRANT_URL",
                help="Run `make up-qdrant` or start the native binary, then point to http://localhost:6333."
            )
            edited["QDRANT_COLLECTION"] = st.text_input(
                "QDRANT_COLLECTION",
                value=kv.get("QDRANT_COLLECTION", "content"),
                key="env_QDRANT_COLLECTION"
            )
            edited["QDRANT_API_KEY"] = st.text_input(
                "QDRANT_API_KEY (optional)",
                value=kv.get("QDRANT_API_KEY", ""),
                key="env_QDRANT_API_KEY",
                type="password"
            )
        else:
            edited["DB_DIR"] = st.text_input(
                "DB_DIR",
                value=kv.get("DB_DIR", "engine/.chroma"),
                key="env_DB_DIR",
                help="Filesystem location for Chroma storage."
            )
            edited["CHROMA_COLLECTION"] = st.text_input(
                "CHROMA_COLLECTION",
                value=kv.get("CHROMA_COLLECTION", "content"),
                key="env_CHROMA_COLLECTION"
            )
        st.subheader("Persona Defaults")
        persona_default = (kv.get("GEN_PERSONA", "") or "").strip()
        persona_options = ["", "founder", "pm", "content", "sme"]
        try:
            idx = persona_options.index(persona_default)
        except ValueError:
            idx = 0
        chosen_persona = st.selectbox("GEN_PERSONA (optional)", persona_options, index=idx, key="env_GEN_PERSONA_select")
        edited["GEN_PERSONA"] = chosen_persona
    st.subheader("Section Min Lengths (characters)")
    cmin1, cmin2, cmin3 = st.columns(3)
    with cmin1:
        edited["MINLEN_OVERVIEW"] = st.text_input("Overview", value=kv.get("MINLEN_OVERVIEW", "180"), key="env_MINLEN_OVERVIEW")
        edited["MINLEN_WHY_IT_MATTERS"] = st.text_input("Why It Matters", value=kv.get("MINLEN_WHY_IT_MATTERS", "160"), key="env_MINLEN_WHY")
        edited["MINLEN_PREREQUISITES"] = st.text_input("Prerequisites", value=kv.get("MINLEN_PREREQUISITES", "140"), key="env_MINLEN_PRE")
    with cmin2:
        edited["MINLEN_STEPS"] = st.text_input("Steps", value=kv.get("MINLEN_STEPS", "200"), key="env_MINLEN_STEPS")
        edited["MINLEN_EXAMPLES"] = st.text_input("Examples", value=kv.get("MINLEN_EXAMPLES", "140"), key="env_MINLEN_EX")
        edited["MINLEN_FAQS"] = st.text_input("FAQs", value=kv.get("MINLEN_FAQS", "120"), key="env_MINLEN_FAQS")
    with cmin3:
        edited["MINLEN_REFERENCES"] = st.text_input("References", value=kv.get("MINLEN_REFERENCES", "10"), key="env_MINLEN_REF")

    if st.button("Save .env", key="btn_save_env"):
        save_env_preserve_comments(edited, raw_lines, WHITELIST_ENV_KEYS, path=".env")
        st.success("Saved .env (backup created).")

    st.divider()
    st.subheader("Connectivity Checks")
    o_url = edited.get("OLLAMA_URL") or kv.get("OLLAMA_URL") or "http://localhost:11434"
    ok, msg = check_ollama(o_url)
    st.write(f"Ollama: {'OK' if ok else 'Fail'} - {msg[:200]}")
    if edited.get("WP_BASE_URL") or kv.get("WP_BASE_URL"):
        w_url = edited.get("WP_BASE_URL") or kv.get("WP_BASE_URL")
        wok, wmsg = check_wordpress(w_url)
        st.write(f"WordPress: {'OK' if wok else 'Fail'} - {wmsg[:200]}")
    st.markdown('</div>', unsafe_allow_html=True)


def section_lora():
    st.header("LoRA")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if st.button("Build Dataset from Artifacts", key="btn_build_lora_dataset"):
        with st.status("Building dataset...", expanded=True) as s:
            for line in run_cmd([os.sys.executable, "tools/lora/build_dataset.py"]):
                st.write(line)
        st.success("Dataset built")
    # Show counts
    sec_path = "data/lora/sections.jsonl"
    post_path = "data/lora/posts.jsonl"
    def _count_lines(p: str) -> int:
        try:
            with open(p, "r", encoding="utf-8") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
    st.write(f"Sections: {_count_lines(sec_path)} | Posts: {_count_lines(post_path)}")
    st.info("Train on a GPU box using tools/lora/trl_sft_template.py and register the model in Ollama.")

    st.subheader("Add Samples (Manual)")
    mode = st.radio("Sample Type", ["Section", "Post", "Upload JSONL", "Upload .md"], horizontal=True, key="lora_sample_mode")
    personas = ["", "founder", "pm", "content", "sme"]
    if mode == "Section":
        sec_prefill = st.selectbox(
            "Section templates",
            options=["Manual entry"] + [p["label"] for p in LORA_SECTION_PRESETS],
            index=0,
            key="lora_sec_prefill_choice",
            help="Drop in a starter snippet to see the expected structure."
        )
        if sec_prefill != "Manual entry":
            preset = next(p for p in LORA_SECTION_PRESETS if p["label"] == sec_prefill)
            st.session_state.lora_sec_title = preset["title"]
            st.session_state.lora_sec_h2 = preset["h2"]
            st.session_state.lora_sec_persona = preset["persona"]
            st.session_state.lora_sec_body = preset["body"]
            st.session_state.lora_sec_prefill_choice = "Manual entry"
        c1, c2, c3 = st.columns(3)
        with c1:
            sec_title = st.text_input(
                "Post Title",
                value=st.session_state.get("lora_sec_title", ""),
                key="lora_sec_title",
                placeholder="Docs-as-Code Governance Checklist for SMBs"
            )
        with c2:
            sec_h2 = st.text_input(
                "Section (H2)",
                value=st.session_state.get("lora_sec_h2", "Overview"),
                key="lora_sec_h2",
                placeholder="Overview"
            )
        with c3:
            sec_persona = st.selectbox("Persona", personas, index=0, key="lora_sec_persona")
        sec_body = st.text_area(
            "Section Body (Markdown, no heading)",
            height=200,
            key="lora_sec_body",
            placeholder="Explain the section in short sentences and bullet points."
        )
        if st.button("Add Section Sample", key="btn_add_section_sample"):
            if sec_title and sec_h2 and sec_body.strip():
                # Validate sample
                errs = []
                import re as _re
                if _re.search(r"^(Document:|Your task:|I\'m sorry|In a hypothet)", sec_body, flags=_re.I | _re.M):
                    errs.append("Meta artifacts detected")
                # sentence length check
                sentences = [s.strip() for s in _re.split(r"(?<=[\.!?])\s+", sec_body) if s.strip()]
                if sentences:
                    max_words = max(len(s.split()) for s in sentences)
                    if max_words > 28:
                        errs.append(f"Long sentence detected (max {max_words} words)")
                if errs:
                    st.error("; ".join(errs))
                else:
                    ctrl = f"[persona={sec_persona}] " if sec_persona else ""
                    instr = (f"{ctrl}Write ONLY the body for the section '{sec_h2}' for a post titled '{sec_title}'. "
                             "No heading in the output. Short sentences; use bullets for steps.")
                    append_jsonl(sec_path, {"instruction": instr, "output": sec_body.strip()})
                    st.success("Section sample appended to data/lora/sections.jsonl")
            else:
                st.warning("Please fill title, section, and body.")
    elif mode == "Post":
        post_prefill = st.selectbox(
            "Post templates",
            options=["Manual entry"] + [p["label"] for p in LORA_POST_PRESETS],
            index=0,
            key="lora_post_prefill_choice",
            help="Use a prefab example to understand structure expectations."
        )
        if post_prefill != "Manual entry":
            preset = next(p for p in LORA_POST_PRESETS if p["label"] == post_prefill)
            st.session_state.lora_post_title = preset["title"]
            st.session_state.lora_post_persona = preset["persona"]
            st.session_state.lora_post_body = preset["body"]
            st.session_state.lora_post_prefill_choice = "Manual entry"
        pcols = st.columns(2)
        with pcols[0]:
            p_title = st.text_input(
                "Post Title",
                value=st.session_state.get("lora_post_title", ""),
                key="lora_post_title",
                placeholder="AI Content Governance Playbook for SMB Teams"
            )
        with pcols[1]:
            p_persona = st.selectbox("Persona", personas, index=0, key="lora_post_persona")
        p_body = st.text_area(
            "Post Body (full Markdown)",
            height=240,
            key="lora_post_body",
            placeholder="Include Overview, Why It Matters, Prerequisites, Steps, Examples, FAQs, and References sections."
        )
        if st.button("Add Post Sample", key="btn_add_post_sample"):
            if p_title and p_body.strip():
                # Validate sample
                errs = []
                import re as _re
                if _re.search(r"^(Document:|Your task:|I\'m sorry|In a hypothet)", p_body, flags=_re.I | _re.M):
                    errs.append("Meta artifacts detected")
                sentences = [s.strip() for s in _re.split(r"(?<=[\.!?])\s+", p_body) if s.strip()]
                if sentences:
                    max_words = max(len(s.split()) for s in sentences)
                    if max_words > 32:
                        errs.append(f"Long sentence detected (max {max_words} words)")
                if errs:
                    st.error("; ".join(errs))
                else:
                    ctrl = f"[persona={p_persona}] " if p_persona else ""
                    instr = (f"{ctrl}Write a clear, helpful blog post with the title '{p_title}'. "
                             "Use H2 sections: Overview, Why It Matters, Prerequisites, Steps, Examples, FAQs, References. "
                             "Use short sentences and bullet points for steps.")
                    append_jsonl(post_path, {"instruction": instr, "output": p_body.strip()})
                    st.success("Post sample appended to data/lora/posts.jsonl")
            else:
                st.warning("Please fill title and body.")
    elif mode == "Upload JSONL":
        target = st.selectbox("Target Dataset", ["sections.jsonl", "posts.jsonl"], key="lora_jsonl_target")
        upj = st.file_uploader("Upload JSONL (instruction, output)", type=["jsonl"], key="lora_jsonl_upload")
        if upj and st.button("Append JSONL", key="btn_append_jsonl"):
            import json as _json
            path = sec_path if target == "sections.jsonl" else post_path
            lines = upj.read().decode("utf-8").splitlines()
            ok, fail = 0, 0
            for ln in lines:
                try:
                    rec = _json.loads(ln)
                    if isinstance(rec, dict) and rec.get("instruction") and rec.get("output"):
                        # Validate output
                        import re as _re
                        out = str(rec.get("output"))
                        bad = _re.search(r"^(Document:|Your task:|I\'m sorry|In a hypothet)", out, flags=_re.I | _re.M)
                        sentences = [s.strip() for s in _re.split(r"(?<=[\.!?])\s+", out) if s.strip()]
                        too_long = False
                        if sentences:
                            too_long = max(len(s.split()) for s in sentences) > 40
                        if bad or too_long:
                            fail += 1
                        else:
                            append_jsonl(path, rec)
                            ok += 1
                    else:
                        fail += 1
                except Exception:
                    fail += 1
            st.success(f"Appended {ok} record(s). Skipped {fail}.")
    elif mode == "Upload .md":
        md_files = st.file_uploader("Upload Markdown files", type=["md"], accept_multiple_files=True, key="lora_md_upload")
        cols = st.columns(2)
        with cols[0]:
            title_mode = st.selectbox("Title From", ["Filename", "H1"], key="lora_md_title_mode")
        with cols[1]:
            up_persona = st.selectbox("Persona (optional)", personas, index=0, key="lora_md_persona")
        if md_files and st.button("Convert to Post Samples", key="btn_md_to_posts"):
            import re as _re
            added = 0
            for f in md_files:
                txt = f.getvalue().decode("utf-8")
                # Validate
                errs = []
                if _re.search(r"^(Document:|Your task:|I\'m sorry|In a hypothet)", txt, flags=_re.I | _re.M):
                    errs.append("Meta artifacts detected")
                sentences = [s.strip() for s in _re.split(r"(?<=[\.!?])\s+", txt) if s.strip()]
                if sentences and max(len(s.split()) for s in sentences) > 40:
                    errs.append("Long sentence detected")
                if errs:
                    continue
                title = os.path.splitext(f.name)[0]
                if title_mode == "H1":
                    m = _re.search(r"^#\s+(.+)$", txt, flags=_re.M)
                    if m:
                        title = m.group(1).strip()
                if not title:
                    title = os.path.splitext(f.name)[0]
                ctrl = f"[persona={up_persona}] " if up_persona else ""
                instr = (f"{ctrl}Write a clear, helpful blog post with the title '{title}'. "
                         "Use H2 sections: Overview, Why It Matters, Prerequisites, Steps, Examples, FAQs, References. "
                         "Use short sentences and bullet points for steps.")
                append_jsonl(post_path, {"instruction": instr, "output": txt.strip()})
                added += 1
            st.success(f"Converted and appended {added} post sample(s).")
    st.markdown('</div>', unsafe_allow_html=True)


def section_brief_builder():
    st.header("Brief Builder")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    styles = [os.path.splitext(os.path.basename(p))[0] for p in list_files_glob("engine/styles/**/*.md")]
    if not styles:
        styles = ["default"]
    default_style = "pruningmypothos" if "pruningmypothos" in styles else styles[0]

    existing_briefs = list_files_glob("briefs/*.yaml")
    existing_options = ["(new brief)"] + existing_briefs
    import yaml as _yaml
    parsed_briefs: Dict[str, Dict[str, Any]] = {}
    for _path in existing_briefs:
        try:
            parsed_briefs[_path] = _yaml.safe_load(read_text(_path)) or {}
        except Exception:
            parsed_briefs[_path] = {}

    st.session_state.setdefault("brief_existing_select", "(new brief)")
    st.session_state.setdefault("brief_loaded_from", "")
    st.session_state.setdefault("brief_title", "")
    st.session_state.setdefault("brief_slug", "")
    st.session_state.setdefault("brief_tags", "docs-as-code,smbs,governance")
    st.session_state.setdefault("brief_persona", "")
    st.session_state.setdefault("brief_blog_mode", True)
    st.session_state.setdefault("brief_planner", True)
    st.session_state.setdefault("brief_no_external", True)
    st.session_state.setdefault("brief_allowed_domains", "pruningmypothos.com")
    st.session_state.setdefault("brief_outputs", ["blog", "linkedin"])
    st.session_state.setdefault("brief_publish_status", "draft")
    if st.session_state.get("brief_style_profile") not in styles:
        st.session_state["brief_style_profile"] = default_style
    st.session_state.setdefault("brief_prefill_select", "Manual entry")
    st.session_state.setdefault("brief_prefill_last_applied", "")
    st.session_state.setdefault("brief_prefill_pending", None)
    if "brief_allowed_domain_list" not in st.session_state:
        default_allow = [d.strip() for d in st.session_state.get("brief_allowed_domains", "pruningmypothos.com").splitlines() if d.strip()]
        st.session_state.brief_allowed_domain_list = default_allow or ["pruningmypothos.com"]
    if "brief_block_domain_list" not in st.session_state:
        st.session_state.brief_block_domain_list = []
    st.session_state.setdefault("brief_allow_new", "")
    st.session_state.setdefault("brief_block_new", "")

    def _ensure_unique_state_list(key: str) -> None:
        vals = [str(d).strip() for d in st.session_state.get(key, []) if str(d).strip()]
        st.session_state[key] = list(dict.fromkeys(vals))

    def _add_allowed_domain() -> None:
        new_dom = (st.session_state.get("brief_allow_new") or "").strip()
        if new_dom:
            st.session_state.brief_allowed_domain_list.append(new_dom)
        _ensure_unique_state_list("brief_allowed_domain_list")
        st.session_state.brief_allow_new = ""

    def _add_block_domain() -> None:
        new_dom = (st.session_state.get("brief_block_new") or "").strip()
        if new_dom:
            st.session_state.brief_block_domain_list.append(new_dom)
        _ensure_unique_state_list("brief_block_domain_list")
        st.session_state.brief_block_new = ""

    if existing_options:
        selected_existing = st.selectbox(
            "Start from existing brief",
            options=existing_options,
            index=existing_options.index(st.session_state.get("brief_existing_select", "(new brief)")) if st.session_state.get("brief_existing_select", "(new brief)") in existing_options else 0,
            key="brief_existing_select",
            help="Load fields from an existing brief to tweak and resave."
        )
    else:
        selected_existing = "(new brief)"

    if selected_existing != "(new brief)" and st.session_state.get("brief_loaded_from") != selected_existing:
        st.session_state.brief_load_pending = selected_existing
        st.session_state.brief_loaded_from = selected_existing
    elif selected_existing == "(new brief)" and st.session_state.get("brief_loaded_from"):
        st.session_state.brief_loaded_from = ""

    load_pending = st.session_state.pop("brief_load_pending", None)
    if load_pending:
        try:
            data = parsed_briefs.get(load_pending, {})
            st.session_state.brief_title = data.get("title", "")
            st.session_state.brief_slug = data.get("slug", "")
            tags_data = data.get("tags", [])
            if isinstance(tags_data, list):
                st.session_state.brief_tags = ",".join(str(t) for t in tags_data if t)
            elif isinstance(tags_data, str):
                st.session_state.brief_tags = tags_data
            st.session_state.brief_persona = data.get("persona", "")
            if data.get("blog_mode") is not None:
                st.session_state.brief_blog_mode = data.get("blog_mode") == "sectional"
            if data.get("planner") is not None:
                st.session_state.brief_planner = data.get("planner") == "outline"
            st.session_state.brief_no_external = bool(data.get("no_external", st.session_state.brief_no_external))
            allowed_domains = []
            sources = data.get("sources") or {}
            if isinstance(sources, dict):
                allowed_domains = sources.get("allow", []) or []
            st.session_state.brief_allowed_domain_list = [str(d).strip() for d in allowed_domains if str(d).strip()]
            st.session_state.brief_allowed_domains = "\n".join(st.session_state.brief_allowed_domain_list)
            block_domains = []
            if isinstance(sources, dict):
                block_domains = sources.get("block", []) or []
            st.session_state.brief_block_domain_list = [str(d).strip() for d in block_domains if str(d).strip()]
            outputs_data = data.get("outputs", st.session_state.get("brief_outputs", ["blog", "linkedin"]))
            if isinstance(outputs_data, list):
                st.session_state.brief_outputs = outputs_data
            publish_data = data.get("publish") or {}
            st.session_state.brief_publish_status = publish_data.get("status", "draft")
            if data.get("style_profile") in styles:
                st.session_state.brief_style_profile = data.get("style_profile")
        except Exception:
            pass

    template_labels = ["Manual entry"] + [t["label"] for t in BRIEF_TEMPLATE_HINTS]
    prefill_choice = st.selectbox(
        "Starter templates",
        options=template_labels,
        index=template_labels.index(st.session_state.get("brief_prefill_select", "Manual entry")) if st.session_state.get("brief_prefill_select", "Manual entry") in template_labels else 0,
        key="brief_prefill_select",
        help="Autofill the brief with a proven configuration."
    )
    if prefill_choice != "Manual entry" and st.session_state.get("brief_prefill_last_applied") != prefill_choice:
        st.session_state.brief_prefill_pending = prefill_choice
        st.session_state.brief_prefill_last_applied = prefill_choice
    elif prefill_choice == "Manual entry" and st.session_state.get("brief_prefill_last_applied"):
        st.session_state.brief_prefill_last_applied = ""
    pending_prefill = st.session_state.pop("brief_prefill_pending", None)
    if pending_prefill:
        template = next(t for t in BRIEF_TEMPLATE_HINTS if t["label"] == pending_prefill)
        st.session_state.brief_title = template["title"]
        st.session_state.brief_slug = template["slug"]
        st.session_state.brief_tags = template["tags"]
        st.session_state.brief_persona = template.get("persona", "")
        st.session_state.brief_blog_mode = template.get("blog_mode", True)
        st.session_state.brief_planner = template.get("planner", True)
        st.session_state.brief_no_external = template.get("no_external", True)
        allowed_val = template.get("allowed", st.session_state.get("brief_allowed_domains", ""))
        if isinstance(allowed_val, str):
            allow_list = [d.strip() for d in allowed_val.splitlines() if d.strip()]
        elif isinstance(allowed_val, list):
            allow_list = [str(d).strip() for d in allowed_val if str(d).strip()]
        else:
            allow_list = []
        st.session_state.brief_allowed_domain_list = allow_list or st.session_state.brief_allowed_domain_list
        st.session_state.brief_allowed_domains = "\n".join(st.session_state.brief_allowed_domain_list)
        block_val = template.get("blocked", template.get("block", []))
        if isinstance(block_val, str):
            block_list = [d.strip() for d in block_val.splitlines() if d.strip()]
        elif isinstance(block_val, list):
            block_list = [str(d).strip() for d in block_val if str(d).strip()]
        else:
            block_list = []
        st.session_state.brief_block_domain_list = block_list
        st.session_state.brief_outputs = template.get("outputs", st.session_state.get("brief_outputs", ["blog", "linkedin"]))
        st.session_state.brief_publish_status = template.get("publish_status", "draft")
        desired_style = template.get("style_profile")
        if desired_style and desired_style in styles:
            st.session_state.brief_style_profile = desired_style
        else:
            st.session_state.brief_style_profile = default_style

    _ensure_unique_state_list("brief_allowed_domain_list")
    _ensure_unique_state_list("brief_block_domain_list")

    def _slugify(text: str) -> str:
        import re as _re
        base = (text or "").strip().lower()
        base = _re.sub(r"[^a-z0-9]+", "-", base).strip("-")
        return base or "new-brief"

    title = st.text_input(
        "Title",
        value=st.session_state.get("brief_title", ""),
        key="brief_title",
        placeholder="Docs-as-Code Governance Checklist for SMBs",
        help="Headline for the content brief."
    )
    slug_col, slug_btn_col = st.columns([3, 1])
    with slug_btn_col:
        if st.button("Auto slug", key="brief_slug_auto"):
            st.session_state.brief_slug = _slugify(st.session_state.get("brief_title", ""))
    with slug_col:
        slug = st.text_input(
            "Slug",
            value=st.session_state.get("brief_slug", ""),
            key="brief_slug",
            placeholder="docs-as-code-governance-checklist",
            help="Used for artifact folders - lowercase, dash-separated."
        )

    tags = st.text_input(
        "Tags (comma-separated)",
        value=st.session_state.get("brief_tags", ""),
        key="brief_tags",
        placeholder="docs-as-code,governance,smbs",
        help="Helps with filtering and content routing."
    )

    tag_suggestions: set[str] = set()
    for data in parsed_briefs.values():
        tags_data = data.get("tags", [])
        if isinstance(tags_data, str):
            tags_data = [tags_data]
        for t in tags_data or []:
            if isinstance(t, str) and t.strip():
                tag_suggestions.add(t.strip())
    sorted_tags = sorted(tag_suggestions, key=lambda x: x.lower())
    if sorted_tags:
        selected_tag_suggestions = st.multiselect(
            "Quick tag add",
            options=sorted_tags,
            key="brief_tag_suggestions",
            help="Select tags to append to the list above."
        )
        if selected_tag_suggestions and st.button("Add selected tags", key="brief_add_tags"):
            current = [t.strip() for t in tags.split(",") if t.strip()]
            combined = current + [t for t in selected_tag_suggestions if t not in current]
            st.session_state.brief_tags = ",".join(combined)
            tags = st.session_state.brief_tags

    with st.expander("Sources & Constraints", expanded=False):
        allow_suggestions: set[str] = set()
        block_suggestions: set[str] = set()
        for data in parsed_briefs.values():
            sources = data.get("sources") or {}
            if isinstance(sources, dict):
                for dom in sources.get("allow", []) or []:
                    if isinstance(dom, str) and dom.strip():
                        allow_suggestions.add(dom.strip())
                for dom in sources.get("block", []) or []:
                    if isinstance(dom, str) and dom.strip():
                        block_suggestions.add(dom.strip())

        allow_options = sorted(set(allow_suggestions).union(st.session_state.brief_allowed_domain_list), key=lambda x: x.lower())
        allow_input_col, allow_btn_col = st.columns([3, 1])
        with allow_input_col:
            st.text_input("Add allowed domain", key="brief_allow_new", placeholder="example.com")
        with allow_btn_col:
            st.button("Add", key="brief_allow_add_btn", on_click=_add_allowed_domain)
        st.multiselect(
            "Allowed Domains",
            options=allow_options,
            key="brief_allowed_domain_list",
            help="Domains the generator can cite in References."
        )

        block_options = sorted(set(block_suggestions).union(st.session_state.brief_block_domain_list), key=lambda x: x.lower())
        block_input_col, block_btn_col = st.columns([3, 1])
        with block_input_col:
            st.text_input("Add blocked domain", key="brief_block_new", placeholder="competitor.com")
        with block_btn_col:
            st.button("Add", key="brief_block_add_btn", on_click=_add_block_domain)
        st.multiselect(
            "Blocked Domains",
            options=block_options,
            key="brief_block_domain_list",
            help="Domains to avoid in the final references/output."
        )

    st.session_state.brief_allowed_domains = "\n".join(st.session_state.brief_allowed_domain_list)

    with st.expander("Configuration & Output", expanded=True):
        c_cfg1, c_cfg2 = st.columns(2)
        with c_cfg1:
            persona_options = ["", "founder", "pm", "content", "sme"]
            persona_default = st.session_state.get("brief_persona", "")
            persona_index = persona_options.index(persona_default) if persona_default in persona_options else 0
            persona_bb = st.selectbox(
                "Persona",
                persona_options,
                index=persona_index,
                key="brief_persona",
                help="Optional default voice for the generated content."
            )
        with c_cfg2:
            style_value = st.session_state.get("brief_style_profile", default_style)
            if style_value not in styles:
                style_value = default_style
            style_profile = st.selectbox(
                "Style Profile",
                options=styles,
                index=styles.index(style_value),
                key="brief_style_profile",
                help="Pick the tone/style guide markdown to apply."
            )

        c_chk1, c_chk2, c_chk3 = st.columns(3)
        with c_chk1:
            blog_mode = st.checkbox("Sectional Mode", key="brief_blog_mode", help="Toggle sectional generation vs single narrative.")
        with c_chk2:
            planner = st.checkbox("Outline Planner", key="brief_planner", help="Request an outline planner step before drafting.")
        with c_chk3:
            no_external = st.checkbox("No External Links", key="brief_no_external", help="Force the draft to avoid linking outside the allowlist.")

        outputs = st.multiselect(
            "Outputs",
            options=["blog", "linkedin", "instagram", "github_doc"],
            default=st.session_state.get("brief_outputs", ["blog", "linkedin"]),
            key="brief_outputs",
            help="Select which artifact bundles to generate."
        )
        status_options = ["draft", "publish", "future"]
        status_default = st.session_state.get("brief_publish_status", "draft")
        if status_default not in status_options:
            status_default = "draft"
        publish_status = st.selectbox(
            "Publish Status",
            options=status_options,
            index=status_options.index(status_default),
            key="brief_publish_status",
            help="Default WordPress status saved into the brief."
        )

    import yaml as _yaml
    allowed_list = [d.strip() for d in st.session_state.get("brief_allowed_domain_list", []) if d.strip()]
    allowed_list = list(dict.fromkeys(allowed_list))
    block_list = [d.strip() for d in st.session_state.get("brief_block_domain_list", []) if d.strip()]
    block_list = list(dict.fromkeys(block_list))
    sources_payload = {"allow": allowed_list.copy()}
    if block_list:
        sources_payload["block"] = block_list.copy()
    save_col, preview_col = st.columns([1, 3])
    with save_col:
        save_clicked = st.button("Create Brief", key="btn_create_brief")
    with preview_col:
        preview_payload = {
            "title": title,
            "slug": slug,
            "tags": [t.strip() for t in st.session_state.get("brief_tags", "").split(",") if t.strip()],
            "style_profile": style_profile,
            "blog_mode": "sectional" if blog_mode else None,
            "planner": "outline" if planner else None,
            "no_external": bool(no_external),
            "sources": sources_payload,
            "outputs": st.session_state.get("brief_outputs", ["blog", "linkedin"]),
            "publish": {"status": publish_status},
        }
        if persona_bb:
            preview_payload["persona"] = persona_bb
        preview_payload = {k: v for k, v in preview_payload.items() if v not in (None, [], {})}
        try:
            preview_yaml = _yaml.safe_dump(preview_payload, sort_keys=False, allow_unicode=True)
        except Exception:
            preview_yaml = ""
        st.code(preview_yaml or "# YAML preview", language="yaml")

    if save_clicked:
        if not title or not slug:
            st.warning("Title and slug are required")
        else:
            import yaml
            data = {
                "title": title,
                "slug": slug,
                "tags": [t.strip() for t in tags.split(",") if t.strip()],
                "style_profile": style_profile,
                "blog_mode": "sectional" if blog_mode else None,
                "planner": "outline" if planner else None,
                "no_external": bool(no_external),
                "sources": sources_payload,
                "outputs": outputs,
                "publish": {"status": publish_status},
            }
            if persona_bb:
                data["persona"] = persona_bb
            # remove None values
            data = {k: v for k, v in data.items() if v not in (None, [], {})}
            out_path = os.path.join("briefs", f"{slug}.yaml")
            with open(out_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
            st.success(f"Brief written: {out_path}")
    st.markdown('</div>', unsafe_allow_html=True)


tabs = st.tabs(["Ingest", "Index", "Generate", "Preview", "Publish", "Settings", "LoRA", "Brief Builder", "Chat"])
with tabs[0]:
    section_ingest()
with tabs[1]:
    section_index()
with tabs[2]:
    section_generate()
with tabs[3]:
    section_preview()
with tabs[4]:
    section_publish()
with tabs[5]:
    section_settings()
with tabs[6]:
    section_lora()
with tabs[7]:
    section_brief_builder()
with tabs[8]:
    # --- Chat + Scratchpad ---
    st.header("Chat + Scratchpad")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    # Inline connectivity indicator
    o_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ok_ollama, msg_ollama = check_ollama(o_url)
    st.caption(f"Ollama: {'OK' if ok_ollama else 'Fail'} - {str(msg_ollama)[:200]}")

    # Controls
    colA, colB, colC, colD = st.columns([2,1,1,1])
    with colA:
        chat_model = st.text_input("Model (comma-separated to try multiple)", value=_default_model(), key="chat_model")
    with colB:
        chat_temp_default = float(os.getenv("GEN_TEMPERATURE", "0.3"))
        chat_temp = st.slider("Temperature", min_value=0.0, max_value=1.0, value=chat_temp_default, step=0.05, key="chat_temp")
    with colC:
        chat_persona = st.selectbox("Persona", ["", "founder", "pm", "content", "sme"], index=0, key="chat_persona")
    with colD:
        chat_k = st.slider("Top-K", min_value=0, max_value=20, value=6, step=1, key="chat_k")
    c2a, c2b = st.columns([1,1])
    with c2a:
        chat_stream = st.checkbox("Stream tokens", value=True, key="chat_stream")
    with c2b:
        chat_timeout = st.slider("HTTP Timeout (s)", min_value=30, max_value=1800, value=int(os.getenv("CHAT_HTTP_TIMEOUT", "300")), step=30, key="chat_timeout")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    import requests
    from engine.rag.search import retrieve as rag_retrieve
    from engine.tools.html import md_to_clean_html as _md2html

    def ollama_chat(prompt: str, model: str, temp: float = 0.0, persona: str = "", system: str = "", *, timeout_s: int = 300) -> str:
        base = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
        controls = f"[persona={persona}] " if persona else ""
        # Support trying multiple models: "m1, m2, m3"
        models = [m.strip() for m in (model or "").split(",") if m.strip()] or [model]
        last_err = None
        for m in models:
            try:
                body = {
                    "model": m,
                    "messages": ([{"role": "system", "content": system}] if system else []) + [
                        {"role": "user", "content": controls + prompt}
                    ],
                    "stream": False,
                    "options": {"temperature": float(temp)},
                }
                r = requests.post(base + "/api/chat", json=body, timeout=timeout_s)
                if r.status_code == 404:
                    # Fallback to generate API if chat is unsupported
                    gen_prompt = (system + "\n\n" if system else "") + controls + prompt
                    gen_body = {"model": m, "prompt": gen_prompt, "stream": False, "options": {"temperature": float(temp)}}
                    rg = requests.post(base + "/api/generate", json=gen_body, timeout=timeout_s)
                    rg.raise_for_status()
                    data_g = rg.json()
                    return data_g.get("response", "")
                r.raise_for_status()
                data = r.json()
                if isinstance(data, dict) and data.get("message"):
                    return data["message"].get("content", "")
                if isinstance(data, dict) and data.get("messages"):
                    parts = [mx.get("content", "") for mx in data["messages"] if isinstance(mx, dict)]
                    return "\n".join([p for p in parts if p]).strip()
                return ""
            except Exception as e:
                last_err = e
                continue
        raise RuntimeError(f"All chat attempts failed for models {models}: {last_err}")

    def ollama_chat_stream(prompt: str, model: str, temp: float = 0.0, persona: str = "", *, timeout_s: int = 300):
        base = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
        controls = f"[persona={persona}] " if persona else ""
        models = [m.strip() for m in (model or "").split(",") if m.strip()] or [model]
        last_err = None
        for m in models:
            try:
                body = {
                    "model": m,
                    "messages": [{"role": "user", "content": controls + prompt}],
                    "stream": True,
                    "options": {"temperature": float(temp)},
                }
                with requests.post(base + "/api/chat", json=body, stream=True, timeout=timeout_s) as r:
                    if r.status_code == 404:
                        # Fallback to generate stream
                        gen_body = {"model": m, "prompt": controls + prompt, "stream": True, "options": {"temperature": float(temp)}}
                        with requests.post(base + "/api/generate", json=gen_body, stream=True, timeout=timeout_s) as rg:
                            rg.raise_for_status()
                            for line in rg.iter_lines(decode_unicode=True):
                                if not line:
                                    continue
                                try:
                                    data_g = json.loads(line)
                                except Exception:
                                    continue
                                piece = data_g.get("response", "") if isinstance(data_g, dict) else ""
                                if piece:
                                    yield piece
                            return
                    r.raise_for_status()
                    for line in r.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except Exception:
                            continue
                        piece = ""
                        if isinstance(data, dict):
                            if isinstance(data.get("message"), dict):
                                piece = data["message"].get("content", "")
                            elif "response" in data:
                                piece = data.get("response", "")
                        if piece:
                            yield piece
                    return
            except Exception as e:
                last_err = e
                continue
        raise RuntimeError(f"All chat attempts failed for models {models}: {last_err}")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    cols_chat = st.columns([4, 2, 1])
    with cols_chat[0]:
        st.markdown("### Chat")
    with cols_chat[1]:
        st.markdown(
            f"<div style='padding:6px 10px;border-radius:12px;border:1px solid rgba(15,23,42,0.08);background:rgba(14,165,233,0.08);display:inline-flex;gap:6px;align-items:center;'>"
            f"<span style='font-weight:600;'>Model:</span> {_default_model()}</div>",
            unsafe_allow_html=True,
        )
    with cols_chat[2]:
        if st.button("Clear chat", key="btn_clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

    # Form gives Cmd/Ctrl+Enter submit
    with st.form(key="chat_form"):
        q = st.text_area("Ask a question", height=120, placeholder="e.g., Draft a short 'Why It Matters' for docs-as-code governance.")
        use_retrieval = st.checkbox("Retrieve context (RAG)", value=True)
        submitted = st.form_submit_button("Send", disabled=not ok_ollama)
    if submitted and q.strip():
        st.session_state.chat_history.append({"role": "user", "content": q})
        ctx = ""
        sources = []
        if use_retrieval:
            ctx, sources = rag_retrieve(q, k=int(chat_k))
        if use_retrieval:
            system_prompt = (
                "You are a concise assistant. Answer directly in Markdown with no greetings or filler. "
                "Use only the provided context; if it is empty, say you have no supporting context. Keep answers short and clear."
            )
            prompt = (
                f"Context:\n{ctx}\n\nQuestion: {q}\n\nAnswer concisely in Markdown. "
                "If context is empty, state that no context was provided and give a brief general answer."
            )
            temp_eff = min(chat_temp, 0.4)
        else:
            system_prompt = (
                "You are a capable chat assistant. Stay on-topic, skip greetings, and answer in clear Markdown. "
                "Do not show analysis steps or internal reasoning. Provide helpful answers with short examples when useful. "
                "Keep responses under ~200 words unless asked otherwise."
            )
            prompt = f"User question: {q}\n\nRespond helpfully and clearly in Markdown. Do not include meta analysis or planning."
            temp_eff = chat_temp
        try:
            with st.spinner("Thinking..."):
                if chat_stream:
                    msg = st.chat_message("assistant")
                    placeholder = msg.empty()
                    acc = []
                    for chunk in ollama_chat_stream(prompt, chat_model, temp_eff, chat_persona, timeout_s=int(chat_timeout)):
                        acc.append(chunk)
                        placeholder.markdown("".join(acc))
                    ans = "".join(acc)
                else:
                    ans = ollama_chat(prompt, chat_model, temp_eff, chat_persona, system=system_prompt, timeout_s=int(chat_timeout))
        except Exception as e:
            ans = f"[error] {e}"
        st.session_state.chat_history.append({"role": "assistant", "content": ans, "sources": sources})

    # History display using chat bubbles
    for turn in st.session_state.chat_history[-20:]:
        role = turn.get("role", "assistant")
        msg = st.chat_message("user" if role == "user" else "assistant")
        msg.markdown(turn.get("content", ""))
        if role != "user" and turn.get("sources"):
            with msg.expander("Sources", expanded=False):
                for s in turn["sources"]:
                    st.code(str(s))
    st.markdown('</div>', unsafe_allow_html=True)
