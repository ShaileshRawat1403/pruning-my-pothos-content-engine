# Agentic AI Primer

## What “agentic” means
LLM-driven systems that can decide when to call tools, plan multi-step work, and reflect on results instead of only answering a single prompt.

## Core loop
1) **Observe**: accept user/task input and current state.
2) **Plan**: outline steps; choose tools (search, DB, code execution).
3) **Act**: run tools; gather results.
4) **Reflect**: check if results meet the goal; revise plan if not.
5) **Report**: produce a concise, grounded answer with sources.

## Design rules
- Keep the planner simple: short lists of steps; avoid deep recursion without guardrails.
- Cap tool calls and depth to prevent runaway loops.
- Always ground responses in tool outputs; no freeform speculation.
- Cache intermediate results to avoid redundant calls.
- Log tool inputs/outputs for observability and debugging.

## Patterns
- **Retriever-then-Generator**: search first, then compose an answer with citations.
- **Validator**: run a second pass to check style, safety, and grounding.
- **Fallback models**: try fast models first; escalate to larger ones on failure or low confidence.

## Practical safeguards
- Timeouts and rate limits for external tools.
- Allowlist tools; block shell access unless explicitly required.
- Detect low-context cases and ask for clarification instead of guessing.

## Example roles
- Brief planner (turns a request into steps and sources)
- Fact retriever (fetches chunks from vector DB)
- Writer (drafts sections with style and length controls)
- QA/validator (checks grounding, tone, and completeness)
