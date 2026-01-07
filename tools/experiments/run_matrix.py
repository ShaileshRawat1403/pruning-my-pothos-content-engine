#!/usr/bin/env python3
"""
Run a small experiment matrix over (model x persona x retrieve cap) for one or more briefs.
Summarize blog lint pass/fail and generation time per run.

Usage:
  python tools/experiments/run_matrix.py --briefs briefs/ai-content-governance-smbs-focused.yaml \
    --models llama3.2:3b phi3:mini-128k \
    --personas "" founder pm \
    --caps 1 2

Outputs CSV summary to experiments/results.csv
"""
import argparse, os, time, subprocess, json, csv, shlex
from pathlib import Path


def run_cmd(cmd, env=None):
    e = os.environ.copy()
    if env:
        e.update({k: str(v) for k, v in env.items() if v is not None})
    t0 = time.time()
    p = subprocess.run(cmd, env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    dt = time.time() - t0
    return p.returncode, p.stdout, dt


def lint_blog(slug: str, allow=None, no_external=True) -> bool:
    allow_arg = []
    if allow:
        for d in allow:
            allow_arg += ["--allow", d]
    noext = ["--no-external"] if no_external else []
    rc, out, _ = run_cmd([".venv/bin/python", "tools/ci/check_post.py", "--file", f"artifacts/{slug}/blog/draft.md", *allow_arg, *noext])
    return rc == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--briefs", nargs="+", required=True)
    ap.add_argument("--models", nargs="+", default=["llama3.2:3b"])
    ap.add_argument("--personas", nargs="+", default=[""])
    ap.add_argument("--caps", nargs="+", type=int, default=[1])
    ap.add_argument("--allow", nargs="*", default=[])
    args = ap.parse_args()

    Path("experiments").mkdir(exist_ok=True)
    rows = []
    for brief in args.briefs:
        try:
            import yaml
            d = yaml.safe_load(Path(brief).read_text())
            slug = d.get("slug")
        except Exception:
            slug = None
        for model in args.models:
            for persona in args.personas:
                for cap in args.caps:
                    env = {
                        "GEN_MODEL": model,
                        "GEN_TEMPERATURE": 0.0,
                        "GEN_SEED": 42,
                        "RETRIEVE_MAX_PER_SOURCE": cap,
                        "SKIP_PUBLISH": 1,
                    }
                    if persona:
                        env["GEN_PERSONA"] = persona
                    rc, out, dt = run_cmd([".venv/bin/python", "-m", "engine.run", brief], env)
                    ok = False
                    if slug:
                        ok = lint_blog(slug, allow=args.allow, no_external=True)
                    rows.append({
                        "brief": brief,
                        "slug": slug or "",
                        "model": model,
                        "persona": persona or "",
                        "cap": cap,
                        "gen_seconds": round(dt, 2),
                        "blog_lint_ok": ok,
                    })
                    print(f"{brief} | {model} | persona={persona or '-'} | cap={cap} | lint_ok={ok} | {dt:.1f}s")

    with open("experiments/results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["brief", "slug", "model", "persona", "cap", "gen_seconds", "blog_lint_ok"])
        w.writeheader(); w.writerows(rows)
    print("Saved experiments/results.csv")


if __name__ == "__main__":
    main()
