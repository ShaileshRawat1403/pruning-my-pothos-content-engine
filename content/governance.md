# Content Governance for SMBs

This note seeds retrieval with house rules the generator must follow.

## Voice & Structure
- Voice: clear, direct, helpful. Avoid hype.
- Sections: H2s exactly: Overview, Why It Matters, Prerequisites, Steps, Examples, FAQs, References.
- Sentences: short (≤20 words); prefer bullets for steps.
- Close with a next action or CTA.

## Links & Citations
- If `no_external: true`, do not include URLs; add "No external references available." under References.
- If `sources.allow` is set, only cite those domains.
- Use inline [1], [2]; list links under References.

## Disallowed
- Product/model catalogs or vendor blurbs unless explicitly in context.
- Meta text like "Document:", "Your task:", apologies, or analysis chatter.

## Workflow
- Deterministic runs: `GEN_TEMPERATURE=0.0`, `GEN_SEED=42`.
- Duplicate guard: similarity ≥ 0.92 → skip publish.
- Preview locally before publish.

