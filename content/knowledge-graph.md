# Knowledge Graph (High-Level)

## Nodes
- **Briefs**: title, slug, persona, style_profile, outputs, sources (allow/block), publish status.
- **Content Sources**: URL/file path, tags, chunk IDs, domain.
- **Chunks**: embedding vector, text span, source_id, section hints.
- **Models**: primary, fallback, candidate set, params (temperature, seed, max_predict).
- **Runs/Artifacts**: brief_id, model_used, outputs (blog, social), quality metrics, publish result.
- **Styles**: profile name → tone rules, formatting rules.
- **Personas**: label → voice/tone biases.
- **Vector DB**: collection, chunk → embedding, metadata.

## Edges
- Brief **uses** Style | Persona | Sources (allow/block).
- Brief **generates** Artifacts (blog/social/github).
- Artifact **references** Chunks → Source → Domain.
- Model **produces** Artifacts **using** Retrieval (Chunks).
- Run **logs** Model params | retrieval params | quality results.
- Style **applies to** Sections in Artifacts.
- Persona **applies to** Tone in Artifacts.

## Use
- Retrieval grounding: Artifact sections cite Chunk/Source to trace provenance.
- Style enforcement: map each Artifact section to the Style rules used.
- Quality checks: tie lint scores back to Brief/Model parameters.
- Debugging: if a section is weak, inspect the Chunks and Sources linked to that run, then regenerate with alternate Style/Persona/Model.
