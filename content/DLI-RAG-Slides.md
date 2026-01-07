# Building RAG Agents (Summary)

## Core idea
Retrieval-Augmented Generation (RAG) pairs an LLM with a search layer so responses stay grounded in your data instead of the model’s prior.

## Architecture (high level)
- **User query** → embed → vector search (Qdrant/Chroma) → top-k chunks
- **LLM** gets: user query + retrieved chunks + system/guardrails
- **Response** → citations + optional tool calls (links, follow-ups)

## Design principles
- Keep retrieval deterministic: fixed top_k and per-source caps to avoid noisy blends.
- Chunk text cleanly (semantic or fixed ~500–800 chars) with minimal overlap; store source IDs.
- Re-rank if needed; avoid over-stuffing the context window.
- Track provenance: return which sources were cited and include stable URLs.

## Guardrails
- Disallow answers when confidence is low; state “insufficient context.”
- Enforce allowlist/denylist for domains in references.
- Cap generation length; avoid speculative claims; keep style consistent.

## Agent extensions
- Tool use: allow the model to trigger secondary lookups or calculations.
- Conversation memory: summarize long threads, not raw append.
- Evaluation: auto-check for grounding (citations), relevance, and style compliance.

## Practical tips
- Pre-clean PDFs/slides: remove page numbers/footers; normalize headings.
- Keep embeddings fresh: re-index when sources change.
- Monitor retrieval quality: measure hit rate per intent/query cluster.
- Start with smaller models for latency; fall back to larger ones when confidence drops.

## Glossary
- **Embedding**: vector representation of text used for similarity search.
- **Chunk**: a slice of source text stored in the vector DB.
- **Top-k**: number of chunks retrieved per query.
- **Context window**: max tokens an LLM can see in one request.
