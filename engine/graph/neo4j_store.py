import os
import datetime
from typing import Any, Dict, List, Optional

try:
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover
    GraphDatabase = None  # type: ignore


REQUIRED_KEYS = ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD")


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(name, default)
    if val is None:
        return None
    return str(val).strip() or None


def is_configured() -> bool:
    if GraphDatabase is None:
        return False
    return all(_get_env(k) for k in REQUIRED_KEYS)


def _driver():
    if GraphDatabase is None:
        raise RuntimeError("neo4j driver not installed")
    uri = _get_env("NEO4J_URI")
    user = _get_env("NEO4J_USER")
    password = _get_env("NEO4J_PASSWORD")
    if not (uri and user and password):
        raise RuntimeError("graph not configured")
    return GraphDatabase.driver(uri, auth=(user, password))


def graph_status() -> Dict[str, Any]:
    if GraphDatabase is None:
        return {"ok": False, "detail": "neo4j driver not installed"}
    missing = [k for k in REQUIRED_KEYS if not _get_env(k)]
    if missing:
        return {"ok": False, "detail": "graph not configured", "missing": missing}
    database = _get_env("NEO4J_DATABASE", "neo4j")
    try:
        with _driver() as drv:
            with drv.session(database=database) as session:
                session.run("RETURN 1").single()
        return {"ok": True, "database": database}
    except Exception as exc:
        return {"ok": False, "detail": str(exc)}


def _node_label(node: Dict[str, Any]) -> str:
    for key in ("title", "label", "slug", "path", "url", "name", "id"):
        if node.get(key):
            return str(node[key])
    return "node"


def fetch_graph(limit: int = 400) -> Dict[str, Any]:
    if not is_configured():
        return {"nodes": [], "links": []}
    database = _get_env("NEO4J_DATABASE", "neo4j")
    with _driver() as drv:
        with drv.session(database=database) as session:
            nodes = session.run(
                "MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props LIMIT $limit",
                limit=limit,
            ).data()
            rels = session.run(
                "MATCH (a)-[r]->(b) RETURN elementId(a) AS source, elementId(b) AS target, type(r) AS type LIMIT $limit",
                limit=limit,
            ).data()
    normalized_nodes = []
    for row in nodes:
        labels = row.get("labels") or []
        props = row.get("props") or {}
        node_type = labels[0] if labels else "Node"
        normalized_nodes.append({
            "id": row.get("id"),
            "type": node_type,
            "label": _node_label(props),
            "meta": props,
        })
    normalized_links = []
    for row in rels:
        normalized_links.append({
            "source": row.get("source"),
            "target": row.get("target"),
            "type": row.get("type"),
        })
    return {"nodes": normalized_nodes, "links": normalized_links}


def record_run(
    *,
    brief: Dict[str, Any],
    slug: str,
    brief_path: str,
    status: str,
    reason: Optional[str] = None,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
) -> Dict[str, Any]:
    if not is_configured():
        return {"ok": False, "detail": "graph not configured"}

    database = _get_env("NEO4J_DATABASE", "neo4j")
    started = started_at or datetime.datetime.utcnow().isoformat()
    finished = finished_at or datetime.datetime.utcnow().isoformat()
    run_id = f"run:{slug}:{started}"
    tags = brief.get("tags") or []
    persona = brief.get("persona")
    title = brief.get("title")
    sources = []
    sources_meta = brief.get("sources") or {}
    if isinstance(sources_meta, dict):
        sources = sources_meta.get("urls") or sources_meta.get("links") or []
    if not isinstance(sources, list):
        sources = []

    cypher = """
    MERGE (b:Brief {path: $brief_path})
      ON CREATE SET b.title = $title, b.slug = $slug
      ON MATCH SET b.title = coalesce(b.title, $title)
    MERGE (r:Run {id: $run_id})
      SET r.status = $status,
          r.reason = $reason,
          r.started_at = $started_at,
          r.finished_at = $finished_at,
          r.slug = $slug,
          r.title = $title
    MERGE (b)-[:HAS_RUN]->(r)
    """

    cypher_tags = """
    UNWIND $tags AS tag
      MERGE (t:Topic {name: tag})
      MERGE (r)-[:TAGGED]->(t)
    """

    cypher_persona = """
    MERGE (p:Persona {name: $persona})
    MERGE (r)-[:USES_PERSONA]->(p)
    """

    cypher_sources = """
    UNWIND $sources AS url
      MERGE (s:Source {url: url})
      MERGE (r)-[:USES_SOURCE]->(s)
    """

    with _driver() as drv:
        with drv.session(database=database) as session:
            session.run(
                cypher,
                brief_path=brief_path,
                title=title,
                slug=slug,
                run_id=run_id,
                status=status,
                reason=reason,
                started_at=started,
                finished_at=finished,
            )
            if tags:
                session.run(cypher_tags, tags=tags)
            if persona:
                session.run(cypher_persona, persona=persona)
            if sources:
                session.run(cypher_sources, sources=sources)

    return {"ok": True, "run_id": run_id}
