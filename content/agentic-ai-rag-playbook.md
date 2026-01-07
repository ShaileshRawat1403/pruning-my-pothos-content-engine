---
title: Agentic AI + RAG Implementation Playbook
slug: agentic-ai-rag-playbook
audience: pm, sme, platform-engineer
tags:
  - agentic-ai
  - rag
  - docs-as-code
  - governance
---

# Agentic AI + RAG Implementation Playbook (ELI12)

> **Goal:** help a small team build an agentic content workflow that reliably answers questions with up-to-date docs using Retrieval Augmented Generation (RAG).

## 1. Big Idea (Explain Like I'm 12)

Imagine a super-smart librarian (the **agent**) who:

- reads your company docs every morning (that's **retrieval**)
- keeps the most useful pages at the front of the shelf (that's the **vector index**)
- answers teammates using natural language (that's the **LLM**)
- double-checks answers with citation stickers (that's your **governance guardrail**)

You give the librarian a short **brief** (task instructions), a stack of **approved books** (allowed domains), and a list of **off-limits topics** (blocked domains). The agent handles the rest while logging every decision.

## 2. Architecture Overview

```
┌────────────┐     ingest docs     ┌──────────────┐    embed + store    ┌─────────────┐
│ Source Docs│ ───────────────────▶│ RAG Pipeline │────────────────────▶│ Vector Store │
└────────────┘                     └──────────────┘                     └─────────────┘
        ▲                                   │                                    │
        │                                   ▼                                    ▼
        │                         ┌────────────────┐                   ┌─────────────────┐
        │                         │ Retrieval Layer│◀─────────────┐    │ Governance Rules │
        │                         └───────▲───────┘              │    └─────────────────┘
        │                                 │                      │             │
        ▼                                 ▼                      │             ▼
┌────────────────┐             ┌─────────────────────┐          │   ┌────────────────────┐
│ Allowed Domains│             │ Agentic Orchestrator│──────────┴──▶│ Answer + Citations │
└────────────────┘             └─────────────────────┘              └────────────────────┘
```

## 3. Prerequisites Checklist

- [ ] Python 3.9+ virtual environment activated
- [ ] `requirements.txt` installed (`pip install -r requirements.txt`)
- [ ] Local LLM endpoint (Ollama, OpenAI, etc.) reachable
- [ ] Content ingested under `content/` with chunk counts verified in Streamlit Ingest tab
- [ ] Brief created with:
  - **Allowed domains**: your own sites + trusted references
  - **Blocked domains**: noisy or irrelevant sources (competitors, generic blogs)
  - **Must include terms**: key phrases that must appear (e.g., "vector index", "citation")

## 4. Data Prep Workflow

```bash
# 1. Pull recent docs, slides, and FAQs
python -m engine.ingest --urls sources/agentic-rag-urls.txt

# 2. Convert internal HTML or Markdown
streamlit run ui/app.py  # use Ingest tabs for chunk validation

# 3. Rebuild embeddings
python -m engine.rag.build_index
```

Validation tips:

- Use the new "Chunk counts" panel after each ingest to ensure documents exceed 6–8 chunks.
- Block irrelevant domains in the Brief Builder chip input so the agent never cites them.

## 5. Brief Template (copy/paste into **Brief Builder → YAML Preview**)

```yaml
title: "Agentic AI + RAG Playbook"
slug: agentic-ai-rag-playbook
persona: pm
tags: [agentic-ai, rag, docs-as-code]
style_profile: pruningmypothos
blog_mode: sectional
planner: outline
no_external: false
sources:
  allow:
    - pruningmypothos.com
    - docs.github.com
    - langchain.com
    - python.langchain.com
    - llamaindex.ai
  block:
    - wikipedia.org
    - reddit.com
    - stackoverflow.com
  paths:
    - content/agentic-ai-rag-playbook.md
    - content/ai-agentic-smbs.md
exclude_terms: [crypto, gambling]
must_include_terms: [retrieval, vector index, guardrails, evaluation]
min_lengths:
  Overview: 200
  Why It Matters: 180
  Steps: 220
outputs: [blog, github_doc]
publish:
  status: draft
```

## 6. Agentic Retrieval Pipeline (Python Example)

```python
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

SYSTEM_PROMPT = """
You are an AI librarian for agentic RAG systems.
Always cite sources as inline markdown links.
If answer is uncertain, say so and list verification steps.
"""

def build_retriever(collection_path: str):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    store = Chroma(embedding_function=embeddings, persist_directory=collection_path)
    return store.as_retriever(search_type="mmr", search_kwargs={"k": 4})

retriever = build_retriever("engine/.chroma")
model = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2)

def agentic_rag_answer(question: str) -> str:
    docs = retriever.get_relevant_documents(question)
    context = "\n\n".join(f"Source: {d.metadata.get('source')}\n{d.page_content}" for d in docs)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {question}\nAnswer:")
    ]
    response = model(messages)
    return response.content

print(agentic_rag_answer("How do I add a guardrail to block competitor domains?"))
```

## 7. Governance Checklist

| Control                                   | Owner   | Status |
|-------------------------------------------|---------|--------|
| Allow/block domain lists maintained       | PM      | ☐      |
| Retrieval excludes competitor embeds      | Eng     | ☐      |
| Duplicate detection threshold (<0.92)     | Data    | ☐      |
| Section length minimums enforced          | PM      | ☐      |
| Blocklist violation JSON monitored        | QA      | ☐      |

## 8. Evaluation Routine

1. **Run deterministic generation** (temp = 0, seed = 42).
2. Review `artifacts/<slug>/meta/section_quality.json` for low-scoring sections.
3. Spot-check citations; block any noisy domains via Brief Builder chips.
4. Use `make eval-agentic` (custom script) to run regression prompts against the new content.

## 9. Rollout Playbook

- **Day 0:** ingest updated docs, rebuild index, regenerate draft.
- **Day 1:** human edit, merge changes to `content/`, re-run `build_index`.
- **Day 2:** schedule publish; monitor blocklist JSON for violations.
- **Weekly:** refresh allow/block lists, re-run evaluations, archive old drafts.

## 10. Quick Start Summary

1. Add clean source docs.
2. Use the Brief Builder to set **Allowed** and **Blocked** domains via chips.
3. Generate deterministic draft.
4. Review meta JSONs; iterate until blocklist + quality gates pass.
5. Publish or export technical assets (blog + GitHub doc).

Happy shipping!
