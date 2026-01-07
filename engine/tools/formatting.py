import re

def _squash_blank_lines(text: str) -> str:
    # Keep at most one blank line in a row
    lines = text.splitlines()
    out = []
    blank = 0
    for ln in lines:
        if ln.strip() == "":
            blank += 1
            if blank <= 1:
                out.append("")
        else:
            blank = 0
            out.append(ln.rstrip())
    return "\n".join(out).strip()

def _to_markers(text: str, *, bullet="▪️ ", callout="👉 ") -> str:
    out_lines = []
    for ln in text.splitlines():
        s = ln.lstrip()
        # Bullets → ▪️
        if s.startswith("- ") or s.startswith("* ") or s.startswith("• "):
            out_lines.append(bullet + s[2:])
            continue
        # ASCII arrows to 👉
        if s.startswith("-> ") or s.startswith("> "):
            out_lines.append(callout + s.split(maxsplit=1)[-1])
            continue
        out_lines.append(ln.rstrip())
    return "\n".join(out_lines)

def ensure_hashtags(text: str, hashtags: str) -> str:
    if not hashtags:
        return text.strip()
    t = text.strip()
    # If text already ends with a hashtag block, keep
    last = t.splitlines()[-1] if t.splitlines() else ""
    if "#" in last:
        return t
    return (t + "\n\n" + hashtags).strip()

def linkedin_format(text: str, hashtags: str, *, limit: int = 3000) -> str:
    t = _to_markers(text)
    t = _squash_blank_lines(t)
    # Emphasize the first non-empty line as a hook if not already emphasized
    lines = t.splitlines()
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s:
            if not (s.startswith("**") and s.endswith("**")) and len(s) <= 140:
                lines[i] = f"**{s}**"
            break
    t = "\n".join(lines)
    t = ensure_hashtags(t, hashtags)
    # hard trim happens in caller; keep here too for safety
    if len(t) > limit:
        t = t[: limit - 1] + "…"
    return t

def instagram_format(text: str, hashtags: str, *, limit: int = 2200) -> str:
    t = _to_markers(text)
    t = _squash_blank_lines(t)
    t = ensure_hashtags(t, hashtags)
    if len(t) > limit:
        t = t[: limit - 1] + "…"
    return t

def blog_format(md: str) -> str:
    # Light normalization: trim whitespace and ensure single H1 if multiple exist.
    lines = md.splitlines()
    h1_seen = False
    out = []
    for ln in lines:
        # Drop Setext underlines (==== or ----) that can appear under random lines
        if re.match(r"^[=-]{3,}\s*$", ln):
            continue
        if ln.startswith("# "):
            if h1_seen:
                # downgrade accidental extra H1 to H2
                ln = "##" + ln[1:]
            h1_seen = True
        out.append(ln.rstrip())
    return _squash_blank_lines("\n".join(out).strip())

def github_format(md: str) -> str:
    # Light normalization for README-style docs
    return blog_format(md)
