# A Lean AI Content Engine for Small Businesses

A small, reliable content engine helps SMBs ship consistent, helpful articles without hiring a big team. Keep it simple: local models via Ollama, fast embeddings with bge-small, a file-backed vector DB (Chroma), and WordPress REST for publishing. Docs-as-Code means everything is reproducible: briefs in YAML, prompts versioned, artifacts stored per run.

## Why this stack
- **Ollama + small models** (Llama 3 or 7B instruct) run on a Mac and keep costs near zero.
- **SentenceTransformers (bge-small)** gives fast, decent RAG recall.
- **Chroma** is easy to persist in the repo and good enough for a few thousand chunks.
- **WordPress REST** lets you publish as draft first (safe-by-default).

## Minimal flow
1. Write notes in Markdown in `content/`.
2. `make index` builds embeddings in `engine/.chroma/`.
3. A brief (`briefs/*.yaml`) sets title/goal/tone/allowlist/length.
4. `make run brief=...` retrieves context → drafts Markdown → writes `artifacts/<slug>/draft.md` (and `draft.html`).
5. If WP creds exist, it creates a **Draft** (unless you choose publish/future in the brief).

## Ops tips
- Keep models small and cap tokens so requests always finish.
- Put clear **References** sections in your notes so generations copy the pattern.
- Use an allowlist so outbound links stay within your trusted domains.

## References
- https://ollama.ai
- https://www.sbert.net
- https://www.trychroma.com
- https://developer.wordpress.org/rest-api/
- https://pruningmypothos.com
