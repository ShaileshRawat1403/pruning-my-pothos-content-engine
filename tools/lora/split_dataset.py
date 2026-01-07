#!/usr/bin/env python3
"""
Split LoRA datasets into train/val with deterministic shuffling.
Inputs (if present):
  data/lora/sections.jsonl, data/lora/posts.jsonl
Outputs:
  data/lora/sections_train.jsonl, data/lora/sections_val.jsonl
  data/lora/posts_train.jsonl,    data/lora/posts_val.jsonl
Reports counts and persona distribution (if found in instruction).
"""
import os
import json
import random
from collections import Counter

DATA_DIR = os.path.join("data", "lora")


def load_jsonl(path: str):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out


def persona_of(rec):
    try:
        ins = rec.get("instruction", "")
        if "[persona=" in ins:
            s = ins.split("[persona=", 1)[1]
            p = s.split("]", 1)[0].strip().lower()
            return p
    except Exception:
        return None
    return None


def split_and_write(name: str, records: list, val_ratio: float = 0.1, seed: int = 42):
    if not records:
        return (0, 0, Counter())
    random.Random(seed).shuffle(records)
    n = len(records)
    n_val = max(1, int(n * val_ratio))
    val = records[:n_val]
    train = records[n_val:]
    # write
    def dump(fn, arr):
        path = os.path.join(DATA_DIR, fn)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for r in arr:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    dump(f"{name}_train.jsonl", train)
    dump(f"{name}_val.jsonl", val)
    # persona stats
    ctr = Counter()
    for r in records:
        p = persona_of(r)
        if p:
            ctr[p] += 1
    return (len(train), len(val), ctr)


def main():
    secs = load_jsonl(os.path.join(DATA_DIR, "sections.jsonl"))
    posts = load_jsonl(os.path.join(DATA_DIR, "posts.jsonl"))
    st, sv, sp = split_and_write("sections", secs)
    pt, pv, pp = split_and_write("posts", posts)
    print(f"Sections: train={st}, val={sv}, personas={dict(sp)}")
    print(f"Posts:    train={pt}, val={pv}, personas={dict(pp)}")


if __name__ == "__main__":
    main()

