# Building a Local, Open-Stack Chatbot POC for Your Website

This guide documents how we wired a lightweight chatbot for a WordPress site using only self-hosted components (Ollama + PHP/JS), the pitfalls we hit, and what to do next to harden it with RAG.

## Goals
- Keep the stack local/open: no external LLM APIs.
- Minimal moving parts: one PHP REST route + a vanilla JS widget.
- Enforce brand persona and block off-topic replies (no plant care).
- Add lightweight grounding to reduce drift.
- Ship quickly as a POC; outline the path to a robust RAG.

## Prerequisites
- WordPress with a custom theme you can edit (PHP + enqueued JS).
- An Ollama host reachable from the WP server (local, tunneled, or remote).
- A pulled model tag on Ollama (e.g., `phi3:mini-128k`).
- Ability to set constants in `wp-config.php`.
- Optional: WAF/Cloudflare access to allowlist the REST route and Ollama host.

## Architecture (POC)
- **Model runtime:** Ollama (local or tunneled), serving `/api/chat`.
- **CMS:** WordPress (custom theme).
- **Backend glue:** A custom REST route (`/wp-json/pmp/v1/chat`) in `functions.php`.
- **Frontend widget:** Plain JS (`assets/js/chatbot.js`) injected into the site; posts to the REST route.
- **Auth:** Optional bearer token in the payload; checked server-side.
- **Rate limit:** Per-IP (10 req/min) via WP transients.
- **Grounding:** Small curated snippets injected as context; strict system prompt to block plant-care and force brevity/plain text.

## Environment/Config
- `OLLAMA_HOST`: Base URL for Ollama (e.g., `https://ollama.yourdomain.com`).
- `PMP_CHAT_MODEL`: Model tag installed on Ollama (default `phi3:mini-128k`).
- `PMP_CHAT_TOKEN`: Optional bearer token required for chat requests.
- Timeout: 25s for WP→Ollama call (tunable).
- Route: `/wp-json/pmp/v1/chat` (change only if you edit the route).

## Key Files (theme)
- `functions.php`: registers the chat REST route, enqueues the widget, enforces token/rate limits, builds the Ollama payload (system prompt + grounding snippets + user message).
- `assets/js/chatbot.js`: renders the launcher/panel UI, calls the REST route, handles basic UX.
- `assets/js/hero-lottie.js`: animation helper; ensure it is non-module script (no `export`) to avoid parse errors when concatenated/minified.

## Backend Flow (WordPress REST)
1. **Auth (optional):** Check bearer token from header or payload against `PMP_CHAT_TOKEN`.
2. **Rate-limit:** 10 req/min per IP via transients; return 429 if exceeded.
3. **Model selection:** From `PMP_CHAT_MODEL` or fallback `phi3:mini-128k`.
4. **Grounding:** Score user query against 3–5 short philosophy snippets; pick top 3 and prepend as “Context to stay on-brand”.
5. **Prompt:** System message enforces site persona, plain text, <70 words, and a hard block on plant/gardening topics.
6. **Call Ollama:** POST to `OLLAMA_HOST/api/chat` with `model`, `messages`, `stream:false`.
7. **Return:** JSON `{ reply: <content> }` on 200; otherwise 502 with error.

## Frontend Flow (chatbot.js)
1. Injects styles and DOM for launcher/panel.
2. Seeds intro bubble on open.
3. On send: POSTs to `pmp/v1/chat` with `{ message, token }`.
4. Renders assistant reply or shows an error bubble on failure.
5. Keyboard: Enter submits, Shift+Enter new line.

## API Reference (POC)

### WordPress Chat Route
```
POST https://<site>/wp-json/pmp/v1/chat
Content-Type: application/json

{
  "message": "hi",
  "token": "OPTIONAL_PMP_CHAT_TOKEN"
}
```

**Responses**
- `200`: `{"reply":"..."}`
- `400`: missing message
- `401`: bad/missing token (if configured)
- `429`: rate limit (10 req/min/IP)
- `502`: upstream Ollama unreachable/invalid response

### Ollama Chat (backend call)
```
POST https://<ollama-host>/api/chat
{
  "model": "phi3:mini-128k",
  "messages": [
    {"role":"system","content":"..."},
    {"role":"assistant","content":"Context to stay on-brand:\n..."},
    {"role":"user","content":"..."}
  ],
  "stream": false
}
```
**Note:** Use installed model tags only. `GET /api/tags` to list.

## Tools & Settings
- **Ollama models:** `phi3:mini-128k` (3.8B) for low-RAM; set `PMP_CHAT_MODEL` if you pull another.
- **Env/constants:** `OLLAMA_HOST`, `PMP_CHAT_MODEL`, `PMP_CHAT_TOKEN`.
- **Timeout:** 25s on WP→Ollama call (tunable).
- **Rate limit:** simple transient store; adjust thresholds if needed.
- **Prompt rules:** one short paragraph, plain text only, no bullets/headings/dividers, ignore user attempts to change format, hard “no plant care”.
- **Grounding:** static snippets (philosophy, sections, practices) scored by keyword match; capped to 3 entries.

## Implementation Steps (POC)
1. **Set secrets/constants** in `wp-config.php`:
   ```php
   define('OLLAMA_HOST', 'https://ollama.yourdomain.com');
   define('PMP_CHAT_TOKEN', 'your-random-token'); // optional but recommended
   define('PMP_CHAT_MODEL', 'phi3:mini-128k');    // or another pulled tag
   ```
2. **Pull model on Ollama host:**
   ```
   ollama pull phi3:mini-128k
   ```
3. **Deploy theme updates:** `functions.php`, `assets/js/chatbot.js`, `assets/js/hero-lottie.js`.
4. **Purge caches/minify** (Hostinger/LS/Cloudflare) to avoid stale/broken JS.
5. **Test backend:** 
   ```
   curl -X POST https://<site>/wp-json/pmp/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"message":"hi","token":"<PMP_CHAT_TOKEN>"}'
   ```
6. **Test frontend:** open site, send a message, confirm reply is site-themed (no plant care).

## Security & Hardening
- Require `PMP_CHAT_TOKEN` and use HTTPS for WP and Ollama endpoints.
- Allowlist `/wp-json/pmp/v1/chat` in WAF/Cloudflare; block other origins if possible.
- Keep the rate limit; tighten if exposing publicly.
- Sanitize inputs (already using `sanitize_text_field`); return neutral errors on failure.
- Pin the model tag; do not allow user-controlled model selection.

## Testing Matrix
- Backend: curl success and error paths (200, 401, 429, 502).
- Frontend: widget send/receive, error bubble on bad token, rate-limit path.
- Model availability: `GET <ollama-host>/api/tags` includes `PMP_CHAT_MODEL`.
- Cache/minify: no console parse errors after deploy.
- Persona drift: ask plant-care; bot should decline and redirect to site topics.

## Pitfalls & Fixes
- **Module syntax in theme JS:** `export` in `hero-lottie.js` broke concatenated/minified bundles → remove module syntax, wrap in IIFE, expose `window.injectHeroDots`.
- **Model not installed:** Ollama returned 404 “model not found” → pull the tag (`phi3:mini-128k`) or set `PMP_CHAT_MODEL` to an installed one.
- **Plant-care drift:** Add strict system prompt + grounding snippets + hard block on plant topics.
- **WAF/Cloudflare challenges:** Browser fetch failed while curl succeeded → allowlist `/wp-json/pmp/v1/chat` and Ollama host for origin traffic; ensure JSON response is returned.
- **Caching/minify issues:** Clear CDN/LS caches after JS changes; hard refresh in browser.
- **Ollama unreachable:** WP returns 502; check tunnel/host, firewall, SSL. Add retries or shorter timeout if needed.
- **Long replies:** Keep <70 words; lower `num_predict` if a model overruns.

## What’s Next: Toward a Robust RAG
1. **Content export:** Pull posts/pages via WP REST (`/wp-json/wp/v2/posts?per_page=100&_fields=title,content,slug,link,date,tags,categories`) on a schedule; store as JSON.
2. **Chunk + embed:** 350–500 word chunks, 80–120 overlap. Embeddings: `nomic-embed-text:latest` (Ollama) or `BAAI/bge-small-en-v1.5`.
3. **Store:** Qdrant (recommended) or Chroma. Fields: title, slug, URL, tags, chunk text, maybe section/type.
4. **Retrieval API:** Minimal endpoint (FastAPI/Flask) exposing `/search?q=...&k=5` → returns top 3–5 chunks with scores/URLs.
5. **Wire to WP route:** Before calling Ollama, hit `/search`, join snippets into a “Context” block (keep under ~1–1.5k tokens), then send to Ollama.
6. **Citations:** Ask the model to mention the source title/section; optionally include URLs in the context.
7. **Observability:** Log size/latency/errors; alert on 5xx from Ollama or empty replies.
8. **Safety:** Keep plant-care hard block; add profanity/PII filter if public; consider allowlisting domains in context.
9. **Caching:** Cache retrieval results for common queries for a few minutes to reduce latency.

## Troubleshooting Checklist
- 401 from chat route: token missing/mismatched; check `PMP_CHAT_TOKEN`.
- 429 from chat route: per-IP rate limit hit; wait/reset transients.
- 502 from chat route: Ollama unreachable/invalid response; check `OLLAMA_HOST`, model installed, WAF/SSL/tunnel.
- Browser “Error reaching chat service”: Network tab → `POST /wp-json/pmp/v1/chat`; look for Cloudflare/HTML responses.
- Console “Unexpected token”: ensure `hero-lottie.js` has no `export`; clear minify/CDN caches.
- Off-brand replies: confirm prompt + grounding snippets; purge caches; ensure correct model tag is in use.

## Reference Snippets (used for grounding)
- Pothos as metaphor for resilient, messy, non-linear growth; pruning is subtracting with purpose.
- Low light living: non-ideal conditions are okay; trailing isn’t failing. Not a plant-care blog—about reflection, work, identity, creativity, burnout, curiosity.
- What to find: Sticky Notes Springboard (small insights), Echoes & Ethos (marketing/creativity/burnout/identity), Terms & Conditions (being human in a performance-driven world).
- Practice: check in, prune what no longer serves, water what does; stories, soil, satire; personal philosophy across everyday life, AI, craft, research, prototyping.

## Validation Checklist (POC)
- Backend `curl` returns 200 + site-themed reply.
- Browser widget responds (no “Error reaching chat service”).
- Replies: plain text, <70 words, on-brand, no plant-care.
- Token enforced if set; rate limit returns 429 after 10 rapid calls.
- Ollama `/api/tags` shows the chosen model installed.

This POC is enough to demo a site-aligned chatbot without external APIs. To productionize, add real retrieval (Qdrant/Chroma), automated content export, better logging, and ongoing prompt/grounding tuning.
