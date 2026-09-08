"""ENVO/ECOCORE coverage browser for EcoMech.

Reads all curated process entries and generates an HTML page showing:
  - Overall KB statistics
  - Per-entry coverage table (term ID, name, evidence counts, compliance score)
  - Ontology prefix breakdown

Usage:
    uv run python -m ecomech.analysis.coverage
    uv run python -m ecomech.analysis.coverage --output dashboard/coverage.html
    uv run python -m ecomech.analysis.coverage --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

# Re-use compliance scoring from existing module
from ecomech.analysis.compliance import analyze_entry, EntryCompliance, _SECTION_FIELDS

# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def _evidence_count(data: dict[str, Any]) -> int:
    """Count total evidence items across all sections."""
    total = 0
    for section in _SECTION_FIELDS:
        for item in data.get(section) or []:
            total += len(item.get("evidence") or [])
    return total


def _term_prefix(term_id: str) -> str:
    return term_id.split(":")[0] if ":" in term_id else "UNKNOWN"


def collect_entries(processes_dir: Path) -> list[dict[str, Any]]:
    """Return a list of summary dicts for all curated processes."""
    rows = []
    for f in sorted(processes_dir.glob("*.yaml")):
        data = yaml.safe_load(f.read_text())
        if not isinstance(data, dict):
            continue
        ec = analyze_entry(f)
        pt = data.get("process_term") or {}
        rows.append({
            "file": f.name,
            "id": data.get("id") or pt.get("id", ""),
            "term_prefix": _term_prefix(data.get("id") or pt.get("id", "")),
            "term_label": pt.get("label", ""),
            "name": data.get("name", f.stem.replace("_", " ")),
            "ecological_scale": data.get("ecological_scale", ""),
            "mechanisms": len(data.get("mechanisms") or []),
            "indicators": len(data.get("indicators") or []),
            "drivers": len(data.get("drivers") or []),
            "interventions": len(data.get("interventions") or []),
            "evidence_count": _evidence_count(data),
            "score": ec.score,
            "issues": ec.issues,
        })
    return rows


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 14px; line-height: 1.5; color: #1a1a1a; background: #f7f9f7;
}
a { color: #2d6a4f; text-decoration: none; }
a:hover { text-decoration: underline; }
.header {
  background: #1b4332; color: #fff; padding: 1.5rem 2rem;
}
.header h1 { font-size: 1.5rem; font-weight: 700; }
.header p { opacity: 0.8; margin-top: 0.25rem; font-size: 0.9rem; }
.main { max-width: 1100px; margin: 0 auto; padding: 1.5rem; }
.stats-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem; margin-bottom: 2rem;
}
.stat-card {
  background: #fff; border: 1px solid #d8f3dc; border-radius: 8px;
  padding: 1rem; text-align: center;
}
.stat-card .value { font-size: 2rem; font-weight: 700; color: #1b4332; }
.stat-card .label { font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }
.section-title {
  font-size: 1rem; font-weight: 700; color: #1b4332;
  text-transform: uppercase; letter-spacing: 0.06em;
  border-bottom: 2px solid #d8f3dc; padding-bottom: 0.4rem;
  margin-bottom: 1rem; margin-top: 1.5rem;
}
table { width: 100%; border-collapse: collapse; background: #fff;
        border-radius: 8px; overflow: hidden;
        border: 1px solid #e0ece4; }
th { background: #1b4332; color: #fff; padding: 0.5rem 0.75rem;
     text-align: left; font-size: 0.78rem; font-weight: 600;
     text-transform: uppercase; letter-spacing: 0.04em; }
td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #f0f4f1;
     font-size: 0.82rem; vertical-align: middle; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #f0fdf4; }
.badge {
  display: inline-block; border-radius: 4px; padding: 0.1rem 0.4rem;
  font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
}
.badge-envo  { background: #d8f3dc; color: #1b4332; }
.badge-ecocore { background: #dbeafe; color: #1e40af; }
.badge-other { background: #f3f4f6; color: #374151; }
.score-bar {
  display: inline-block; height: 8px; border-radius: 4px;
  background: #d8f3dc; vertical-align: middle;
}
.score-fill { height: 100%; border-radius: 4px; background: #2d6a4f; }
.num { font-variant-numeric: tabular-nums; }
.issue-count { color: #b45309; font-size: 0.75rem; }
footer { text-align: center; padding: 2rem; font-size: 0.78rem; color: #9ca3af;
         border-top: 1px solid #e5e7eb; margin-top: 2rem; }
"""


def _badge(prefix: str) -> str:
    cls = "badge-envo" if prefix == "ENVO" else "badge-ecocore" if prefix == "ECOCORE" else "badge-other"
    return f'<span class="badge {cls}">{prefix}</span>'


def _score_bar(score: float) -> str:
    pct = max(0, min(100, score))
    return (
        f'<div class="score-bar" style="width:60px;">'
        f'<div class="score-fill" style="width:{pct}%;"></div></div>'
        f' <span class="num">{score:.0f}</span>'
    )


def render_html(entries: list[dict[str, Any]], generated_at: str = "") -> str:
    total = len(entries)
    total_mechs = sum(e["mechanisms"] for e in entries)
    total_evidence = sum(e["evidence_count"] for e in entries)
    avg_score = sum(e["score"] for e in entries) / total if total else 0
    prefix_counts: dict[str, int] = {}
    for e in entries:
        prefix_counts[e["term_prefix"]] = prefix_counts.get(e["term_prefix"], 0) + 1

    stats_html = f"""
    <div class="stats-grid">
      <div class="stat-card"><div class="value">{total}</div><div class="label">Curated Processes</div></div>
      <div class="stat-card"><div class="value">{total_mechs}</div><div class="label">Total Mechanisms</div></div>
      <div class="stat-card"><div class="value">{total_evidence}</div><div class="label">Evidence Items</div></div>
      <div class="stat-card"><div class="value">{avg_score:.0f}</div><div class="label">Avg Compliance Score</div></div>
      {"".join(f'<div class="stat-card"><div class="value">{v}</div><div class="label">{k} Entries</div></div>' for k, v in sorted(prefix_counts.items()))}
    </div>"""

    rows_html = ""
    for e in sorted(entries, key=lambda x: x["score"], reverse=True):
        prefix = e["term_prefix"]
        issue_str = f'<span class="issue-count">⚠ {len(e["issues"])} issue(s)</span>' if e["issues"] else ""
        rows_html += f"""
      <tr>
        <td>{_badge(prefix)} <code style="font-size:0.75rem;">{e['id']}</code></td>
        <td><strong>{e['name']}</strong><br><span style="color:#6b7280;font-size:0.75rem;">{e['term_label']}</span></td>
        <td class="num">{e['mechanisms']}</td>
        <td class="num">{e['indicators']}</td>
        <td class="num">{e['drivers']}</td>
        <td class="num">{e['interventions']}</td>
        <td class="num">{e['evidence_count']}</td>
        <td>{_score_bar(e['score'])} {issue_str}</td>
      </tr>"""

    gen_note = f"Generated {generated_at}" if generated_at else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EcoMech — Process Coverage Dashboard</title>
  <style>{_CSS}</style>
</head>
<body>
<header class="header">
  <h1>EcoMech — Process Coverage Dashboard</h1>
  <p>Curated ecological process entries and their curation status. {gen_note}</p>
</header>
<main class="main">
  <h2 class="section-title">Summary Statistics</h2>
  {stats_html}

  <h2 class="section-title">Curated Processes ({total})</h2>
  <table>
    <thead>
      <tr>
        <th>Term ID</th>
        <th>Process Name</th>
        <th>Mechs</th>
        <th>Indic.</th>
        <th>Drivers</th>
        <th>Interv.</th>
        <th>Evidence</th>
        <th>Score / 100</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
</main>
<footer>EcoMech — Ecological Process Mechanisms Knowledge Base</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def render_json(entries: list[dict[str, Any]]) -> str:
    # Remove issues list for cleaner JSON (keep count)
    out = []
    for e in entries:
        row = dict(e)
        row["issue_count"] = len(row.pop("issues"))
        out.append(row)
    return json.dumps({"entries": out, "total": len(out)}, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate EcoMech process coverage report.")
    parser.add_argument("--input", default="kb/processes", help="Directory of process YAML files")
    parser.add_argument("--output", default="dashboard/coverage.html", help="HTML output path")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of HTML")
    args = parser.parse_args(argv)

    entries = collect_entries(Path(args.input))

    if args.json:
        print(render_json(entries))
        return

    from datetime import datetime, timezone
    html = render_html(entries, generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Coverage dashboard written to {out} ({len(entries)} processes)")


if __name__ == "__main__":
    main()
