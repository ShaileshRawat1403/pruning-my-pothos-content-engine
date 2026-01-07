# Docs-as-Code for SMBs

Docs-as-Code treats content like software: plain text, versioned, tested, and deployed. For small businesses, it means less chaos and more shipping.

## Core practices
- **Briefs as tickets**: one YAML per deliverable.
- **Prompts in repo**: system + user prompts live under `engine/prompts/`.
- **Determinism**: pin models/deps; store run artifacts.
- **Guardrails**: draft-first, link allowlists, duplicate checks.

## Structure pattern for blog posts
- H1 once with the title
- H2 sections: Overview, Why It Matters, Prerequisites, Steps, Examples, FAQs, References
- Short sentences and bulleted steps
- End with **## References** and real URLs

## References
- https://pruningmypothos.com
- https://developer.wordpress.org/rest-api/
- https://www.sbert.net
- https://www.trychroma.com
- https://ollama.ai
