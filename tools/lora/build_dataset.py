#!/usr/bin/env python3
"""
Builds LoRA SFT datasets from generated artifacts.
Outputs JSONL files under data/lora/ with records:
  {"instruction": "...", "output": "..."}

Two datasets are produced:
- sections.jsonl: per-H2 section bodies (preferred for stable style learning)
- posts.jsonl: full post body (single sample per artifact)

No external deps beyond repo requirements.
"""
import os
import re
import json
from glob import glob
import frontmatter

ART_DIR = "artifacts"
OUT_DIR = os.path.join("data", "lora")


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def split_sections(md: str):
    """Return list of (heading, body) for H2 sections.
    Expects a single H1 at top, then H2 sections.
    """
    parts = []
    # Normalize newlines
    text = md.strip()
    # Find all H2 headings
    matches = list(re.finditer(r"^##\s+(.+)$", text, flags=re.M))
    if not matches:
        return parts
    # Include content between H2s
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        heading = m.group(1).strip()
        body = text[start:end].strip().lstrip("\n")
        parts.append((heading, body))
    return parts


def clean_body(txt: str) -> str:
    # Remove meta artifacts that should not be learned
    bad = [r"^Document:\s*", r"^Your task:\s*", r"^I\'m sorry", r"^In a hypothet"]
    out = txt
    for pat in bad:
        out = re.sub(pat, "", out, flags=re.I | re.M)
    # Collapse excessive blank lines
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out


def main():
    ensure_dir(OUT_DIR)
    sec_out = open(os.path.join(OUT_DIR, "sections.jsonl"), "w", encoding="utf-8")
    post_out = open(os.path.join(OUT_DIR, "posts.jsonl"), "w", encoding="utf-8")
    n_sec = 0
    n_post = 0
    def infer_persona_from_path(path: str) -> str:
        import re as _re
        m = _re.search(r"persona=([A-Za-z0-9_\-]+)", path)
        return (m.group(1).lower() if m else "")

    for blog_md in glob(os.path.join(ART_DIR, "*", "blog", "draft.md")):
        try:
            with open(blog_md, "r", encoding="utf-8") as f:
                raw = f.read()
            post = frontmatter.loads(raw)
            title = post.get("title") or "Untitled"
            body = (post.content or "").strip()  # keep only the markdown body; drop front matter
            if not body:
                continue
            persona = (post.metadata or {}).get("persona") or infer_persona_from_path(blog_md)
            ctrl = f"[persona={persona}] " if persona else ""
            # Full post record
            instr = (
                f"{ctrl}Write a clear, helpful blog post with the title '{title}'. "
                "Use H2 sections: Overview, Why It Matters, Prerequisites, Steps, Examples, FAQs, References. "
                "Use short sentences and bullet points for steps."
            )
            out_rec = {"instruction": instr, "output": clean_body(body)}
            post_out.write(json.dumps(out_rec, ensure_ascii=False) + "\n")
            n_post += 1

            # Section records
            for h2, sec_body in split_sections(body):
                sec_body = clean_body(sec_body)
                if not sec_body:
                    continue
                sinstr = (
                    f"{ctrl}Write ONLY the body for the section '{h2}' for a post titled '{title}'. "
                    "No heading in the output. Short sentences; use bullets for steps."
                )
                sec_out.write(json.dumps({"instruction": sinstr, "output": sec_body}, ensure_ascii=False) + "\n")
                n_sec += 1
        except Exception:
            continue
    # Also harvest style-examples as post samples (persona can be in path)
    for md in glob(os.path.join("content", "style-examples", "**", "*.md"), recursive=True):
        try:
            txt = open(md, "r", encoding="utf-8").read().strip()
            if not txt:
                continue
            title = os.path.splitext(os.path.basename(md))[0]
            persona = infer_persona_from_path(md)
            ctrl = f"[persona={persona}] " if persona else ""
            instr = (
                f"{ctrl}Write a clear, helpful blog post with the title '{title}'. "
                "Use H2 sections: Overview, Why It Matters, Prerequisites, Steps, Examples, FAQs, References. "
                "Use short sentences and bullet points for steps."
            )
            post_out.write(json.dumps({"instruction": instr, "output": clean_body(txt)}, ensure_ascii=False) + "\n")
            n_post += 1
        except Exception:
            continue
    sec_out.close(); post_out.close()
    print(f"Wrote {n_sec} section samples → {OUT_DIR}/sections.jsonl")
    print(f"Wrote {n_post} post samples    → {OUT_DIR}/posts.jsonl")


if __name__ == "__main__":
    main()
