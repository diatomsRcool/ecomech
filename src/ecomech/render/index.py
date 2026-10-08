"""Generate EcoMech index pages from the KB.

Produces:
  pages/index.html          — site homepage
  pages/processes/index.html — full process listing

Usage:
    uv run python -m ecomech.render.index
    uv run python -m ecomech.render.index --kb kb/processes --out pages
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, select_autoescape

# ---------------------------------------------------------------------------
# Category map — process file stem → display category
# Ungrouped entries fall into "Other".
# ---------------------------------------------------------------------------

_CATEGORIES: dict[str, list[str]] = {
    "Nutrient Cycling": [
        "Nitrogen_Cycling", "Phosphorus_Cycling", "Carbon_Cycling", "Sulfur_Cycling",
        "Iron_Cycling", "Methane_Cycling", "Redox_Dynamics",
    ],
    "Primary Production": [
        "Terrestrial_Primary_Production", "Marine_Primary_Production",
        "Marine_Benthic_Primary_Production",
    ],
    "Decomposition": [
        "Litter_Decomposition",
    ],
    "Trophic Interactions": [
        "Herbivory", "Predation", "Detritivory",
    ],
    "Symbioses": [
        "Mycorrhizal_Association", "Root_Nodule_Symbiosis", "Coral_Zooxanthellae_Symbiosis",
    ],
    "Disturbance & Succession": [
        "Wildfire_Succession", "Gap_Dynamics", "Flood_Pulse",
    ],
    "Ecosystem Services": [
        "Pollination", "Seed_Dispersal", "Water_Filtration", "Carbon_Sequestration",
    ],
}

# Reverse lookup: stem → category name
_STEM_TO_CATEGORY: dict[str, str] = {
    stem: cat for cat, stems in _CATEGORIES.items() for stem in stems
}


def _excerpt(text: str, chars: int = 180) -> str:
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    return text[:chars].rsplit(" ", 1)[0] + "…" if len(text) > chars else text


def load_processes(kb_dir: Path) -> list[dict[str, Any]]:
    """Load all process YAML files and return a sorted list of summaries."""
    entries = []
    for f in sorted(kb_dir.glob("*.yaml")):
        data = yaml.safe_load(f.read_text())
        if not isinstance(data, dict):
            continue
        pt = data.get("process_term") or {}
        entries.append({
            "stem": f.stem,
            "name": data.get("name", f.stem),
            "id": pt.get("id") or data.get("id", ""),
            "label": pt.get("label", ""),
            "description": _excerpt(data.get("description", "")),
            "ecological_scale": data.get("ecological_scale", ""),
            "mechanism_count": len(data.get("mechanisms") or []),
            "category": _STEM_TO_CATEGORY.get(f.stem, "Other"),
            "href": f"{f.stem}.html",
        })
    return entries


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

_SHARED_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 15px; line-height: 1.6; color: #1a1a1a; background: #f7f9f7;
}
a { color: #2d6a4f; text-decoration: none; }
a:hover { text-decoration: underline; }
.site-header {
  background: #1b4332; color: #fff;
  padding: 0.5rem 2rem; font-size: 0.85rem; letter-spacing: 0.04em;
}
.site-header a { color: #95d5b2; }
footer {
  text-align: center; padding: 2rem;
  font-size: 0.8rem; color: #9ca3af;
  border-top: 1px solid #e5e7eb; margin-top: 2rem;
}
.badge {
  display: inline-block; border-radius: 4px;
  padding: 0.1rem 0.5rem; font-size: 0.72rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.04em;
  margin-right: 0.25rem;
}
.badge-id { background: #d8f3dc; color: #1b4332; font-family: monospace; }
.badge-scale { background: #e0f2fe; color: #0c4a6e; }
"""

_HOME_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EcoMech — Ecological Process Mechanisms</title>
  <style>
    {{ shared_css }}
    .hero {
      background: linear-gradient(135deg, #2d6a4f 0%, #1b4332 100%);
      color: #fff; padding: 3rem 2rem 2.5rem;
    }
    .hero h1 { font-size: 2.4rem; font-weight: 800; margin-bottom: 0.5rem; }
    .hero p { max-width: 640px; opacity: 0.9; font-size: 1rem; margin-bottom: 1.5rem; }
    .hero-links { display: flex; gap: 1rem; flex-wrap: wrap; }
    .hero-links a {
      background: rgba(255,255,255,0.15); color: #fff;
      border: 1px solid rgba(255,255,255,0.3);
      padding: 0.4rem 1.1rem; border-radius: 20px; font-size: 0.88rem;
    }
    .hero-links a:hover { background: rgba(255,255,255,0.25); text-decoration: none; }

    .stats {
      display: flex; gap: 2rem; flex-wrap: wrap;
      padding: 1.25rem 2rem; background: #fff;
      border-bottom: 1px solid #e5e7eb;
    }
    .stat { text-align: center; }
    .stat-value { font-size: 1.8rem; font-weight: 800; color: #1b4332; }
    .stat-label { font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }

    .main { max-width: 1080px; margin: 0 auto; padding: 2rem 1.5rem; }
    .category { margin-bottom: 2.5rem; }
    .category-title {
      font-size: 0.8rem; font-weight: 700; color: #6b7280;
      text-transform: uppercase; letter-spacing: 0.08em;
      border-bottom: 2px solid #d8f3dc; padding-bottom: 0.4rem;
      margin-bottom: 1rem;
    }
    .process-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1rem;
    }
    .process-card {
      background: #fff; border: 1px solid #e0ece4; border-radius: 8px;
      padding: 1rem 1.25rem; display: flex; flex-direction: column; gap: 0.4rem;
    }
    .process-card:hover { border-color: #52b788; box-shadow: 0 2px 8px rgba(45,106,79,0.1); }
    .process-card .name { font-weight: 600; color: #1b4332; font-size: 0.95rem; }
    .process-card .desc { font-size: 0.82rem; color: #555; flex: 1; }
    .process-card .meta { display: flex; flex-wrap: wrap; gap: 0.25rem; margin-top: 0.25rem; }
  </style>
</head>
<body>

<header class="site-header">
  EcoMech &mdash; Ecological Process Mechanisms Knowledge Base
</header>

<div class="hero">
  <h1>EcoMech</h1>
  <p>
    A curated knowledge base of ecological process mechanisms — the biological,
    chemical, and physical steps underlying how ecosystems function — backed by
    primary literature evidence.
  </p>
  <div class="hero-links">
    <a href="processes/index.html">Browse all {{ total }} processes &rsaquo;</a>
    <a href="https://github.com/diatomsRcool/ecomech" target="_blank" rel="noopener">GitHub &rsaquo;</a>
  </div>
</div>

<div class="stats">
  <div class="stat">
    <div class="stat-value">{{ total }}</div>
    <div class="stat-label">Processes</div>
  </div>
  <div class="stat">
    <div class="stat-value">{{ total_mechanisms }}</div>
    <div class="stat-label">Mechanisms</div>
  </div>
  <div class="stat">
    <div class="stat-value">{{ total_refs }}</div>
    <div class="stat-label">References</div>
  </div>
  <div class="stat">
    <div class="stat-value">{{ category_count }}</div>
    <div class="stat-label">Categories</div>
  </div>
</div>

<main class="main">
  {% for cat_name, cat_entries in categories %}
  <div class="category">
    <div class="category-title">{{ cat_name }}</div>
    <div class="process-grid">
      {% for entry in cat_entries %}
      <a href="processes/{{ entry.href }}" style="text-decoration:none;">
        <div class="process-card">
          <div class="name">{{ entry.name }}</div>
          <div class="desc">{{ entry.description }}</div>
          <div class="meta">
            <span class="badge badge-id">{{ entry.id }}</span>
            {% if entry.ecological_scale %}
            <span class="badge badge-scale">{{ entry.ecological_scale }}</span>
            {% endif %}
          </div>
        </div>
      </a>
      {% endfor %}
    </div>
  </div>
  {% endfor %}
</main>

<footer>
  EcoMech &mdash; Ecological Process Mechanisms Knowledge Base
</footer>

</body>
</html>
"""

_PROCESS_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>All Processes — EcoMech</title>
  <style>
    {{ shared_css }}
    .hero {
      background: linear-gradient(135deg, #2d6a4f 0%, #1b4332 100%);
      color: #fff; padding: 2rem;
    }
    .hero h1 { font-size: 1.8rem; font-weight: 700; }
    .hero p { opacity: 0.85; font-size: 0.9rem; }
    .main { max-width: 960px; margin: 0 auto; padding: 2rem 1.5rem; }
    .process-list { display: flex; flex-direction: column; gap: 0.75rem; }
    .process-row {
      background: #fff; border: 1px solid #e0ece4; border-radius: 8px;
      padding: 0.9rem 1.25rem; display: flex; align-items: baseline;
      gap: 1rem; flex-wrap: wrap;
    }
    .process-row:hover { border-color: #52b788; }
    .process-row .name { font-weight: 600; color: #1b4332; min-width: 220px; }
    .process-row .desc { font-size: 0.85rem; color: #555; flex: 1; min-width: 200px; }
    .process-row .meta { display: flex; gap: 0.3rem; flex-wrap: wrap; white-space: nowrap; }
  </style>
</head>
<body>

<header class="site-header">
  <a href="../index.html">EcoMech</a> &rsaquo; All Processes
</header>

<div class="hero">
  <h1>All Processes</h1>
  <p>{{ entries | length }} curated ecological process entries</p>
</div>

<main class="main">
  <div class="process-list">
    {% for entry in entries %}
    <a href="{{ entry.href }}" style="text-decoration:none;">
      <div class="process-row">
        <div class="name">{{ entry.name }}</div>
        <div class="desc">{{ entry.description }}</div>
        <div class="meta">
          <span class="badge badge-id">{{ entry.id }}</span>
          {% if entry.ecological_scale %}
          <span class="badge badge-scale">{{ entry.ecological_scale }}</span>
          {% endif %}
        </div>
      </div>
    </a>
    {% endfor %}
  </div>
</main>

<footer>
  EcoMech &mdash; Ecological Process Mechanisms Knowledge Base
</footer>

</body>
</html>
"""


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------

def _count_mechanisms(kb_dir: Path) -> int:
    total = 0
    for f in kb_dir.glob("*.yaml"):
        data = yaml.safe_load(f.read_text())
        if isinstance(data, dict):
            total += len(data.get("mechanisms") or [])
    return total


def _count_refs(kb_dir: Path) -> int:
    refs: set[str] = set()
    for f in kb_dir.glob("*.yaml"):
        text = f.read_text()
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("reference:"):
                refs.add(line.split("reference:", 1)[1].strip())
    return len(refs)


# ---------------------------------------------------------------------------
# Render functions
# ---------------------------------------------------------------------------

def render_home(entries: list[dict], out_dir: Path) -> Path:
    # Group entries by category, preserving category order
    cat_map: dict[str, list[dict]] = {}
    for entry in entries:
        cat_map.setdefault(entry["category"], []).append(entry)

    # Canonical order: defined categories first, then "Other" alphabetically
    ordered = [(cat, cat_map[cat]) for cat in _CATEGORIES if cat in cat_map]
    if "Other" in cat_map:
        ordered.append(("Other", sorted(cat_map["Other"], key=lambda e: e["name"])))

    env = Environment(autoescape=select_autoescape(["html"]))
    tmpl = env.from_string(_HOME_TEMPLATE)
    html = tmpl.render(
        shared_css=_SHARED_CSS,
        total=len(entries),
        total_mechanisms=sum(e["mechanism_count"] for e in entries),
        total_refs="—",  # filled in by caller
        category_count=len(ordered),
        categories=ordered,
    )
    out = out_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    return out


def render_process_index(entries: list[dict], out_dir: Path) -> Path:
    env = Environment(autoescape=select_autoescape(["html"]))
    tmpl = env.from_string(_PROCESS_INDEX_TEMPLATE)
    html = tmpl.render(shared_css=_SHARED_CSS, entries=entries)
    out = out_dir / "processes" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate EcoMech index pages.")
    parser.add_argument("--kb", default="kb/processes", help="KB processes directory")
    parser.add_argument("--out", default="pages", help="Output pages root directory")
    args = parser.parse_args(argv)

    kb_dir = Path(args.kb)
    out_dir = Path(args.out)

    entries = load_processes(kb_dir)
    ref_count = _count_refs(kb_dir)

    # Patch ref count into home render
    env = Environment(autoescape=select_autoescape(["html"]))
    cat_map: dict[str, list[dict]] = {}
    for entry in entries:
        cat_map.setdefault(entry["category"], []).append(entry)
    ordered = [(cat, cat_map[cat]) for cat in _CATEGORIES if cat in cat_map]
    if "Other" in cat_map:
        ordered.append(("Other", sorted(cat_map["Other"], key=lambda e: e["name"])))

    tmpl = env.from_string(_HOME_TEMPLATE)
    html = tmpl.render(
        shared_css=_SHARED_CSS,
        total=len(entries),
        total_mechanisms=sum(e["mechanism_count"] for e in entries),
        total_refs=ref_count,
        category_count=len(ordered),
        categories=ordered,
    )
    home = out_dir / "index.html"
    home.write_text(html, encoding="utf-8")
    print(f"Generated: {home}")

    proc_index = render_process_index(entries, out_dir)
    print(f"Generated: {proc_index}")


if __name__ == "__main__":
    main()
