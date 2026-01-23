import React, { useEffect, useMemo, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const Panel = ({ title, children, actions }) => (
  <section className="panel">
    <div className="panel-header">
      <h2 className="panel-title">{title}</h2>
      {actions ? <div className="panel-meta">{actions}</div> : null}
    </div>
    {children}
  </section>
);

const Stat = ({ label, value, loading, error }) => (
  <div className="stat-card">
    <p className="stat-label">{label}</p>
    {loading ? (
      <div className="stat-skeleton" />
    ) : error ? (
      <p className="text-danger text-sm mono">{error}</p>
    ) : (
      <p className="stat-value">{value ?? "–"}</p>
    )}
  </div>
);

const useFetch = (path, opts = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [nonce, setNonce] = useState(0);
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
  }, [path, nonce]);
  return { data, loading, error, setData, refresh: () => setNonce((n) => n + 1) };
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
        className={`flex items-center gap-2 py-1 cursor-pointer ${isFile ? "hover-accent" : "font-semibold"}`}
        onClick={() => {
          if (isFile && node.__file) onSelect(node.__file.path);
        }}
      >
        <span>{name}</span>
        {isFile && node.__file?.chunks !== undefined && (
          <span className="text-xs text-muted">{node.__file.chunks ?? "?"} ch</span>
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
          <label className="text-sm font-bold text-muted">URLs (one per line)</label>
          <textarea
            value={urls}
            onChange={(e) => setUrls(e.target.value)}
            className="w-full h-40 field field-soft mono text-xs"
            placeholder="https://example.com/page"
          />
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() =>
                run("/api/ingest", { method: "POST", body: { urls: urls.split("\n").filter(Boolean) } })
              }
              disabled={busy}
              className="btn btn-primary"
            >
              {busy ? "Ingesting..." : "Ingest URLs"}
            </button>
            <button
              onClick={onReindex}
              className="btn btn-accent"
            >
              Rebuild Index
            </button>
          </div>
        </div>
        <div className="space-y-3">
          <label className="text-sm font-bold text-muted">Paste Markdown</label>
          <input
            value={pastePath}
            onChange={(e) => setPastePath(e.target.value)}
            className="field w-full"
            placeholder="folder/note.md"
          />
          <textarea
            value={pasteBody}
            onChange={(e) => setPasteBody(e.target.value)}
            className="w-full h-32 field field-soft mono text-xs"
          />
          <button
            onClick={async () => {
              await saveContent(pastePath, pasteBody);
              setUploadStatus("Saved pasted content");
            }}
            className="btn btn-primary"
          >
            Save
          </button>
        </div>
        <div className="space-y-3">
          <label className="text-sm font-bold text-muted">Upload .md/.txt</label>
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
          <label className="flex items-center gap-2 text-xs text-muted">
            <input
              type="checkbox"
              checked={reindexAfter}
              onChange={(e) => setReindexAfter(e.target.checked)}
            />
            Reindex after save/upload
          </label>
          {uploadStatus && <p className="text-xs text-muted">{uploadStatus}</p>}
        </div>
      </div>
      <div className="mt-3">
        <p className="text-sm font-bold text-muted mb-2">Log</p>
        <pre className="w-full h-32 mono text-xs scroll-panel overflow-y-auto">
          {log.join("\n")}
          {busy && <div className="stat-skeleton mt-2" />}
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
          className="btn btn-accent"
        >
          {busy ? "Indexing..." : "Rebuild Index"}
        </button>
        <span className="text-sm text-muted">
          Last indexed: {lastIndexed ? new Date(lastIndexed * 1000).toLocaleString() : "–"}
        </span>
      </div>
      <pre className="mt-3 w-full h-32 mono text-xs scroll-panel overflow-y-auto">
        {log.join("\n")}
      </pre>
      <div className="mt-4">
        <h4 className="text-sm font-bold mb-2">Stale files (edited since last index)</h4>
        {stale.length === 0 && <p className="text-sm text-muted">None detected.</p>}
        <ul className="space-y-2">
          {stale.slice(0, 10).map((f) => (
            <li key={f.path} className="flex items-center justify-between list-card text-sm">
              <span className="truncate">{f.path}</span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted">
                  {new Date(f.mtime * 1000).toLocaleDateString()}
                </span>
                <button
                  onClick={() => reindexFile(f.path)}
                  className="chip chip-accent"
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

const GraphPanel = () => {
  const graph = useFetch("/api/graph");
  const [filter, setFilter] = useState("all");
  const [selected, setSelected] = useState(null);
  const [dims, setDims] = useState({ w: 960, h: 520 });

  useEffect(() => {
    const update = () => {
      const w = Math.min(1120, Math.max(320, window.innerWidth - 64));
      const h = window.innerWidth < 768 ? 420 : 520;
      setDims({ w, h });
    };
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  const nodes = graph.data?.nodes || [];
  const links = graph.data?.links || [];
  const types = useMemo(() => Array.from(new Set(nodes.map((n) => n.type))).sort(), [nodes]);

  const visibleNodes = useMemo(() => {
    if (filter === "all") return nodes;
    return nodes.filter((n) => n.type === filter);
  }, [nodes, filter]);

  const visibleNodeIds = useMemo(() => new Set(visibleNodes.map((n) => n.id)), [visibleNodes]);

  const visibleLinks = useMemo(
    () => links.filter((l) => visibleNodeIds.has(l.source) && visibleNodeIds.has(l.target)),
    [links, visibleNodeIds]
  );

  const colorMap = {
    Brief: "#0d9488",
    Run: "#f59e0b",
    Topic: "#22c55e",
    Persona: "#3b82f6",
    Source: "#f97316",
  };

  return (
    <Panel
      title="Knowledge Graph"
      actions={
        <div className="flex items-center gap-2 text-xs text-muted">
          <span>Nodes: {visibleNodes.length}</span>
          <span>•</span>
          <span>Links: {visibleLinks.length}</span>
          <button className="btn btn-outline" onClick={() => graph.refresh()}>Refresh</button>
        </div>
      }
    >
      <div className="flex flex-wrap gap-2 mb-3">
        <button
          onClick={() => setFilter("all")}
          className={`chip ${filter === "all" ? "chip-active" : ""}`}
        >
          All
        </button>
        {types.map((t) => (
          <button
            key={t}
            onClick={() => setFilter(t)}
            className={`chip ${filter === t ? "chip-active" : ""}`}
          >
            {t}
          </button>
        ))}
      </div>
      <div className="grid lg:grid-cols-[2fr_1fr] gap-4">
        <div className="panel-inner">
          {graph.loading && <p className="text-sm text-muted">Loading graph…</p>}
          {graph.error && <p className="text-sm text-danger">{graph.error}</p>}
          {!graph.loading && visibleNodes.length === 0 && (
            <p className="text-sm text-muted">No graph data yet. Run a brief to populate Neo4j.</p>
          )}
          {visibleNodes.length > 0 && (
            <ForceGraph2D
              width={dims.w}
              height={dims.h}
              graphData={{ nodes: visibleNodes, links: visibleLinks }}
              nodeLabel={(node) => `${node.type}: ${node.label}`}
              nodeColor={(node) => colorMap[node.type] || "#94a3b8"}
              linkColor={() => "rgba(148, 163, 184, 0.4)"}
              linkDirectionalParticles={2}
              linkDirectionalParticleWidth={1.2}
              linkCurvature={0.12}
              onNodeClick={(node) => setSelected(node)}
            />
          )}
        </div>
        <div className="space-y-3">
          <div className="list-card">
            <p className="text-xs text-muted">Selected node</p>
            {selected ? (
              <div className="mt-2 space-y-1">
                <p className="font-semibold">{selected.label}</p>
                <p className="text-xs text-muted">{selected.type}</p>
                {selected.meta?.path && (
                  <p className="text-xs text-muted break-all">Path: {selected.meta.path}</p>
                )}
                {selected.meta?.url && (
                  <p className="text-xs text-muted break-all">URL: {selected.meta.url}</p>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted mt-2">Click a node to inspect it.</p>
            )}
          </div>
          <div className="list-card">
            <p className="text-xs text-muted mb-2">Legend</p>
            <div className="space-y-2 text-xs">
              {Object.entries(colorMap).map(([type, color]) => (
                <div key={type} className="flex items-center gap-2">
                  <span className="inline-block w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                  <span>{type}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
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
          <label className="text-sm font-bold text-muted">Brief</label>
          <select
            value={selectedBrief}
            onChange={(e) => setSelectedBrief(e.target.value)}
            className="field w-full"
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
            className="w-full h-48 field field-soft mono text-xs"
          />
          <div className="grid md:grid-cols-2 gap-3">
            <input
              placeholder="GEN_MODEL"
              value={opts.model}
              onChange={(e) => setOpts({ ...opts, model: e.target.value })}
              className="field field-soft"
            />
            <input
              placeholder="GEN_MODEL_FALLBACK"
              value={opts.fallback}
              onChange={(e) => setOpts({ ...opts, fallback: e.target.value })}
              className="field field-soft"
            />
            <input
              placeholder="Temperature"
              value={opts.temp}
              onChange={(e) => setOpts({ ...opts, temp: e.target.value })}
              className="field field-soft"
              disabled={opts.deterministic}
            />
            <input
              placeholder="Seed"
              value={opts.seed}
              onChange={(e) => setOpts({ ...opts, seed: e.target.value })}
              className="field field-soft"
              disabled={opts.deterministic}
            />
            <input
              placeholder="GEN_MAX_PREDICT"
              value={opts.maxPredict}
              onChange={(e) => setOpts({ ...opts, maxPredict: e.target.value })}
              className="field field-soft"
            />
            <input
              placeholder="Persona"
              value={opts.persona}
              onChange={(e) => setOpts({ ...opts, persona: e.target.value })}
              className="field field-soft"
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
            className="btn btn-primary"
          >
            {busy ? "Generating..." : "Generate Draft"}
          </button>
        </div>
        <div>
          <p className="text-sm font-bold text-muted mb-2">Generation Log</p>
          <pre className="w-full h-72 mono text-xs scroll-panel overflow-y-auto">
            {log.join("\n")}
            {busy && <div className="stat-skeleton mt-2" />}
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
          className="flex-1 field"
        />
        <select
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
          className="flex-1 field"
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
          <div className="scroll-panel">
            <p className="text-sm font-bold mb-1">{slug}</p>
            <p className="text-xs text-muted">
              {meta?.title || "Untitled"} {meta?.tags && meta.tags.length ? `• ${meta.tags.join(", ")}` : ""}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <a
              href={details?.paths?.index ? details.paths.index : `artifacts/${slug}/index.html`}
              className="btn btn-accent"
              target="_blank"
              rel="noreferrer"
            >
              Open Preview
            </a>
            <a
              href={details?.paths?.blog_html ? details.paths.blog_html : `artifacts/${slug}/blog/latest.html`}
              className="btn btn-outline"
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
            <pre className="w-full h-64 mono text-xs scroll-panel overflow-auto">
              {details.content?.blog_md || "No blog content."}
            </pre>
            {details.content?.blog_md && (
              <div className="mt-2 space-y-2">
                <div className="flex items-center gap-3">
                  <label className="text-xs text-muted">Min length</label>
                  <input
                    type="number"
                    value={minLen}
                    onChange={(e) => setMinLen(Number(e.target.value) || 0)}
                    className="w-20 field field-soft text-xs"
                  />
                  {regen.busy && <span className="text-xs text-muted">Regenerating…</span>}
                </div>
                <div className="flex flex-wrap gap-2">
                  {headingsFromMd(details.content.blog_md).map((sec) => (
                    <button key={sec} onClick={() => handleRegen(sec)} className="chip">
                      Regen: {sec}
                    </button>
                  ))}
                </div>
                {regen.log.length > 0 && (
                  <pre className="w-full h-24 mono text-xs scroll-panel overflow-auto">
                    {regen.log.join("\n")}
                  </pre>
                )}
              </div>
            )}
          </div>
          <div className="space-y-3">
            <div>
              <h4 className="font-bold mb-2">LinkedIn</h4>
              <pre className="w-full h-28 mono text-xs scroll-panel overflow-auto">
                {details.content?.linkedin_md || "No LinkedIn content."}
              </pre>
            </div>
            <div>
              <h4 className="font-bold mb-2">Instagram</h4>
              <pre className="w-full h-28 mono text-xs scroll-panel overflow-auto">
                {details.content?.instagram_md || "No Instagram content."}
              </pre>
            </div>
            <div>
              <h4 className="font-bold mb-2">Meta files</h4>
              <pre className="w-full h-28 mono text-xs scroll-panel overflow-auto">
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
          className="md:col-span-2 field field-soft"
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
            className="w-24 field field-soft"
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
        className="md:col-span-2 field field-soft"
      />
    );
  };

  return (
    <Panel title="Settings (.env)">
      {loading && <p>Loading…</p>}
      {error && <p className="text-danger">{error}</p>}
      {form && (
        <div className="space-y-3">
          {Object.entries(form).map(([k, v]) => (
            <div key={k} className="grid md:grid-cols-3 gap-2 items-center">
              <label className="text-sm font-bold text-muted">{k}</label>
              {renderField(k, v)}
            </div>
          ))}
          <button onClick={save} className="btn btn-primary">
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
          className="btn btn-primary"
        >
          {busy ? "Building…" : "Build Dataset"}
        </button>
        <button
          onClick={() => runSplit("/api/lora/split")}
          disabled={splitBusy}
          className="btn btn-accent"
        >
          {splitBusy ? "Splitting…" : "Split Train/Val"}
        </button>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        <pre className="w-full h-40 mono text-xs scroll-panel overflow-y-auto">
          {log.join("\n")}
        </pre>
        <pre className="w-full h-40 mono text-xs scroll-panel overflow-y-auto">
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
        <button className="btn btn-primary" onClick={() => check("/api/ollama-check", setOllama)}>
          Check Ollama
        </button>
        <button className="btn btn-accent" onClick={() => check("/api/wp-check", setWp)}>
          Check WordPress
        </button>
      </div>
      <div className="grid md:grid-cols-3 gap-3">
        <div className="list-card">
          <h4 className="font-bold mb-2">Ollama</h4>
          <pre className="text-xs">{ollama ? JSON.stringify(ollama, null, 2) : "Waiting for response…"}</pre>
        </div>
        <div className="list-card">
          <h4 className="font-bold mb-2">WordPress</h4>
          <pre className="text-xs">{wp ? JSON.stringify(wp, null, 2) : "Waiting for response…"}</pre>
        </div>
        <div className="list-card">
          <h4 className="font-bold mb-2">Models</h4>
          {models.loading && <p>Loading…</p>}
          {models.error && <p className="text-danger">{models.error}</p>}
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
    <div className="app-shell">
      <header className="sticky top-0 z-10 app-header">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="brand-mark">CE</div>
            <div>
              <p className="text-lg font-bold">Content Engine Dashboard</p>
              <p className="text-xs text-muted">PruningMyPothos</p>
            </div>
          </div>
          <div className="flex gap-2 flex-wrap justify-end">
            {["overview", "ingest", "index", "generate", "preview", "graph", "lora", "settings", "checks"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`tab-button ${activeTab === tab ? "tab-button-active" : ""}`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-6 fade-up">
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
            <div className="flex flex-wrap gap-2 items-center">
              <button onClick={() => setActiveTab("ingest")} className="btn btn-outline">
                Ingest URLs
              </button>
              <button
                onClick={() => quickIndex.run("/api/index")}
                className="btn btn-accent"
                disabled={quickIndex.busy}
              >
                {quickIndex.busy ? "Indexing…" : "Rebuild Index"}
              </button>
              <button onClick={() => setActiveTab("generate")} className="btn btn-outline">
                Generate Draft
              </button>
              {quickIndex.log.length > 0 && (
                <span className="text-xs text-muted">Index log: {quickIndex.log.slice(-1)[0]}</span>
              )}
            </div>
            <div className="grid lg:grid-cols-3 gap-4">
              <Panel
                title="Knowledge Base"
                actions={<span>Last indexed: {formatDate(indexStats.data?.last_indexed)}</span>}
              >
                <p className="text-sm text-muted mb-3">
                  {indexStats.data?.vdb_backend
                    ? `Vector DB: ${indexStats.data.vdb_backend}`
                    : "Vector DB not detected"}
                </p>
                <div className="space-y-2">
                  <p className="text-xs font-bold text-muted">Top files by chunks</p>
                  <ul className="space-y-2">
                    {(indexStats.data?.top_files || []).map((f) => {
                      const max = Math.max(...(indexStats.data?.top_files || []).map((x) => x.chunks || 1), 1);
                      const pct = Math.min(100, Math.round((f.chunks / max) * 100));
                      return (
                        <li key={f.path} className="text-sm list-card">
                          <div className="flex items-center justify-between gap-2">
                            <span className="truncate">{f.path}</span>
                            <span className="text-xs mono text-muted">{f.chunks} ch</span>
                          </div>
                          <div className="progress-track mt-1">
                            <div className="progress-bar" style={{ width: `${pct}%` }}></div>
                          </div>
                        </li>
                      );
                    })}
                    {!indexStats.loading && (!indexStats.data?.top_files || indexStats.data.top_files.length === 0) && (
                      <li className="text-sm text-muted">No stats yet.</li>
                    )}
                  </ul>
                </div>
              </Panel>
              <Panel title="Recent docs">
                <ul className="space-y-2">
                  {(contentList.data || []).slice(0, 6).map((f) => (
                    <li
                      key={f.path}
                      className="flex items-center justify-between text-sm list-card cursor-pointer"
                      onClick={() => {
                        setSelectedFile(f.path);
                        loadFile(f.path);
                        setActiveTab("overview");
                      }}
                    >
                      <div className="truncate">{f.path}</div>
                      <div className="text-xs text-muted">{new Date(f.mtime * 1000).toLocaleDateString()}</div>
                    </li>
                  ))}
                  {contentList.loading && <li className="text-sm text-muted">Loading…</li>}
                  {contentList.error && <li className="text-sm text-danger">{contentList.error}</li>}
                </ul>
              </Panel>
              <Panel title="Chat (RAG)">
                <div className="h-64 overflow-y-auto space-y-3 mb-3 scroll-panel">
                  {chatHistory.length === 0 && <p className="text-sm text-muted">Ask anything grounded in content/…</p>}
                  {chatHistory.map((m, idx) => (
                    <div key={idx} className="text-sm space-y-1">
                      <p className={m.role === "user" ? "font-semibold" : ""}>{m.content}</p>
                      {m.sources && m.sources.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {m.sources.map((s) => (
                            <button
                              key={s}
                              className="chip"
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
                  {chatBusy && <p className="text-sm text-muted">Thinking…</p>}
                </div>
                <div className="flex items-center gap-3 mb-2 text-xs text-muted">
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
                    <span className="mono">{chatTopK}</span>
                  </label>
                </div>
                <div className="flex gap-2">
                  <input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && sendChat()}
                    placeholder="Ask a question about your notes"
                    className="flex-1 field"
                  />
                  <button
                    onClick={sendChat}
                    disabled={chatBusy}
                    className="btn btn-accent"
                  >
                    Send
                  </button>
                </div>
              </Panel>
            </div>
            <Panel
              title="Edit content"
              actions={
                fileStatus ? <span>{fileStatus}</span> : null
              }
            >
              <div className="grid lg:grid-cols-3 gap-4">
                <div className="space-y-3">
                  <label className="text-sm font-bold text-muted">Files</label>
                  <div className="h-64 overflow-y-auto scroll-panel">
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
                    )) || <p className="text-sm text-muted">No files yet.</p>}
                  </div>
                  <div className="space-y-2">
                    <p className="text-xs font-bold text-muted">New doc</p>
                    <input
                      value={newFilePath}
                      onChange={(e) => setNewFilePath(e.target.value)}
                      placeholder="folder/new-doc.md"
                      className="field w-full"
                    />
                    <textarea
                      value={newFileBody}
                      onChange={(e) => setNewFileBody(e.target.value)}
                      className="w-full h-24 field field-soft mono text-xs"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={createFile}
                        className="btn btn-primary"
                      >
                        Create
                      </button>
                      <label className="btn btn-accent cursor-pointer">
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
                    className="w-full h-64 field field-soft mono text-xs"
                    placeholder="Select a file to edit"
                  />
                  <div className="flex gap-3 mt-3">
                    <button
                      onClick={saveFile}
                      disabled={!selectedFile || fileLoading}
                      className="btn btn-primary"
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
                      className="btn btn-accent"
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
        {activeTab === "graph" && <GraphPanel />}
        {activeTab === "lora" && <LoRAPanel />}
        {activeTab === "settings" && <SettingsPanel />}
        {activeTab === "checks" && <ChecksPanel />}
      </main>
    </div>
  );
}
