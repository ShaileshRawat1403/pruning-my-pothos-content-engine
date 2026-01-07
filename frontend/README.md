# Hybrid React Front Layer + WordPress Blog (Execution Notes)

This folder holds the React front layer (Vite) plus the shared CSS token file for WordPress. The steps below map to Tasks 0–5 from the execution prompt.

---

## Task 0 – Current State (checked via public endpoints)

- WordPress is at the root: `https://pruningmypothos.com/wp-admin/` redirects to login (302), `/blog/wp-admin/` is 404.
- Origin shows Hostinger behind Cloudflare (headers: `platform: hostinger`, `server: cloudflare`).
- REST is live at `https://pruningmypothos.com/wp-json/wp/v2/…`; example post permalink: `https://pruningmypothos.com/retrieval-augmented-generation-rag/` (canonical is root, not `/blog` yet).

---

## Task 1 – Routing Model (Cloudflare-first)

Goal: React handles everything except WordPress system paths. WordPress stays on the Hostinger origin.

Route patterns to keep on WordPress:

- `/blog/*` (public blog once the prefix is enabled)
- `/wp-admin/*`, `/wp-login.php`, `/wp-json/*`, `/wp-content/*`, `/wp-includes/*`, `/xmlrpc.php`

Cloudflare setup options:

1) **Cloudflare Pages + Worker (recommended)**

```
// worker (wrangler.toml: route = "pruningmypothos.com/*")
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const preserve = [
      "/blog/",
      "/wp-admin/",
      "/wp-json/",
      "/wp-content/",
      "/wp-includes/",
      "/xmlrpc.php",
    ];

    const hitWordPress = preserve.some((p) => url.pathname.startsWith(p));
    if (hitWordPress) {
      // If WP stays at root, strip /blog for origin fetch
      url.pathname = url.pathname.replace(/^\/blog/, "");
      return fetch(url.toString(), request);
    }

    return env.ASSETS.fetch(request);
  },
};
```

- Pages project routes `/*` to the Pages build; the Worker runs in front to bypass Pages for the preserved paths.
- If you later move WP physically to `/blog`, drop the `replace(/^\/blog/, "")` line.

2) **Cloudflare Rules Only (lighter but less flexible)**

- Deploy Pages to `/*`.
- Add “Bypass Cloudflare on Cloudflare Pages” rule for the list above (including `/blog/*` once live) pointing to the Hostinger origin.
- Still keep `/wp-json/*` and admin paths bypassed.

DNS: no risky changes; keep A/CNAME to Cloudflare proxy. Rollback is deleting the Worker/bypass rules so everything returns to WordPress.

---

## Task 2 – React Front Layer

Location: `frontend/`

Commands:

```bash
cd frontend
npm install
npm run dev     # local
npm run build   # outputs dist/ for Pages or any static host
```

Routing rules inside the app:

- “Notes” / “Start Reading” buttons go to the WordPress blog (real URLs). The app prefers `/blog/` but auto-falls back to root if `/blog/wp-json` returns 404.
- Recent Thoughts pulls live posts from `WP REST` (`_embed&per_page=6`). Fallback copies are used if the API fails.
- Internal sections (Gallery, DIY Stack, About, Contact, A.I.) stay client-side view-state.

Environment knobs:

- `VITE_WP_SITE_URL` (default: `https://pruningmypothos.com`)
- `VITE_WP_BLOG_PREFIX` (default: `/blog`). Set to `""` while `/blog` is not yet routed.

Deploy to Cloudflare Pages:

- Build command: `npm run build`
- Output dir: `dist`
- Add the Worker (above) or Pages bypass rules so `/blog/*` and WP system paths go to Hostinger.

Key files:

- `src/App.jsx` – updated hero, live WP feed, dark-mode sync, real blog links.
- `src/styles/tokens.css` – design tokens used by the React layer.

---

## Task 3 – Unified CSS Tokens (Option 1)

- React tokens: `src/styles/tokens.css`
- WordPress drop-in: `frontend/wp-shared-tokens.css` (same tokens + WP typography, buttons, callouts).

How to apply on WordPress:

1) Upload `wp-shared-tokens.css` to your theme and enqueue it after the theme CSS.
2) Add this inline script in `header.php` (above styles) to sync dark mode with the React key:

```html
<script>
(() => {
  try {
    const t = localStorage.getItem("pmp-theme");
    const m = window.matchMedia("(prefers-color-scheme: dark)").matches;
    if (t === "dark" || (!t && m)) document.documentElement.classList.add("dark");
  } catch (e) {}
})();
</script>
```

Token names:

- Colors: `--color-bg`, `--color-surface`, `--color-surface-2`, `--color-text`, `--color-muted`, `--color-border`, `--color-accent`
- Radii: `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl`, `--radius-2xl`
- Shadows: `--shadow-subtle`, `--shadow-card`, `--shadow-elevated`
- Fonts: `--font-heading`, `--font-body`, `--font-mono`

Helpers:

- `.callout-short-answer`, `.callout-key-takeaway` (AEO helpers)
- `.dark` on `<html>` toggles the theme.

---

## Task 4 – WordPress Chrome Alignment

- Header nav targets: `/`, `/blog/`, `/gallery`, `/resources`, `/about`, plus an A.I. link mirroring the React layer.
- Keep markup stable; only swap classes/tokens. Use the shared CSS for buttons (`border-radius: 999px; box-shadow: var(--shadow-subtle); accent color on hover`).
- Footer: mirror links above; background `var(--color-surface-2)`, borders `var(--color-border)`, typography from tokens.

Templates to adjust: `header.php`, `footer.php`, and the navigation block if using block themes. Avoid plugin dependencies.

---

## Task 5 – AEO/SEO Hygiene

- Canonical remains the WordPress URL (React only links out).
- Headings keep a clear hierarchy inside WP content; blockquotes already styled in the shared CSS.
- Utility classes (usable in WP editor):
  - `.callout-short-answer` for short answers/FAQ
  - `.callout-key-takeaway` for key takeaways
- React pages: set per-page `<title>`/`<meta name="description">` in `index.html` or add a lightweight head manager if needed.

---

## Next Steps Checklist

1) Create the Cloudflare Worker (or bypass rules) so `/blog/*` and WP system paths route to Hostinger; strip `/blog` before origin fetch while WP is at root.
2) Deploy the React build to Cloudflare Pages using `frontend/`.
3) Drop `wp-shared-tokens.css` into the WP theme and add the dark-mode bootstrap script.
4) Update WP header/footer nav links to match the React nav targets.
5) Once `/blog` routing is live, set `VITE_WP_BLOG_PREFIX=/blog` (and, optionally, WP “Site Address” to `/blog` for canonical URLs).
