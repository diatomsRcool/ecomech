"""Process similarity explorer for EcoMech.

Computes pairwise cosine similarity between ecological process entries based
on TF-IDF vectors of their descriptions, mechanism names, and ontology terms.
Outputs an HTML heatmap and a CSV similarity matrix.

Requirements: numpy, (optionally) pandas — both are already installed.

Usage:
    uv run python -m ecomech.analysis.embedding
    uv run python -m ecomech.analysis.embedding --output dashboard/similarity.html
    uv run python -m ecomech.analysis.embedding --csv export/similarity.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alphanumeric, drop stopwords."""
    _STOP = {
        "the", "a", "an", "and", "or", "in", "of", "to", "is", "are",
        "by", "for", "with", "from", "that", "this", "which", "as",
        "be", "on", "at", "its", "it", "via", "through", "into",
    }
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in _STOP and len(t) > 2]


def _extract_text(data: dict[str, Any]) -> str:
    """Build a bag-of-words string from a process entry."""
    parts: list[str] = []
    if data.get("name"):
        parts.append(data["name"])
    if data.get("description"):
        parts.append(data["description"])
    for section in ("mechanisms", "indicators", "drivers", "interventions"):
        for item in data.get(section) or []:
            if item.get("name"):
                parts.append(item["name"])
            if item.get("description"):
                parts.append(item["description"])
            # Ontology term labels
            for key in ("biological_processes", "ecological_processes", "chemical_entities"):
                for sub in item.get(key) or []:
                    lbl = (sub.get("term") or {}).get("label", "")
                    if lbl:
                        parts.append(lbl)
            for td in item.get("taxa_involved") or []:
                lbl = (td.get("taxon") or {}).get("label", "")
                if lbl:
                    parts.append(lbl)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# TF-IDF vectorizer (no sklearn dependency)
# ---------------------------------------------------------------------------

def build_tfidf(documents: list[str]) -> np.ndarray:
    """Return an (n_docs, n_terms) TF-IDF matrix."""
    tokenized = [_tokenize(doc) for doc in documents]
    n = len(tokenized)

    # Build vocabulary
    vocab: dict[str, int] = {}
    for tokens in tokenized:
        for t in set(tokens):
            if t not in vocab:
                vocab[t] = len(vocab)

    v = len(vocab)
    tf = np.zeros((n, v), dtype=np.float32)

    for i, tokens in enumerate(tokenized):
        if not tokens:
            continue
        for t in tokens:
            tf[i, vocab[t]] += 1.0
        tf[i] /= len(tokens)

    # IDF
    df = np.sum(tf > 0, axis=0).astype(np.float32)
    idf = np.log((n + 1) / (df + 1)) + 1.0

    return tf * idf


def cosine_similarity(matrix: np.ndarray) -> np.ndarray:
    """Return pairwise cosine similarity matrix (n × n)."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-10, norms)
    normed = matrix / norms
    return normed @ normed.T


# ---------------------------------------------------------------------------
# HTML heatmap
# ---------------------------------------------------------------------------

_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
       font-size: 12px; background: #f7f9f7; color: #1a1a1a; }
.header { background: #1b4332; color: #fff; padding: 1.5rem 2rem; }
.header h1 { font-size: 1.4rem; font-weight: 700; }
.header p { opacity: 0.8; margin-top: 0.25rem; font-size: 0.85rem; }
.main { padding: 1.5rem; overflow-x: auto; }
table { border-collapse: collapse; }
th, td { padding: 3px 4px; white-space: nowrap; font-size: 10px; }
th { background: #1b4332; color: #fff; font-weight: 600; }
th.row-label { text-align: right; background: #fff; color: #374151; font-weight: 600;
               padding-right: 0.5rem; position: sticky; left: 0; z-index: 1; }
.top-clusters { margin-bottom: 1.5rem; }
.cluster-row { display: flex; gap: 0.5rem; align-items: baseline; margin-bottom: 0.4rem;
               font-size: 0.82rem; }
.cluster-num { color: #6b7280; min-width: 1.5rem; }
footer { text-align: center; padding: 1.5rem; font-size: 0.78rem; color: #9ca3af;
         border-top: 1px solid #e5e7eb; margin-top: 1rem; }
"""


def _sim_color(v: float) -> str:
    """Map similarity 0–1 to a green gradient CSS color."""
    # 0 → white, 1 → dark green
    r = int(255 - v * (255 - 27))
    g = int(255 - v * (255 - 67))
    b = int(255 - v * (255 - 50))
    return f"rgb({r},{g},{b})"


def render_html(names: list[str], sim: np.ndarray) -> str:
    n = len(names)
    short = [nm[:22] + "…" if len(nm) > 24 else nm for nm in names]

    # Header row
    header = "<tr><th></th>" + "".join(
        f'<th style="writing-mode:vertical-lr;transform:rotate(180deg);max-height:120px;">{s}</th>'
        for s in short
    ) + "</tr>"

    # Data rows
    rows_html = ""
    for i in range(n):
        cells = "".join(
            f'<td style="background:{_sim_color(sim[i,j])};color:{"#fff" if sim[i,j]>0.5 else "#374151"};" '
            f'title="{names[i]} × {names[j]}: {sim[i,j]:.3f}">{sim[i,j]:.2f}</td>'
            for j in range(n)
        )
        rows_html += f'<tr><th class="row-label">{short[i]}</th>{cells}</tr>'

    # Top-5 most similar pairs (off-diagonal)
    pairs = [
        (float(sim[i, j]), names[i], names[j])
        for i in range(n) for j in range(i + 1, n)
    ]
    pairs.sort(key=lambda x: x[0], reverse=True)
    top_html = '<div class="section-title" style="margin-bottom:0.75rem;font-size:0.85rem;font-weight:700;color:#1b4332;text-transform:uppercase;letter-spacing:.05em;">Most Similar Process Pairs</div>'
    for rank, (score, a, b) in enumerate(pairs[:10], 1):
        top_html += (
            f'<div class="cluster-row"><span class="cluster-num">{rank}.</span>'
            f'<strong>{a}</strong> &harr; <strong>{b}</strong>'
            f'<span style="color:#6b7280;margin-left:auto;">{score:.3f}</span></div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EcoMech — Process Similarity Explorer</title>
  <style>{_CSS}</style>
</head>
<body>
<header class="header">
  <h1>EcoMech — Process Similarity Explorer</h1>
  <p>TF-IDF cosine similarity across {n} curated processes (descriptions + mechanism terms).</p>
</header>
<main class="main">
  <div class="top-clusters" style="background:#fff;border:1px solid #e0ece4;border-radius:8px;padding:1rem;margin-bottom:1.5rem;max-width:600px;">
    {top_html}
  </div>
  <p style="margin-bottom:0.75rem;color:#6b7280;font-size:0.82rem;">
    Hover cells for exact scores. Darker green = higher similarity.
  </p>
  <table>
    <thead>{header}</thead>
    <tbody>{rows_html}</tbody>
  </table>
</main>
<footer>EcoMech — TF-IDF similarity on descriptions, mechanism names, and ontology term labels</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate EcoMech process similarity explorer.")
    parser.add_argument("--input", default="kb/processes", help="Directory of process YAML files")
    parser.add_argument("--output", default="dashboard/similarity.html", help="HTML output path")
    parser.add_argument("--csv", default="", help="Also write CSV similarity matrix to this path")
    args = parser.parse_args(argv)

    input_dir = Path(args.input)
    files = sorted(input_dir.glob("*.yaml"))
    if not files:
        print(f"No YAML files in {input_dir}", file=sys.stderr)
        sys.exit(1)

    entries = []
    for f in files:
        data = yaml.safe_load(f.read_text())
        if isinstance(data, dict):
            entries.append((data.get("name") or f.stem.replace("_", " "), data))

    names = [e[0] for e in entries]
    docs = [_extract_text(e[1]) for e in entries]

    matrix = build_tfidf(docs)
    sim = cosine_similarity(matrix)

    # HTML output
    html = render_html(names, sim)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Similarity explorer written to {out} ({len(names)} processes)")

    # Optional CSV
    if args.csv:
        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow([""] + names)
            for i, name in enumerate(names):
                writer.writerow([name] + [f"{sim[i,j]:.4f}" for j in range(len(names))])
        print(f"Similarity CSV written to {csv_path}")


if __name__ == "__main__":
    main()
