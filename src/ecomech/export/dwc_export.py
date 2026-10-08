"""Darwin Core MeasurementOrFact export for EcoMech.

Exports ecological indicators from all curated process entries as a
Darwin Core MeasurementOrFact CSV, suitable for import into GBIF,
iDigBio, or Symbiota platforms.

DwC MeasurementOrFact terms used:
  measurementID          — stable CURIE for the indicator row
  parentEventID          — process CURIE (the ecological process being characterised)
  measurementType        — indicator name
  measurementUnit        — unit extracted from indicator.measurement field
  measurementMethod      — evidence_source of the first supporting reference
  measurementRemarks     — indicator description
  bibliographicCitation  — pipe-separated PMIDs / DOIs from indicator evidence
  modified               — process creation_date (ISO date)

Reference: https://dwc.tdwg.org/terms/#measurementorfact

Usage:
    uv run python -m ecomech.export.dwc_export \\
        --input kb/processes --output export/ecomech_dwc_mof.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any

import yaml

_DWC_COLUMNS = [
    "measurementID",
    "parentEventID",
    "measurementType",
    "measurementUnit",
    "measurementMethod",
    "measurementRemarks",
    "bibliographicCitation",
    "modified",
]


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def _extract_unit(measurement: str) -> str:
    """Extract a unit string from a free-text measurement description.

    Looks for a parenthesised token at the end of the string first
    (e.g. "(g C kg-1 dry soil)"), then falls back to the last token
    if it looks like a unit symbol.
    """
    m = re.search(r"\(([^)]+)\)\s*$", measurement or "")
    if m:
        return m.group(1).strip()
    parts = (measurement or "").rsplit(None, 1)
    if len(parts) == 2 and re.match(r"^[a-zA-Z%°/·\-\d]+$", parts[1]):
        return parts[1]
    return ""


def _references(evidence_list: list[dict]) -> str:
    seen: list[str] = []
    for ev in evidence_list or []:
        ref = ev.get("reference", "")
        if ref and ref not in seen:
            seen.append(ref)
    return "|".join(seen)


def _method(evidence_list: list[dict]) -> str:
    for ev in evidence_list or []:
        src = ev.get("evidence_source", "")
        if src:
            return src
    return ""


def extract_mof(data: dict[str, Any], file_stem: str) -> list[dict[str, str]]:
    """Return DwC MeasurementOrFact rows for all indicators in a process entry."""
    pid = (data.get("process_term") or {}).get("id") or data.get("id") or f"ecomech:{file_stem}"
    created = (data.get("creation_date") or "")[:10]  # ISO date only

    rows: list[dict[str, str]] = []
    for i, ind in enumerate(data.get("indicators") or []):
        iname = ind.get("name") or f"indicator_{i + 1}"
        evidence = ind.get("evidence") or []
        rows.append({
            "measurementID": f"ecomech:{file_stem}:ind:{_slug(iname)}",
            "parentEventID": pid,
            "measurementType": iname,
            "measurementUnit": _extract_unit(ind.get("measurement") or ""),
            "measurementMethod": _method(evidence),
            "measurementRemarks": (ind.get("description") or "").replace("\n", " ").strip()[:500],
            "bibliographicCitation": _references(evidence),
            "modified": created,
        })
    return rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Export EcoMech indicators as Darwin Core MeasurementOrFact CSV."
    )
    parser.add_argument("--input", default="kb/processes", help="Directory of process YAML files")
    parser.add_argument(
        "--output", default="export/ecomech_dwc_mof.csv", help="Output CSV path"
    )
    args = parser.parse_args(argv)

    input_dir = Path(args.input)
    output_path = Path(args.output)

    files = sorted(input_dir.glob("*.yaml"))
    if not files:
        print(f"No YAML files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    rows: list[dict[str, str]] = []
    for f in files:
        data = yaml.safe_load(f.read_text())
        if isinstance(data, dict):
            rows.extend(extract_mof(data, f.stem))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_DWC_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} MeasurementOrFact rows → {output_path}")


if __name__ == "__main__":
    main()
