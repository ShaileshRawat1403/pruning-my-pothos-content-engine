"""
Delete one or more sources from the vector index by file path or glob.

Usage examples:
  python -m engine.rag.prune_sources content/plants/*.md content/agentic-vs-nocode.md

Notes:
  - Works with the configured backend (Chroma or Qdrant) via get_store().
  - Only deletes entries whose metadata.source equals the given file path(s).
"""
import os
import sys
import glob

# Minimal .env loader (comments allowed)
def _load_dotenv_file():
    path = os.path.join(os.getcwd(), ".env")
    if not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                raw = line.rstrip("\n"); s = raw.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                k = k.strip(); vv = v.strip()
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

from engine.rag.vectorstore import get_store


def main(args: list[str]):
    if not args:
        print("Provide one or more file paths or globs under content/ to prune.")
        sys.exit(2)
    store = get_store()
    # Expand globs, dedupe, ensure only existing files
    targets: list[str] = []
    for a in args:
        matches = glob.glob(a)
        if matches:
            targets.extend(matches)
        else:
            targets.append(a)
    seen = set(); final = []
    for t in targets:
        tt = os.path.normpath(t)
        if tt not in seen and os.path.exists(tt):
            final.append(tt); seen.add(tt)
    if not final:
        print("No matching files found.")
        return
    for fp in final:
        try:
            store.delete_by_source(fp)
            print(f"Pruned entries for {fp}")
        except Exception as e:
            print(f"Failed to prune {fp}: {e}")


if __name__ == "__main__":
    main(sys.argv[1:])

