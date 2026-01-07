# Agentic Content Engine (M1-friendly)

Opinionated, small-model-first content engine that:
- Indexes your existing content (Qdrant + bge-small),
- Generates grounded drafts (Ollama Llama-3.1-8B or Phi-3 Mini),
- Converts Markdown to HTML,
- Publishes **as draft** to WordPress via REST.

## Guardrails
1) **Duplicate protection**: cosine similarity ≥ 0.92 vs. recent posts → skip publish.
2) **Allowlist references**: only domains in `sources.allow` are permitted in “References”.
3) **Social snippets**: if `social: true`, writes `artifacts/<slug>/social.md` for LinkedIn/X.

## Quickstart
1. Install Docker Desktop (Apple Silicon).
2. Copy `.env.example` → `.env` and set WordPress creds (or leave unset to skip publishing).
3. Start services:
```
make up
make pull
```
4. Add Markdown to `content/` (for RAG), then:
```
make index
```
5. Generate a draft from the example brief:
```
make run brief=briefs/example.yaml
```
6. If WP creds are set and guardrails pass, a **draft** post is created. Otherwise, artifacts are saved to `artifacts/<slug>/`.

### Where to find outputs (categorized)
- Blog: `artifacts/<slug>/blog/draft.md` and `blog/draft.html`
- Social: `artifacts/<slug>/social/linkedin.md`, `social/instagram.md`
- GitHub doc: `artifacts/<slug>/github/README.md`
- Meta (guardrails/results): `artifacts/<slug>/meta/*.json`

## Ingest Open Sources (Production-friendly)
- Put URLs in `sources/urls.txt` (one per line) or YAML in `sources/sources.yaml`.
- Ingest to Markdown with metadata:
```
make ingest urls=sources/urls.txt            # add args="--enrich" to auto-summarize/tag via LLM
```
- Imported files are saved under `content/imports/` and auto-indexed by `make index` / `make index-local`.

Enrichment (optional): set `OLLAMA_URL` and `GEN_MODEL` in `.env` and pass `--enrich` to infer summaries/tags.

### Multi-Platform Outputs
- Add an `outputs` list in your brief to generate platform-specific content alongside the blog draft. Supported: `linkedin`, `instagram`, `github_doc`.
- Optionally set a style profile via `style_profile` or inline `style` guidelines.

Example:
```
outputs: [blog, linkedin, instagram, github_doc]
style_profile: pruningmypothos
```

Local (non-Docker) usage:
```
make venv
make index-local
make run-local brief=briefs/example-multiplatform.yaml
```

## Models
- Default GEN_MODEL: `phi3:mini-128k` (via Ollama) for long-context drafts; fallback: `llama3.2:3b` if you need smaller memory.
- Embeddings: `nomic-embed-text:latest` via Ollama. If your Ollama build predates `/api/embeddings`, set `EMB_PROVIDER=sentence` and the engine will fall back to `sentence-transformers` (default: `BAAI/bge-small-en-v1.5`).

## Next steps
- Add LangGraph once stable.
- Add metrics (PostHog) later if needed.

## Performance Tuning (Ollama via .env)
Set these optional variables in `.env` to tune generation (defaults now favor long-context Phi-3: `GEN_NUM_CTX=120000`, `GEN_MAX_CTX=120000`; lower them if you run into memory pressure):
- `GEN_NUM_CTX` (default 4096)
- `GEN_NUM_PREDICT` (overrides per-length cap)
- `GEN_MAX_CTX` (hard cap on context; default 4096)
- `GEN_MAX_PREDICT` (hard cap on generated tokens; default 2400)
- `GEN_TEMPERATURE` (default 0.3)
- `GEN_NUM_THREAD` (CPU threads)
- `GEN_NUM_BATCH`
- `GEN_TOP_K`, `GEN_TOP_P`
- `GEN_REPEAT_PENALTY`, `GEN_PRESENCE_PENALTY`, `GEN_FREQUENCY_PENALTY`
- `GEN_MIROSTAT`, `GEN_MIROSTAT_TAU`, `GEN_MIROSTAT_ETA`

Example:
```
GEN_NUM_THREAD=6
GEN_TOP_P=0.9
GEN_REPEAT_PENALTY=1.1
```

## Style and Planning
- Style profiles: place a Markdown file in `engine/styles/<name>.md` and set `style_profile: <name>` in your brief.
- Style examples: add `style_examples` as file paths or globs. The engine will read short snippets and condition the prompts.

Example brief additions:
```
style_profile: pruningmypothos
style_examples:
  - samples/voice/*.md
  - content/ai-agentic-smbs.md
```

- Sectional mode: set `blog_mode: sectional` to write long posts with per-section retrieval.
- Simple planner: set `planner: outline` (optionally with sectional mode) to generate a data-driven section plan before writing.
### WordPress publishing
- Set `WP_BASE_URL`, `WP_USER`, `WP_APP_PASSWORD` in `.env`.
- WordPress expects numeric IDs for categories and tags. In your brief, set:
```
publish:
  status: draft
  category_ids: [1, 2]  # numeric category IDs
  tag_ids: [10, 11]     # numeric tag IDs
```
- If non-integer IDs are provided, they are skipped to avoid 400 errors. Any publish error is saved to `artifacts/<slug>/meta/publish_error.json`.
## Vector Store Options

| Option | When to use | Notes |
|--------|-------------|-------|
| **Local Qdrant (recommended)** | Everyday dev / demo without depending on a hosted free tier | <br>1. `make up-qdrant` *(Docker)* **or** install the native binary (`brew install qdrant/qdrant/qdrant`) and run `qdrant --config-path ~/.config/qdrant/config.yaml`.<br>2. Verify with `make check-qdrant` – you should see `200 OK` from `http://localhost:6333/readyz`.<br>3. Set the following in `.env`: <br>`VDB_BACKEND=qdrant`<br>`QDRANT_URL=http://localhost:6333`<br>`QDRANT_COLLECTION=content`<br>(optional) `QDRANT_API_KEY=`
| **Chroma (fallback)** | Quick single-user experiments where you don't want another service | Works entirely in-process and writes to `engine/.chroma`. Set `VDB_BACKEND=chroma` (and remove the Qdrant vars) if you want to revert. |

Once the service is running, rebuild embeddings with `python -m engine.rag.build_index` (or `make index-local`).
