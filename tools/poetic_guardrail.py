#!/usr/bin/env python3
"""
Lightweight PoeticMayhem guardrail checker.

Usage:
  python tools/poetic_guardrail.py --file path/to/output.md
  cat output.txt | python tools/poetic_guardrail.py

Checks (fail on non-zero exit):
- Sentence count <= 6
- Words per sentence <= 14
- At least one line break every ~2 sentences
- No banned clichés
- Contains a contrast/paradox hint (keywords)
"""
import argparse
import re
import sys
from typing import List

BANNED = {
    "hustle", "follow your dreams", "believe in yourself",
    "unlock your potential", "reach for the stars", "you’ve got this",
    "never give up", "change your mindset", "live your best life", "manifest",
}

CONTRAST_HINTS = {" vs ", "but ", "however", "yet ", "paradox", "friction", "contrast", "shift"}


def split_sentences(text: str) -> List[str]:
    # Naive split good enough for short lines
    parts = re.split(r"[.!?]\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def words_per_sentence(sent: str) -> int:
    return len(sent.split())


def has_banned(text: str) -> bool:
    lower = text.lower()
    return any(b in lower for b in BANNED)


def has_contrast(text: str) -> bool:
    lower = text.lower()
    return any(h in lower for h in CONTRAST_HINTS)


def check_line_breaks(text: str) -> bool:
    # Ensure we don't have a giant paragraph; prefer short lines.
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False
    # If any line is very long, reject.
    return all(len(ln.split()) <= 18 for ln in lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Path to file to check", default=None)
    args = parser.parse_args()

    if args.file:
        data = open(args.file, "r", encoding="utf-8").read()
    else:
        data = sys.stdin.read()

    sentences = split_sentences(data)
    if not sentences:
        print("fail: no content", file=sys.stderr)
        return 1
    if len(sentences) > 6:
        print(f"fail: too many sentences ({len(sentences)} > 6)", file=sys.stderr)
        return 1
    if any(words_per_sentence(s) > 14 for s in sentences):
        print("fail: sentence exceeds 14 words", file=sys.stderr)
        return 1
    if has_banned(data):
        print("fail: cliché detected", file=sys.stderr)
        return 1
    if not has_contrast(data):
        print("fail: missing contrast/paradox/shift hint", file=sys.stderr)
        return 1
    if not check_line_breaks(data):
        print("fail: line break/length issues", file=sys.stderr)
        return 1

    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
