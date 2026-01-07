from markdown import markdown
from bs4 import BeautifulSoup
import re

def _slugify(text: str) -> str:
    t = re.sub(r"[^A-Za-z0-9\-\_ ]+", "", text).strip().lower()
    t = re.sub(r"\s+", "-", t)
    t = re.sub(r"-+", "-", t)
    return t

def md_to_clean_html(md_text: str) -> str:
    html = markdown(md_text, extensions=["extra", "sane_lists"])
    soup = BeautifulSoup(html, "html.parser")
    # Add ids to headings for basic linking
    for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        if not h.get("id"):
            s = _slugify(h.get_text(" ", strip=True))
            if s:
                h["id"] = s
    # Sanitize links for safer previews
    for a in soup.find_all("a"):
        a["rel"] = (a.get("rel") or []) + ["nofollow", "noopener"]
        a["target"] = "_blank"
    return str(soup)
