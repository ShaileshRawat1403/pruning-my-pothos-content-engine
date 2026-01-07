import React, { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const Panel = ({ title, children, actions }) => (
  <section className="bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl p-6 shadow-sm">
    <div className="flex items-center justify-between mb-4">
      <h2 className="text-xl font-bold text-stone-900 dark:text-stone-100">{title}</h2>
      {actions}
    </div>
    {children}
  </section>
);

const Stat = ({ label, value, loading, error }) => (
  <div className="bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-xl p-4 shadow-sm">
    <p className="text-xs font-bold uppercase text-stone-400 mb-2">{label}</p>
    {loading ? (
      <div className="h-8 w-1/2 bg-stone-200 dark:bg-stone-800 rounded-md animate-pulse" />
    ) : error ? (
      <p className="text-red-500 text-sm font-mono">{error}</p>
    ) : (
      <p className="text-3xl font-bold text-amber-600">{value ?? "–"}</p>
    )}
  </div>
);

const useFetch = (path, opts = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`${API_BASE}${path}`, opts)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((json) => {
        if (!cancelled) {
          setData(json);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "request failed");
          setData(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [path]);
  return { data, loading, error, setData };
};

const formatDate = (ts) => {
  if (!ts) return "–";
  try {
    const d = new Date(ts * 1000);
    return d.toLocaleString();
  } catch (e) {
    return "–";
  }
};

const groupByFolder = (items = []) => {
  const tree = {};
  items.forEach((f) => {
    const parts = f.path.split("/");
    let node = tree;
    parts.forEach((p, idx) => {
      if (!node[p]) node[p] = { __children: {} };
      if (idx === parts.length - 1) node[p].__file = f;
      node = node[p].__children;
    });
  });
  return tree;
};

const FolderNode = ({ name, node, onSelect, depth = 0 }) => {
  const isFile = !!node.__file;
  const children = node.__children || {};
  return (
    <div style={{ marginLeft: depth * 12 }}>
      <div
        className={`flex items-center gap-2 py-1 cursor-pointer ${isFile ? "hover:text-amber-600" : "font-semibold"}`}
        onClick={() => {
          if (isFile && node.__file) onSelect(node.__file.path);
        }}
      >
        <span>{name}</span>
        {isFile && node.__file?.chunks !== undefined && (
          <span className="text-xs text-stone-500">{node.__file.chunks ?? "?"} ch</span>
        )}
      </div>
      {!isFile &&
        Object.entries(children).map(([childName, child]) => (
          <FolderNode key={childName} name={childName} node={child} onSelect={onSelect} depth={depth + 1} />
        ))}
    </div>
  );
};

const useSSE = () => {
  const [log, setLog] = useState([]);
  const [busy, setBusy] = useState(false);
  const run = async (path, { method = "POST", body } = {}) => {
    setBusy(true);
    setLog([]);
    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    const reader = res.body?.getReader();
    const decoder = new TextDecoder();
    while (reader) {
      const { value, done } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      const lines = chunk
        .split("\n\n")
        .map((l) => l.replace(/^data:\s?/, "").trim())
        .filter(Boolean);
      setLog((prev) => [...prev, ...lines]);
    }
    setBusy(false);
  };
  return { log, busy, run };
};

const IngestPanel = ({ onReindex }) => {
  const [urls, setUrls] = useState("");
  const { log, busy, run } = useSSE();
  const [pastePath, setPastePath] = useState("pasted-note.md");
  const [pasteBody, setPasteBody] = useState("# Title\n\nContent...");
  const [uploadStatus, setUploadStatus] = useState(null);
  const [reindexAfter, setReindexAfter] = useState(false);

  const saveContent = async (path, content) => {
    await fetch(`${API_BASE}/api/content/write`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path, content }),
    });
    if (reindexAfter) {
      await fetch(`${API_BASE}/api/index/file`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path }),
      });
    }
  };

  return (
    <Panel title="Ingest">
      <div className="grid md:grid-cols-3 gap-4">
        <div className="space-y-3">
          <label className="text-sm font-bold text-stone-500">URLs (one per line)</label>
          <textarea
            value={urls}
            onChange={(e) => setUrls(e.target.value)}
            className="w-full h-40 p-3 font-mono text-xs bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded-lg"
            placeholder="https://example.com/page"
          />
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() =>
                run("/api/ingest", { method: "POST", body: { urls: urls.split("\n").filter(Boolean) } })
              }
              disabled={busy}
              className="px-4 py-2 rounded-lg bg-stone-900 text-white disabled:opacity-60"
            >
              {busy ? "Ingesting..." : "Ingest URLs"}
            </button>
            <button
              onClick={onReindex}
              className="px-4 py-2 rounded-lg bg-amber-500 text-white disabled:opacity-60"
            >
              Rebuild Index
            </button>
          </div>
        </div>
        <div className="space-y-3">
          <label className="text-sm font-bold text-stone-500">Paste Markdown</label>
          <input
            value={pastePath}
            onChange={(e) => setPastePath(e.target.value)}
            className="w-full p-2 rounded-lg bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700"
            placeholder="folder/note.md"
          />
          <textarea
            value={pasteBody}
            onChange={(e) => setPasteBody(e.target.value)}
            className="w-full h-32 p-3 font-mono text-xs bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded-lg"
          />
          <button
            onClick={async () => {
              await saveContent(pastePath, pasteBody);
              setUploadStatus("Saved pasted content");
            }}
            className="px-4 py-2 rounded-lg bg-stone-900 text-white"
          >
            Save
          </button>
        </div>
        <div className="space-y-3">
          <label className="text-sm font-bold text-stone-500">Upload .md/.txt</label>
          <input
            type="file"
            accept=".md,.txt"
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              const text = await file.text();
              await saveContent(file.name, text);
              setUploadStatus(`Uploaded ${file.name}`);
            }}
            className="w-full text-sm"
          />
          <label className="flex items-center gap-2 text-xs text-stone-500">
            <input
              type="checkbox"
              checked={reindexAfter}
              onChange={(e) => setReindexAfter(e.target.checked)}
            />
            Reindex after save/upload
          </label>
          {uploadStatus && <p className="text-xs text-stone-500">{uploadStatus}</p>}
        </div>
      </div>
      <div className="mt-3">
        <p className="text-sm font-bold text-stone-500 mb-2">Log</p>
        <pre className="w-full h-32 p-3 font-mono text-xs bg-black text-white rounded-lg overflow-y-auto">
          {log.join("\n")}
          {busy && <div className="h-3 w-1/2 bg-stone-800 rounded-md animate-pulse mt-2" />}
        </pre>
      </div>
    </Panel>
  );
};

const IndexPanel = ({ contentList, indexStats }) => {
  const { log, busy, run } = useSSE();
  const lastIndexed = indexStats?.data?.last_indexed;
  const stale =
    (contentList?.data || []).filter((f) => lastIndexed && f.mtime * 1000 > lastIndexed * 1000) || [];
  const reindexFile = async (path) => {
    await fetch(`${API_BASE}/api/index/file`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });
  };
  return (
    <Panel title="Index">
      <div className="flex gap-3 flex-wrap">
        <button
          onClick={() => run("/api/index")}
          disabled={busy}
          className="px-4 py-2 rounded-lg bg-amber-500 text-white disabled:opacity-60"
        >
          {busy ? "Indexing..." : "Rebuild Index"}
        </button>
        <span className="text-sm text-stone-500">
          Last indexed: {lastIndexed ? new Date(lastIndexed * 1000).toLocaleString() : "–"}
        </span>
      </div>
      <pre className="mt-3 w-full h-32 p-3 font-mono text-xs bg-black text-white rounded-lg overflow-y-auto">
        {log.join("\n")}
      </pre>
      <div className="mt-4">
        <h4 className="text-sm font-bold mb-2">Stale files (edited since last index)</h4>
        {stale.length === 0 && <p className="text-sm text-stone-500">None detected.</p>}
        <ul className="space-y-2">
          {stale.slice(0, 10).map((f) => (
            <li
              key={f.path}
              className="flex items-center justify-between bg-stone-100 dark:bg-stone-900 px-3 py-2 rounded-lg text-sm"
            >
              <span className="truncate">{f.path}</span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-stone-500">
                  {new Date(f.mtime * 1000).toLocaleDateString()}
                </span>
                <button
                  onClick={() => reindexFile(f.path)}
                  className="px-3 py-1 rounded bg-amber-500 text-white text-xs"
                >
                  Reindex
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
};

const GeneratePanel = () => {
  const briefs = useFetch("/api/briefs");
  const [selectedBrief, setSelectedBrief] = useState("");
  const [briefContent, setBriefContent] = useState("");
  const [opts, setOpts] = useState({
    model: "",
    fallback: "",
    temp: "0.0",
    seed: "42",
    maxPredict: "3200",
    persona: "",
    skipPublish: true,
    deterministic: true,
  });
  const { log, busy, run } = useSSE();

  useEffect(() => {
    if (!selectedBrief) {
      setBriefContent("");
      return;
    }
    fetch(`${API_BASE}/api/briefs/${encodeURIComponent(selectedBrief)}`)
      .then((r) => r.json())
      .then((d) => setBriefContent(d.content || ""))
      .catch(() => setBriefContent(""));
  }, [selectedBrief]);

  const handleGenerate = () => {
    if (!selectedBrief) return;
    const env = {
      GEN_MODEL: opts.model || undefined,
      GEN_MODEL_FALLBACK: opts.fallback || undefined,
      GEN_TEMPERATURE: opts.deterministic ? "0.0" : opts.temp,
      GEN_SEED: opts.deterministic ? "42" : opts.seed,
      GEN_MAX_PREDICT: opts.maxPredict,
      GEN_PERSONA: opts.persona || undefined,
      SKIP_PUBLISH: opts.skipPublish ? "1" : "0",
    };
    run("/api/generate", { method: "POST", body: { brief_path: selectedBrief, env } });
  };

  return (
    <Panel title="Generate">
      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-3">
          <label className="text-sm font-bold text-stone-500">Brief</label>
          <select
            value={selectedBrief}
            onChange={(e) => setSelectedBrief(e.target.value)}
            className="w-full p-3 bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded-lg"
          >
            <option value="">-- Select a brief --</option>
            {(briefs.data || []).map((b) => (
              <option key={b} value={b}>
                {b.replace("briefs/", "")}
              </option>
            ))}
          </select>
          <textarea
            value={briefContent}
            readOnly
            className="w-full h-48 p-3 font-mono text-xs bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded-lg"
          />
          <div className="grid md:grid-cols-2 gap-3">
            <input
              placeholder="GEN_MODEL"
              value={opts.model}
              onChange={(e) => setOpts({ ...opts, model: e.target.value })}
              className="p-3 rounded-lg bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700"
            />
            <input
              placeholder="GEN_MODEL_FALLBACK"
              value={opts.fallback}
              onChange={(e) => setOpts({ ...opts, fallback: e.target.value })}
              className="p-3 rounded-lg bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700"
            />
            <input
              placeholder="Temperature"
              value={opts.temp}
              onChange={(e) => setOpts({ ...opts, temp: e.target.value })}
              className="p-3 rounded-lg bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700"
              disabled={opts.deterministic}
            />
            <input
              placeholder="Seed"
              value={opts.seed}
              onChange={(e) => setOpts({ ...opts, seed: e.target.value })}
              className="p-3 rounded-lg bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700"
              disabled={opts.deterministic}
            />
            <input
              placeholder="GEN_MAX_PREDICT"
              value={opts.maxPredict}
              onChange={(e) => setOpts({ ...opts, maxPredict: e.target.value })}
              className="p-3 rounded-lg bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700"
            />
            <input
              placeholder="Persona"
              value={opts.persona}
              onChange={(e) => setOpts({ ...opts, persona: e.target.value })}
              className="p-3 rounded-lg bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700"
            />
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={opts.deterministic}
                onChange={(e) => setOpts({ ...opts, deterministic: e.target.checked })}
              />
              Deterministic (temp=0, seed=42)
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={opts.skipPublish}
                onChange={(e) => setOpts({ ...opts, skipPublish: e.target.checked })}
              />
              Skip publish
            </label>
          </div>
          <button
            onClick={handleGenerate}
            disabled={busy || !selectedBrief}
            className="px-4 py-2 rounded-lg bg-stone-900 text-white disabled:opacity-60"
          >
            {busy ? "Generating..." : "Generate Draft"}
          </button>
        </div>
        <div>
          <p className="text-sm font-bold text-stone-500 mb-2">Generation Log</p>
          <pre className="w-full h-72 p-3 font-mono text-xs bg-black text-white rounded-lg overflow-y-auto">
            {log.join("\n")}
            {busy && <div className="h-3 w-1/2 bg-stone-800 rounded-md animate-pulse mt-2" />}
          </pre>
        </div>
      </div>
    </Panel>
  );
};

const PreviewPanel = () => {
  const artifacts = useFetch("/api/artifacts");
  const [slug, setSlug] = useState("");
  const [details, setDetails] = useState(null);
  const briefsIndex = useFetch("/api/briefs/index");
  const regen = useSSE();
  const [minLen, setMinLen] = useState(200);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    if (!slug) {
      setDetails(null);
      return;
    }
    fetch(`${API_BASE}/api/artifacts/${encodeURIComponent(slug)}`)
      .then((r) => r.json())
      .then(setDetails)
      .catch(() => setDetails(null));
  }, [slug]);

  const filteredSlugs = (artifacts.data || []).filter((s) =>
    s.toLowerCase().includes(filter.toLowerCase())
  );
  const meta = briefsIndex.data && slug ? briefsIndex.data[slug] : null;

  const headingsFromMd = (md) => {
    if (!md) return [];
    const matches = [...md.matchAll(/^##\s+(.+)$/gm)].map((m) => m[1].trim());
    return Array.from(new Set(matches));
  };

  const briefPathForSlug = (s) => {
    const idx = briefsIndex.data || {};
    if (idx[s] && idx[s].path) return idx[s].path;
    return `briefs/${s}.yaml`; // best-effort fallback
  };

  const handleRegen = (section) => {
    if (!slug || !section) return;
    const briefPath = briefPathForSlug(slug);
    regen.run("/api/regenerate", {
      body: { brief_path: briefPath, section, min_len: minLen },
    });
  };

  return (
    <Panel title="Preview">
      <div className="flex flex-col md:flex-row gap-3 mb-4">
        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter by slug"
          className="flex-1 p-3 bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded-lg"
        />
        <select
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
          className="flex-1 p-3 bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded-lg"
        >
          <option value="">-- Select a slug --</option>
          {filteredSlugs.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      {slug && (
        <div className="grid md:grid-cols-3 gap-3 mb-4">
          <div className="bg-stone-100 dark:bg-stone-900 rounded-lg p-3 border border-stone-200 dark:border-stone-800">
            <p className="text-sm font-bold mb-1">{slug}</p>
            <p className="text-xs text-stone-500">
              {meta?.title || "Untitled"} {meta?.tags && meta.tags.length ? `• ${meta.tags.join(", ")}` : ""}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <a
              href={details?.paths?.index ? details.paths.index : `artifacts/${slug}/index.html`}
              className="px-3 py-2 rounded-lg bg-amber-500 text-white text-sm"
              target="_blank"
              rel="noreferrer"
            >
              Open Preview
            </a>
            <a
              href={details?.paths?.blog_html ? details.paths.blog_html : `artifacts/${slug}/blog/latest.html`}
              className="px-3 py-2 rounded-lg bg-stone-200 dark:bg-stone-800 text-sm"
              target="_blank"
              rel="noreferrer"
            >
              Blog HTML
            </a>
          </div>
        </div>
      )}
      {details && (
        <div className="grid md:grid-cols-3 gap-3">
          <div className="md:col-span-2">
            <h4 className="font-bold mb-2">Blog (Markdown)</h4>
            <pre className="w-full h-64 p-3 font-mono text-xs bg-stone-100 dark:bg-stone-900 rounded overflow-auto">
              {details.content?.blog_md || "No blog content."}
            </pre>
            {details.content?.blog_md && (
              <div className="mt-2 space-y-2">
                <div className="flex items-center gap-3">
                  <label className="text-xs text-stone-500">Min length</label>
                  <input
                    type="number"
                    value={minLen}
                    onChange={(e) => setMinLen(Number(e.target.value) || 0)}
                    className="w-20 p-2 rounded bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700 text-xs"
                  />
                  {regen.busy && <span className="text-xs text-stone-500">Regenerating…</span>}
                </div>
                <div className="flex flex-wrap gap-2">
                  {headingsFromMd(details.content.blog_md).map((sec) => (
                    <button
                      key={sec}
                      onClick={() => handleRegen(sec)}
                      className="px-3 py-1 rounded-lg bg-stone-200 dark:bg-stone-800 text-xs hover:bg-amber-500 hover:text-white transition-colors"
                    >
                      Regen: {sec}
                    </button>
                  ))}
                </div>
                {regen.log.length > 0 && (
                  <pre className="w-full h-24 p-2 font-mono text-xs bg-black text-white rounded overflow-auto">
                    {regen.log.join("\n")}
                  </pre>
                )}
              </div>
            )}
          </div>
          <div className="space-y-3">
            <div>
              <h4 className="font-bold mb-2">LinkedIn</h4>
              <pre className="w-full h-28 p-3 font-mono text-xs bg-stone-100 dark:bg-stone-900 rounded overflow-auto">
                {details.content?.linkedin_md || "No LinkedIn content."}
              </pre>
            </div>
            <div>
              <h4 className="font-bold mb-2">Instagram</h4>
              <pre className="w-full h-28 p-3 font-mono text-xs bg-stone-100 dark:bg-stone-900 rounded overflow-auto">
                {details.content?.instagram_md || "No Instagram content."}
              </pre>
            </div>
            <div>
              <h4 className="font-bold mb-2">Meta files</h4>
              <pre className="w-full h-28 p-3 font-mono text-xs bg-stone-100 dark:bg-stone-900 rounded overflow-auto">
                {JSON.stringify(details.content?.meta_files || {}, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </Panel>
  );
};

const SettingsPanel = () => {
  const { data, loading, error, setData } = useFetch("/api/settings");
  const models = useFetch("/api/models");
  const [form, setForm] = useState({});

  useEffect(() => {
    if (data) setForm(data);
  }, [data]);

  const handleChange = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  const save = async () => {
    await fetch(`${API_BASE}/api/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    setData(form);
  };

  const renderField = (key, value) => {
    // Model selectors
    if (key === "GEN_MODEL" || key === "GEN_MODEL_FALLBACK") {
      const opts = models.data || [];
      const noneOpt = key === "GEN_MODEL_FALLBACK" ? ["(none)"] : [];
      return (
        <select
          value={value || ""}
          onChange={(e) => handleChange(key, e.target.value === "(none)" ? "" : e.target.value)}
          className="md:col-span-2 p-3 rounded-lg bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700"
        >
          {noneOpt.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
          {opts.length === 0 && <option value={value || ""}>{value || "type a model"}</option>}
          {opts.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      );
    }
    // Sliders for common numeric knobs
    const slider = (min, max, step, type = "number") => {
      const numeric = parseFloat(value) || 0;
      return (
        <div className="md:col-span-2 flex items-center gap-3">
          <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={numeric}
            onChange={(e) => handleChange(key, e.target.value)}
            className="flex-1"
          />
          <input
            type={type}
            value={value}
            onChange={(e) => handleChange(key, e.target.value)}
            className="w-24 p-2 rounded-lg bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700"
          />
        </div>
      );
    };
    if (key === "GEN_TEMPERATURE") return slider(0, 1, 0.05);
    if (key === "GEN_SEED") return slider(0, 1000000, 1, "number");
    if (key === "GEN_MAX_PREDICT") return slider(256, 12000, 128, "number");
    if (key === "GEN_MAX_CTX") return slider(256, 120000, 512, "number");
    if (key === "RETRIEVE_K") return slider(1, 20, 1, "number");
    if (key === "RETRIEVE_MAX_PER_SOURCE") return slider(1, 5, 1, "number");
    // Default text input
    return (
      <input
        value={value}
        onChange={(e) => handleChange(key, e.target.value)}
        className="md:col-span-2 p-3 rounded-lg bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700"
      />
    );
  };

  return (
    <Panel title="Settings (.env)">
      {loading && <p>Loading…</p>}
      {error && <p className="text-red-500">{error}</p>}
      {form && (
        <div className="space-y-3">
          {Object.entries(form).map(([k, v]) => (
            <div key={k} className="grid md:grid-cols-3 gap-2 items-center">
              <label className="text-sm font-bold text-stone-500">{k}</label>
              {renderField(k, v)}
            </div>
          ))}
          <button onClick={save} className="px-4 py-2 rounded-lg bg-stone-900 text-white">
            Save
          </button>
        </div>
      )}
    </Panel>
  );
};

const LoRAPanel = () => {
  const { log, busy, run } = useSSE();
  const { log: splitLog, busy: splitBusy, run: runSplit } = useSSE();
  return (
    <Panel title="LoRA">
      <div className="flex gap-3 mb-3">
        <button
          onClick={() => run("/api/lora/dataset")}
          disabled={busy}
          className="px-4 py-2 rounded-lg bg-stone-900 text-white disabled:opacity-60"
        >
          {busy ? "Building…" : "Build Dataset"}
        </button>
        <button
          onClick={() => runSplit("/api/lora/split")}
          disabled={splitBusy}
          className="px-4 py-2 rounded-lg bg-amber-500 text-white disabled:opacity-60"
        >
          {splitBusy ? "Splitting…" : "Split Train/Val"}
        </button>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        <pre className="w-full h-40 p-3 font-mono text-xs bg-black text-white rounded-lg overflow-y-auto">
          {log.join("\n")}
        </pre>
        <pre className="w-full h-40 p-3 font-mono text-xs bg-black text-white rounded-lg overflow-y-auto">
          {splitLog.join("\n")}
        </pre>
      </div>
    </Panel>
  );
};

const ChecksPanel = () => {
  const [ollama, setOllama] = useState(null);
  const [wp, setWp] = useState(null);
  const models = useFetch("/api/models");

  const check = (endpoint, setter) => {
    fetch(`${API_BASE}${endpoint}`)
      .then((r) => r.json())
      .then(setter)
      .catch((e) => setter({ ok: false, detail: e.message }));
  };

  useEffect(() => {
    check("/api/ollama-check", setOllama);
    check("/api/wp-check", setWp);
  }, []);

  return (
    <Panel title="Checks">
      <div className="flex gap-3 mb-4">
        <button className="px-4 py-2 rounded-lg bg-stone-900 text-white" onClick={() => check("/api/ollama-check", setOllama)}>
          Check Ollama
        </button>
        <button className="px-4 py-2 rounded-lg bg-amber-500 text-white" onClick={() => check("/api/wp-check", setWp)}>
          Check WordPress
        </button>
      </div>
      <div className="grid md:grid-cols-3 gap-3">
        <div className="p-3 rounded-lg border border-stone-200 dark:border-stone-800">
          <h4 className="font-bold mb-2">Ollama</h4>
          <pre className="text-xs">{ollama ? JSON.stringify(ollama, null, 2) : "Waiting for response…"}</pre>
        </div>
        <div className="p-3 rounded-lg border border-stone-200 dark:border-stone-800">
          <h4 className="font-bold mb-2">WordPress</h4>
          <pre className="text-xs">{wp ? JSON.stringify(wp, null, 2) : "Waiting for response…"}</pre>
        </div>
        <div className="p-3 rounded-lg border border-stone-200 dark:border-stone-800">
          <h4 className="font-bold mb-2">Models</h4>
          {models.loading && <p>Loading…</p>}
          {models.error && <p className="text-red-500">{models.error}</p>}
          {!models.loading && !models.error && (
            <ul className="text-xs space-y-1">
              {(models.data || []).map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Panel>
  );
};

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const briefs = useFetch("/api/briefs");
  const artifacts = useFetch("/api/artifacts");
  const models = useFetch("/api/models");
  const indexStats = useFetch("/api/index/stats");
  const contentList = useFetch("/api/content/list");

  const [selectedFile, setSelectedFile] = useState("");
  const [fileBody, setFileBody] = useState("");
  const [fileLoading, setFileLoading] = useState(false);
  const [fileStatus, setFileStatus] = useState(null);
  const [newFilePath, setNewFilePath] = useState("");
  const [newFileBody, setNewFileBody] = useState("# Title\n\nStart writing...");

  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatBusy, setChatBusy] = useState(false);
  const [chatTopK, setChatTopK] = useState(6);
  const [chatFirstParty, setChatFirstParty] = useState(true);
  const quickIndex = useSSE();

  const loadFile = async (path) => {
    if (!path) return;
    setFileLoading(true);
    setFileStatus(null);
    try {
      const res = await fetch(`${API_BASE}/api/content/read`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path }),
      });
      const data = await res.json();
      setFileBody(data.content || "");
    } catch (e) {
      setFileStatus("Failed to load file");
    } finally {
      setFileLoading(false);
    }
  };

  const saveFile = async () => {
    if (!selectedFile) return;
    setFileStatus("Saving...");
    try {
      await fetch(`${API_BASE}/api/content/write`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: selectedFile, content: fileBody }),
      });
      setFileStatus("Saved");
      contentList.setData && contentList.setData((prev) => prev); // trigger rerender
    } catch (e) {
      setFileStatus("Save failed");
    }
  };

  const createFile = async () => {
    if (!newFilePath.trim()) return;
    setFileStatus("Creating...");
    try {
      await fetch(`${API_BASE}/api/content/write`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: newFilePath, content: newFileBody }),
      });
      setFileStatus("Created");
      setSelectedFile(newFilePath.endsWith(".md") ? newFilePath : `${newFilePath}.md`);
      setFileBody(newFileBody);
      contentList.setData &&
        contentList.setData((prev) => {
          if (!prev) return prev;
          return [...prev];
        });
    } catch (e) {
      setFileStatus("Create failed");
    }
  };

  const uploadFile = async (file) => {
    if (!file) return;
    setFileStatus("Uploading...");
    const text = await file.text();
    const path = file.name.endsWith(".md") ? file.name : `${file.name}.md`;
    try {
      await fetch(`${API_BASE}/api/content/write`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path, content: text }),
      });
      setFileStatus(`Uploaded ${path}`);
      contentList.setData && contentList.setData((prev) => (prev ? [...prev] : prev));
    } catch (e) {
      setFileStatus("Upload failed");
    }
  };

const sendChat = async () => {
  if (!chatInput.trim()) return;
  const message = { role: "user", content: chatInput };
  setChatHistory((prev) => [...prev, message]);
  setChatInput("");
    setChatBusy(true);
    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: message.content,
          first_party_only: chatFirstParty,
          top_k: chatTopK,
        }),
      });
      const data = await res.json();
      setChatHistory((prev) => [
        ...prev,
        { role: "assistant", content: data.answer || "No answer", sources: data.sources || [] },
      ]);
    } catch (e) {
      setChatHistory((prev) => [...prev, { role: "assistant", content: "Chat failed", sources: [] }]);
    } finally {
      setChatBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-stone-50 dark:bg-[#0c0a07] text-stone-900 dark:text-stone-50">
      <header className="sticky top-0 z-10 bg-white/80 dark:bg-[#0c0a07]/90 backdrop-blur border-b border-black/5 dark:border-white/5">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-stone-900 dark:bg-white text-white dark:text-stone-900 flex items-center justify-center font-bold">
              CE
            </div>
            <div>
              <p className="text-lg font-bold">Content Engine Dashboard</p>
              <p className="text-xs text-stone-500">PruningMyPothos</p>
            </div>
          </div>
          <div className="flex gap-2">
            {["overview", "ingest", "index", "generate", "preview", "lora", "settings", "checks"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-2 rounded-lg text-sm font-semibold ${
                  activeTab === tab
                    ? "bg-amber-500 text-white"
                    : "bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-200 hover:bg-stone-200 dark:hover:bg-stone-700"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {activeTab === "overview" && (
          <>
            <div className="grid md:grid-cols-4 gap-4">
              <Stat label="Briefs" value={(briefs.data || []).length} loading={briefs.loading} error={briefs.error} />
              <Stat label="Artifacts" value={(artifacts.data || []).length} loading={artifacts.loading} error={artifacts.error} />
              <Stat
                label="Docs"
                value={indexStats.data?.total_files}
                loading={indexStats.loading}
                error={indexStats.error}
              />
              <Stat
                label="Chunks"
                value={indexStats.data?.total_chunks}
                loading={indexStats.loading}
                error={indexStats.error}
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setActiveTab("ingest")}
                className="px-4 py-2 rounded-lg bg-stone-100 dark:bg-stone-800 text-sm font-semibold"
              >
                Ingest URLs
              </button>
              <button
                onClick={() => quickIndex.run("/api/index")}
                className="px-4 py-2 rounded-lg bg-amber-500 text-white text-sm font-semibold disabled:opacity-60"
                disabled={quickIndex.busy}
              >
                {quickIndex.busy ? "Indexing…" : "Rebuild Index"}
              </button>
              <button
                onClick={() => setActiveTab("generate")}
                className="px-4 py-2 rounded-lg bg-stone-100 dark:bg-stone-800 text-sm font-semibold"
              >
                Generate Draft
              </button>
              {quickIndex.log.length > 0 && (
                <span className="text-xs text-stone-500">Index log: {quickIndex.log.slice(-1)[0]}</span>
              )}
            </div>
            <div className="grid lg:grid-cols-3 gap-4">
              <Panel
                title="Knowledge Base"
                actions={
                  <span className="text-xs text-stone-500">
                    Last indexed: {formatDate(indexStats.data?.last_indexed)}
                  </span>
                }
              >
                <p className="text-sm text-stone-600 dark:text-stone-300 mb-3">
                  {indexStats.data?.vdb_backend
                    ? `Vector DB: ${indexStats.data.vdb_backend}`
                    : "Vector DB not detected"}
                </p>
                <div className="space-y-2">
                  <p className="text-xs font-bold text-stone-500">Top files by chunks</p>
                  <ul className="space-y-2">
                    {(indexStats.data?.top_files || []).map((f) => {
                      const max = Math.max(...(indexStats.data?.top_files || []).map((x) => x.chunks || 1), 1);
                      const pct = Math.min(100, Math.round((f.chunks / max) * 100));
                      return (
                        <li key={f.path} className="text-sm bg-stone-100 dark:bg-stone-900 px-3 py-2 rounded-lg">
                          <div className="flex items-center justify-between gap-2">
                            <span className="truncate">{f.path}</span>
                            <span className="text-xs font-mono text-stone-500">{f.chunks} ch</span>
                          </div>
                          <div className="w-full h-2 bg-stone-200 dark:bg-stone-800 rounded mt-1">
                            <div className="h-2 bg-amber-500 rounded" style={{ width: `${pct}%` }}></div>
                          </div>
                        </li>
                      );
                    })}
                    {!indexStats.loading && (!indexStats.data?.top_files || indexStats.data.top_files.length === 0) && (
                      <li className="text-sm text-stone-500">No stats yet.</li>
                    )}
                  </ul>
                </div>
              </Panel>
              <Panel title="Recent docs">
                <ul className="space-y-2">
                  {(contentList.data || []).slice(0, 6).map((f) => (
                    <li
                      key={f.path}
                      className="flex items-center justify-between text-sm bg-stone-100 dark:bg-stone-900 px-3 py-2 rounded-lg cursor-pointer"
                      onClick={() => {
                        setSelectedFile(f.path);
                        loadFile(f.path);
                        setActiveTab("overview");
                      }}
                    >
                      <div className="truncate">{f.path}</div>
                      <div className="text-xs text-stone-500">{new Date(f.mtime * 1000).toLocaleDateString()}</div>
                    </li>
                  ))}
                  {contentList.loading && <li className="text-sm text-stone-500">Loading…</li>}
                  {contentList.error && <li className="text-sm text-red-500">{contentList.error}</li>}
                </ul>
              </Panel>
              <Panel title="Chat (RAG)">
                <div className="h-64 overflow-y-auto space-y-3 mb-3 bg-stone-100 dark:bg-stone-900 rounded-lg p-3">
                  {chatHistory.length === 0 && <p className="text-sm text-stone-500">Ask anything grounded in content/…</p>}
                  {chatHistory.map((m, idx) => (
                    <div key={idx} className="text-sm space-y-1">
                      <p className={m.role === "user" ? "font-semibold" : ""}>{m.content}</p>
                      {m.sources && m.sources.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {m.sources.map((s) => (
                            <button
                              key={s}
                              className="text-xs px-2 py-1 rounded-full bg-stone-200 dark:bg-stone-800 hover:bg-amber-500 hover:text-white transition-colors"
                              onClick={() => {
                                setSelectedFile(s.replace(/^content\//, ""));
                                loadFile(s.replace(/^content\//, ""));
                                setActiveTab("overview");
                              }}
                            >
                              {s.replace(/^content\//, "")}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                  {chatBusy && <p className="text-sm text-stone-500">Thinking…</p>}
                </div>
                <div className="flex items-center gap-3 mb-2 text-xs text-stone-500">
                  <label className="flex items-center gap-1">
                    <input
                      type="checkbox"
                      checked={chatFirstParty}
                      onChange={(e) => setChatFirstParty(e.target.checked)}
                    />
                    First-party only
                  </label>
                  <label className="flex items-center gap-2">
                    Top K
                    <input
                      type="range"
                      min="1"
                      max="12"
                      value={chatTopK}
                      onChange={(e) => setChatTopK(Number(e.target.value))}
                    />
                    <span className="font-mono">{chatTopK}</span>
                  </label>
                </div>
                <div className="flex gap-2">
                  <input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && sendChat()}
                    placeholder="Ask a question about your notes"
                    className="flex-1 p-3 rounded-lg bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700"
                  />
                  <button
                    onClick={sendChat}
                    disabled={chatBusy}
                    className="px-4 py-2 rounded-lg bg-amber-500 text-white disabled:opacity-60"
                  >
                    Send
                  </button>
                </div>
              </Panel>
            </div>
            <Panel
              title="Edit content"
              actions={
                fileStatus ? <span className="text-xs text-stone-500">{fileStatus}</span> : null
              }
            >
              <div className="grid lg:grid-cols-3 gap-4">
                <div className="space-y-3">
                  <label className="text-sm font-bold text-stone-500">Files</label>
                  <div className="h-64 overflow-y-auto bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded-lg p-3">
                    {(contentList.data && Object.keys(groupByFolder(contentList.data)).length > 0 && (
                      Object.entries(groupByFolder(contentList.data)).map(([name, node]) => (
                        <FolderNode
                          key={name}
                          name={name}
                          node={node}
                          onSelect={(p) => {
                            setSelectedFile(p);
                            loadFile(p);
                          }}
                        />
                      ))
                    )) || <p className="text-sm text-stone-500">No files yet.</p>}
                  </div>
                  <div className="space-y-2">
                    <p className="text-xs font-bold text-stone-500">New doc</p>
                    <input
                      value={newFilePath}
                      onChange={(e) => setNewFilePath(e.target.value)}
                      placeholder="folder/new-doc.md"
                      className="w-full p-3 rounded-lg bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700"
                    />
                    <textarea
                      value={newFileBody}
                      onChange={(e) => setNewFileBody(e.target.value)}
                      className="w-full h-24 p-3 font-mono text-xs bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded-lg"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={createFile}
                        className="px-4 py-2 rounded-lg bg-stone-900 text-white"
                      >
                        Create
                      </button>
                      <label className="px-4 py-2 rounded-lg bg-amber-500 text-white cursor-pointer">
                        Upload
                        <input
                          type="file"
                          accept=".md,.txt"
                          className="hidden"
                          onChange={(e) => uploadFile(e.target.files?.[0])}
                        />
                      </label>
                    </div>
                  </div>
                </div>
                <div className="lg:col-span-2 flex flex-col h-full">
                  <textarea
                    value={fileBody}
                    onChange={(e) => setFileBody(e.target.value)}
                    className="w-full h-64 p-3 font-mono text-xs bg-stone-100 dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded-lg"
                    placeholder="Select a file to edit"
                  />
                  <div className="flex gap-3 mt-3">
                    <button
                      onClick={saveFile}
                      disabled={!selectedFile || fileLoading}
                      className="px-4 py-2 rounded-lg bg-stone-900 text-white disabled:opacity-60"
                    >
                      {fileLoading ? "Saving..." : "Save"}
                    </button>
                    <button
                      onClick={async () => {
                        if (!selectedFile) return;
                        setFileStatus("Reindexing...");
                        try {
                          await fetch(`${API_BASE}/api/index/file`, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ path: selectedFile }),
                          });
                          setFileStatus("Reindexed");
                        } catch (e) {
                          setFileStatus("Reindex failed");
                        }
                      }}
                      disabled={!selectedFile}
                      className="px-4 py-2 rounded-lg bg-amber-500 text-white disabled:opacity-60"
                    >
                      Reindex file
                    </button>
                  </div>
                </div>
              </div>
            </Panel>
          </>
        )}
        {activeTab === "ingest" && <IngestPanel onReindex={() => setActiveTab("index")} />}
        {activeTab === "index" && <IndexPanel contentList={contentList} indexStats={indexStats} />}
        {activeTab === "generate" && <GeneratePanel />}
        {activeTab === "preview" && <PreviewPanel />}
        {activeTab === "lora" && <LoRAPanel />}
        {activeTab === "settings" && <SettingsPanel />}
        {activeTab === "checks" && <ChecksPanel />}
      </main>
    </div>
  );
}
