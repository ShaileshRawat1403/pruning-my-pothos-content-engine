#!/usr/bin/env python3
"""
Lightweight governance checks for a generated Markdown post.
Usage:
  python tools/ci/check_post.py --file artifacts/<slug>/blog/draft.md \
    [--allow github.com --allow pruningmypothos.com] [--no-external] [--min-len 500]

Exits non-zero on any violation.
"""
import argparse
import os
import re
import sys
from typing import List


REQ_H2 = ["Overview", "Why It Matters", "Prerequisites", "Steps", "Examples", "FAQs", "References"]
META_PAT = re.compile(r"^(Document:|Your task:|I\'m sorry|In a hypothet)", re.I | re.M)
URL_RE = re.compile(r"https?://[^\s\)\]]+")


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="Path to Markdown file")
    ap.add_argument("--allow", action="append", default=[], help="Allowed domains")
    ap.add_argument("--no-external", action="store_true")
    ap.add_argument("--min-len", type=int, default=500)
    return ap.parse_args()


def h2_headings(md: str) -> List[str]:
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", md, flags=re.M)]


def domains(urls: List[str]) -> List[str]:
    out = []
    for u in urls:
        try:
            host = re.sub(r"^https?://", "", u).split("/", 1)[0]
            out.append(host.lower())
        except Exception:
            pass
    return out


def main():
    args = parse_args()
    p = args.file
    if not os.path.exists(p):
        print(f"File not found: {p}", file=sys.stderr)
        return 2
    with open(p, "r", encoding="utf-8") as f:
        md = f.read()

    errs = []
    # Meta artifacts
    if META_PAT.search(md):
        errs.append("Meta artifacts present (Document:/Your task:/apology/hypothet)")
    # Length
    if len(md.strip()) < args.min_len:
        errs.append(f"Too short: {len(md.strip())} < {args.min_len}")
    # Required H2s
    h2s = h2_headings(md)
    missing = [h for h in REQ_H2 if h not in h2s]
    if missing:
        errs.append("Missing H2 sections: " + ", ".join(missing))
    # References policy
    urls = URL_RE.findall(md)
    if args.no_external and urls:
        errs.append("Found external URLs while no_external is set")
    if args.allow and urls:
        d = domains(urls)
        bad = [x for x in d if not any(x.endswith(allow) or x == allow for allow in args.allow)]
        if bad:
            errs.append("Disallowed domains: " + ", ".join(sorted(set(bad))))

    if errs:
        for e in errs:
            print("[FAIL]", e)
        return 1
    print("[OK] Governance checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

