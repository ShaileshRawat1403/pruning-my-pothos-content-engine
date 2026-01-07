# Enterprise Content Governance – Policy and Playbook

This document defines how small teams produce, review, and publish reliable content using a docs‑as‑code workflow and light AI assistance. It scopes responsibilities, rules, and controls that keep content accurate, on‑brand, and compliant.

## Scope & Roles
- Audience: prospects, customers, partners; internal enablement where noted.
- Owners: Content Lead (editorial), PM (facts/positioning), SME (technical correctness).
- Approvers: PM + Legal (where required). Content Lead can block for style/structure.

## Style & Structure
- Voice: clear, direct, helpful; avoid hype and passive voice.
- H1: exactly once; H2s: Overview, Why It Matters, Prerequisites, Steps, Examples, FAQs, References.
- Sentences: target ≤20 words; prefer bullets for steps; use parallel structure.
- Calls to action (CTA): end with a concrete next step (e.g., link to guide/demo).

## Evidence & Claims
- Claims must be grounded in owned docs or allowed domains. Include dates for time‑sensitive facts.
- Avoid unverifiable superlatives ("best", "fastest"). Attribute sources explicitly.
- For metrics, include methodology or link to method; prefer ranges over absolutes.

## Citations Policy
- Allowlist domains define what can be cited; anything else is disallowed.
- If `no_external: true`, do not include URLs; add "No external references available." under References.
- Use bracket citations [1], [2] inline and list URLs under References with titles and access dates.
- Link rot: prefer canonical docs; for GitHub, pin commit hashes where feasible.

## Sensitive Content
- No PII, secrets, credentials, internal model names, or source code beyond public repos.
- Comply with branding and legal terminology; avoid regulatory commitments without Legal.
- Respect regional/legal constraints for claims and references.

## Generation Controls
- Deterministic runs by default: `GEN_TEMPERATURE=0.0`, `GEN_SEED` set.
- Sectional mode with outline planner for long posts; reviewers can edit the outline.
- Retry bounds: one conservative retry on generation failures; fall back model allowed.

## Retrieval Policy
- Priority: own documents in `content/` first; public sources second.
- Per‑source cap to diversify context (default `RETRIEVE_MAX_PER_SOURCE=1`).
- Ban meta artifacts and off‑topic chunks from context (e.g., "Document:", apologies, vendor catalogs).

## Guardrails & Audits
- Duplicate detection: cosine similarity ≥ 0.92 vs recent posts → do not publish.
- Meta artifact rejection: fail if body contains "Document:", "Your task:", apologies, or analysis chatter.
- Minimum length: configurable (`AUDIT_MIN_LEN`), enforce before publish.
- References allowlist: enforce `sources.allow`; block disallowed domains.

## Workflow & Approvals
1) Draft: generate deterministic draft; author edits for substance.
2) Review: PM checks facts; Content Lead checks voice/structure; SME checks accuracy.
3) Approve: PM + (optional) Legal approve; Content Lead merges.
4) Publish: to WordPress as draft first; then schedule/publish.
5) Post‑publish: fix issues quickly; log changes.

SLAs: minor updates ≤ 2 business days; major guides ≤ 10 business days.
Exceptions: documented in PR with rationale; Content Lead signs off.

## Versioning & Logging
- Track briefs and drafts in Git; use PRs for review.
- CI checks: style schema, allowlist links, min length, meta artifact ban, duplicate guard.
- Artifacts: retain generated drafts and meta under `artifacts/<slug>/`.

## Compliance Mapping
- Map this policy to brand guidelines, legal disclaimers, and any external standards as required.
- Keep a change log; review policy quarterly.

## Incident Handling
- Takedown: unpublish within 24 hours if material issues arise.
- Hotfix: correct errors and annotate in the post; update references if links change.
- Root cause: document what failed (retrieval, review, approval) and fix the control.

## Appendices
- Style examples: see `content/style-examples/`
- Bad→Good rewrites: maintain a living file with common fixes (length, voice, headings, citations).
- Checklists: author, reviewer, approver; pre‑publish QA.

