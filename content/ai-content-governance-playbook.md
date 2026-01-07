# AI-Assisted Content Governance Playbook for SMBs

Small and midsize businesses can ship trustworthy content without the bureaucracy of an enterprise editorial team. Pairing a docs-as-code workflow with selective AI assistance keeps every asset reviewable, auditable, and fast to update. This playbook summarizes the operating model we use at Pruning My Pothos and highlights the controls that keep automation trustworthy.

## Objectives
- Publish consistent, on-brand content across blog, docs, and social with lean teams.
- Preserve human editorial judgment while using AI to accelerate drafting and formatting.
- Maintain a provable chain of custody for sources, reviews, and approvals.

## Core Principles
1. **Docs-as-code foundation:** Everything lives in Git. Markdown files, briefs, prompts, and governance policies sit alongside application code so version history is automatic.
2. **Grounded generation:** Retrieval Augmented Generation (RAG) feeds the model only approved notes and references. The AI never cites unvetted sources.
3. **Draft-first publishing:** WordPress drafts (or PR previews) ensure humans review before anything goes live.
4. **Guardrails before publish:** Automated checks catch duplicates, disallowed domains, broken links, and minimum length issues. Failing any check blocks the pipeline.
5. **Telemetry-light:** Store run metadata, prompts, and embeddings locally. Avoid shipping sensitive context to third-party analytics until governance is mature.

## Required Tooling
- **Git hosting** (GitHub or GitLab) with protected branches and reviewers.
- **Static analysis and CI** (GitHub Actions or similar) to run linting, link checking, and guardrails.
- **Vector database** (Chroma for local runs, Qdrant for shared deployments) to store chunk embeddings.
- **LLM runtime** (Ollama + `llama3.2:3b` with `phi3:mini-128k` fallback) with deterministic settings for reproducible drafts.
- **Publishing target** (WordPress REST API or static site generator) configured with draft-first credentials.

## Roles & Responsibilities
- **Content Lead:** Owns tone, structure, and final sign-off. Maintains governance rules.
- **Subject Matter Expert (SME):** Validates claims, regulatory language, and industry terminology.
- **Marketing Operations:** Maintains the engine, vector store, model versions, and guardrail automation.
- **Approver (PM or Legal):** Signs off on accuracy for product launches or regulated topics.

## Operating Workflow
1. **Brief:** Create a YAML brief defining audience, goal, tone, allowed sources, and required terms. Track the brief in Git so reviewers see the plan.
2. **Index:** Run `make index-local` (or `make index`) after updating content notes. This updates the vector store with fresh embeddings.
3. **Generate:** Execute `make run-local brief=...` to produce blog, social copy, and supporting artifacts. Generation runs in sectional mode with per-H2 retrieval.
4. **Assess:** Review guardrail reports in `artifacts/<slug>/meta/*.json`. Fix length violations, citation issues, or duplicated segments before editing prose.
5. **Edit:** Copyedit the Markdown, confirm references align with approved domains, and add SME insights where the model was thin.
6. **Approve:** File a PR. Content Lead checks voice and structure; SMEs confirm accuracy; Legal reviews if required. Use PR comments to log decisions.
7. **Publish:** Merge triggers WordPress draft creation or static-site preview. A final reviewer promotes to live once sign-off is logged.
8. **Post-Publish:** Monitor performance, record retro notes, and feed successful assets back into the content folder for future retrieval.

## Retrieval Best Practices
- Keep notes short and evergreen. Split long documents (~1,000 words) into multiple Markdown files.
- Annotate sections with metadata (frontmatter) when relevant: audience, funnel stage, source URL, and last updated date.
- Remove style guides and prompt instructions from the index; keep them as `style_examples` so they influence voice but don't pollute retrieval.
- Refresh the index after major policy changes or when onboarding new SMEs.

## Guardrails Checklist
- **Duplicate Detection:** Compare cosine similarity against posts from the past six months. If ≥0.92, flag for manual review.
- **Allowlist Enforcement:** Only link to domains listed in the brief. Block untrusted references automatically.
- **Terminology Linting:** Fail drafts containing banned phrases (e.g., "AI magic", "revolutionary") and prompt the editor to rewrite.
- **Link Validation:** Confirm HTTP 200 responses for each reference URL before publishing.
- **Section Quality Scores:** Capture per-H2 confidence and prompt editors to strengthen weak sections.

## Metrics to Monitor
- Time from draft generation to publish-ready merge.
- Number of manual edits per section (Git diff lines changed by humans).
- Distribution of citations across allowed sources (avoid over-relying on a single URL).
- Content freshness: how often governance notes are updated alongside product changes.

## Scaling Considerations
- **Shared Vector Stores:** Run Qdrant natively or on a lightweight VM when multiple editors need the same index.
- **Model Variants:** Offer a "fast" brief option using `phi3:mini-128k` for outlines and a "balanced" path using `llama3.2:3b` for final drafts.
- **Compliance Integration:** Map governance checks to frameworks like NIST AI RMF or ISO/IEC 42001 when working with security-conscious clients.
- **Feedback Loops:** Capture reviewer comments and accepted edits as training data for future fine-tuning.

## References
1. GitHub Docs – Protect branches and require reviews: <https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/defining-the-merge-strategy-for-a-protected-branch>
2. WordPress REST API Handbook – Managing posts via REST: <https://developer.wordpress.org/rest-api/reference/posts/>
3. NIST AI Risk Management Framework – Governance alignment: <https://www.nist.gov/itl/ai-risk-management-framework>
4. MkDocs Deployment Guide – Static site publishing patterns: <https://www.mkdocs.org/user-guide/deploying-your-docs/>
