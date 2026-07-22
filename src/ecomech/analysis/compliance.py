"""Field-coverage compliance analysis for EcoMech KB entries.

Scores each EcologicalProcess YAML on how completely it is curated and
aggregates coverage statistics across the whole KB.

Usage (CLI):
    uv run python -m ecomech.analysis.compliance                      # whole KB
    uv run python -m ecomech.analysis.compliance kb/processes/X.yaml  # single file
    uv run python -m ecomech.analysis.compliance --json               # JSON output
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Scoring weights
# ---------------------------------------------------------------------------

# Points awarded for each populated section / property.
# Total possible = sum of all values = 100.
_WEIGHTS: dict[str, int] = {
    # Required identity fields (30 pts)
    "id": 5,
    "name": 5,
    "process_term": 5,
    "description": 5,
    "ecological_scale": 5,
    "creation_date": 5,
    # Core content sections (50 pts)
    "mechanisms": 15,
    "indicators": 10,
    "drivers": 10,
    "interventions": 10,
    "habitat_context": 5,
    # Evidence completeness across all sections (20 pts)
    "evidence_coverage": 20,
}

assert sum(_WEIGHTS.values()) == 100, "Weights must sum to 100"

_REQUIRED_FIELDS = ["id", "name", "process_term", "description", "ecological_scale", "creation_date"]
_SECTION_FIELDS = ["mechanisms", "indicators", "drivers", "interventions", "habitat_context"]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SectionCoverage:
    """Coverage stats for a single section (mechanisms, indicators, etc.)."""
    count: int                    # number of items in this section
    with_evidence: int            # items that have at least one evidence entry
    evidence_items: int           # total evidence entries across all items

    @property
    def evidence_pct(self) -> float:
        """Fraction of items that have evidence (0.0–1.0)."""
        return self.with_evidence / self.count if self.count else 0.0


@dataclass
class EntryCompliance:
    """Compliance report for a single EcologicalProcess KB entry."""
    file: str
    entry_id: str
    name: str

    # Required field presence (True/False per field)
    required_fields: dict[str, bool] = field(default_factory=dict)

    # Per-section coverage
    sections: dict[str, SectionCoverage] = field(default_factory=dict)

    # Mechanism-level sub-field coverage
    mechanisms_with_taxa: int = 0
    mechanisms_with_biological_processes: int = 0
    mechanisms_with_causal_edges: int = 0
    mechanisms_with_abiotic_conditions: int = 0
    total_mechanisms: int = 0

    # Overall score 0–100
    score: float = 0.0

    # Human-readable issues
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Convert SectionCoverage to plain dicts with evidence_pct included
        for k, v in d["sections"].items():
            v["evidence_pct"] = round(self.sections[k].evidence_pct * 100, 1)
        return d


@dataclass
class KBCompliance:
    """Aggregate compliance report for the whole KB."""
    total_entries: int = 0
    mean_score: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0
    entries: list[EntryCompliance] = field(default_factory=list)

    # KB-wide section coverage counts
    section_totals: dict[str, int] = field(default_factory=dict)
    section_with_evidence: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_entries": self.total_entries,
            "mean_score": round(self.mean_score, 1),
            "min_score": self.min_score,
            "max_score": self.max_score,
            "section_totals": self.section_totals,
            "section_evidence_pct": {
                k: round(self.section_with_evidence.get(k, 0) / v * 100, 1) if v else 0.0
                for k, v in self.section_totals.items()
            },
            "entries": [e.to_dict() for e in self.entries],
        }


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def _count_with_evidence(items: list[dict]) -> tuple[int, int]:
    """Return (items_with_evidence, total_evidence_items) for a list of KB items."""
    with_ev = 0
    total_ev = 0
    for item in items:
        ev = item.get("evidence") or []
        if ev:
            with_ev += 1
            total_ev += len(ev)
    return with_ev, total_ev


def _mechanism_sub_coverage(mechanisms: list[dict]) -> tuple[int, int, int, int]:
    """Return counts of mechanisms that have taxa, bio_processes, causal_edges, abiotic_conditions."""
    taxa = bio = causal = abiotic = 0
    for m in mechanisms:
        if m.get("taxa_involved"):
            taxa += 1
        if m.get("biological_processes"):
            bio += 1
        if m.get("causal_edges"):
            causal += 1
        if m.get("abiotic_conditions"):
            abiotic += 1
    return taxa, bio, causal, abiotic


def _score_entry(data: dict) -> tuple[float, list[str]]:
    """Compute compliance score and issues list for a parsed entry dict."""
    pts = 0.0
    issues: list[str] = []

    # Required fields
    for f_name in _REQUIRED_FIELDS:
        present = bool(data.get(f_name))
        if present:
            pts += _WEIGHTS[f_name]
        else:
            issues.append(f"Missing required field: {f_name}")

    # Section presence and evidence coverage
    total_items = 0
    total_with_ev = 0

    for section in _SECTION_FIELDS:
        items = data.get(section) or []
        if items:
            pts += _WEIGHTS[section]
        else:
            issues.append(f"Empty section: {section}")
        with_ev, _ = _count_with_evidence(items)
        total_items += len(items)
        total_with_ev += with_ev

    # Evidence coverage score (proportional)
    if total_items > 0:
        ev_frac = total_with_ev / total_items
        pts += _WEIGHTS["evidence_coverage"] * ev_frac
        if ev_frac < 1.0:
            missing = total_items - total_with_ev
            issues.append(f"{missing} section item(s) lack evidence")
    else:
        issues.append("No section items found — evidence score is 0")

    return round(pts, 1), issues


def analyze_entry(path: Path) -> EntryCompliance:
    """Load a KB YAML file and return its EntryCompliance report."""
    with open(path) as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        return EntryCompliance(
            file=str(path),
            entry_id="",
            name="",
            issues=["File did not parse as a YAML mapping"],
            score=0.0,
        )

    score, issues = _score_entry(data)

    # Required field presence map
    req_map = {f: bool(data.get(f)) for f in _REQUIRED_FIELDS}

    # Section coverage
    sections: dict[str, SectionCoverage] = {}
    for section in _SECTION_FIELDS:
        items = data.get(section) or []
        with_ev, total_ev = _count_with_evidence(items)
        sections[section] = SectionCoverage(
            count=len(items),
            with_evidence=with_ev,
            evidence_items=total_ev,
        )

    # Mechanism sub-field coverage
    mechanisms = data.get("mechanisms") or []
    taxa_c, bio_c, causal_c, abiotic_c = _mechanism_sub_coverage(mechanisms)

    return EntryCompliance(
        file=str(path),
        entry_id=data.get("id", ""),
        name=data.get("name", ""),
        required_fields=req_map,
        sections=sections,
        mechanisms_with_taxa=taxa_c,
        mechanisms_with_biological_processes=bio_c,
        mechanisms_with_causal_edges=causal_c,
        mechanisms_with_abiotic_conditions=abiotic_c,
        total_mechanisms=len(mechanisms),
        score=score,
        issues=issues,
    )


def analyze_kb(processes_dir: Path = Path("kb/processes")) -> KBCompliance:
    """Analyze all YAML files in processes_dir and return KBCompliance."""
    files = sorted(processes_dir.glob("*.yaml"))
    if not files:
        return KBCompliance()

    entries = [analyze_entry(f) for f in files]
    scores = [e.score for e in entries]

    # Aggregate section totals
    section_totals: dict[str, int] = {s: 0 for s in _SECTION_FIELDS}
    section_with_ev: dict[str, int] = {s: 0 for s in _SECTION_FIELDS}
    for e in entries:
        for s in _SECTION_FIELDS:
            cov = e.sections.get(s)
            if cov:
                section_totals[s] += cov.count
                section_with_ev[s] += cov.with_evidence

    return KBCompliance(
        total_entries=len(entries),
        mean_score=sum(scores) / len(scores),
        min_score=min(scores),
        max_score=max(scores),
        entries=entries,
        section_totals=section_totals,
        section_with_evidence=section_with_ev,
    )


# ---------------------------------------------------------------------------
# Text report rendering
# ---------------------------------------------------------------------------

def _bar(frac: float, width: int = 20) -> str:
    filled = round(frac * width)
    return "█" * filled + "░" * (width - filled)


def _score_label(score: float) -> str:
    if score >= 90:
        return "EXCELLENT"
    if score >= 75:
        return "GOOD"
    if score >= 50:
        return "PARTIAL"
    return "INCOMPLETE"


def format_entry_report(ec: EntryCompliance) -> str:
    lines: list[str] = []
    lines.append(f"{'─' * 60}")
    lines.append(f"  {ec.name}  ({ec.entry_id})")
    lines.append(f"  File: {ec.file}")
    lines.append(f"  Score: {ec.score:.0f}/100  [{_score_label(ec.score)}]  {_bar(ec.score / 100)}")
    lines.append("")

    # Required fields
    req_ok = [k for k, v in ec.required_fields.items() if v]
    req_miss = [k for k, v in ec.required_fields.items() if not v]
    lines.append(f"  Required fields ({len(req_ok)}/{len(ec.required_fields)} present):")
    for k in _REQUIRED_FIELDS:
        mark = "✓" if ec.required_fields.get(k) else "✗"
        lines.append(f"    {mark} {k}")

    lines.append("")
    lines.append("  Sections:")
    for section in _SECTION_FIELDS:
        cov = ec.sections.get(section, SectionCoverage(0, 0, 0))
        ev_pct = f"{cov.evidence_pct * 100:.0f}%" if cov.count else "—"
        mark = "✓" if cov.count else "✗"
        lines.append(
            f"    {mark} {section:<20}  {cov.count:>2} item(s)  "
            f"evidence: {cov.with_evidence}/{cov.count} ({ev_pct})"
        )

    if ec.total_mechanisms:
        lines.append("")
        lines.append(f"  Mechanism sub-fields ({ec.total_mechanisms} mechanisms):")
        for label, count in [
            ("biological_processes", ec.mechanisms_with_biological_processes),
            ("taxa_involved", ec.mechanisms_with_taxa),
            ("causal_edges", ec.mechanisms_with_causal_edges),
            ("abiotic_conditions", ec.mechanisms_with_abiotic_conditions),
        ]:
            bar = _bar(count / ec.total_mechanisms)
            lines.append(f"    {label:<25}  {count}/{ec.total_mechanisms}  {bar}")

    if ec.issues:
        lines.append("")
        lines.append("  Issues:")
        for issue in ec.issues:
            lines.append(f"    ⚠  {issue}")

    return "\n".join(lines)


def format_kb_report(kb: KBCompliance) -> str:
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("  EcoMech KB Compliance Summary")
    lines.append("=" * 60)
    lines.append(f"  Entries:    {kb.total_entries}")
    lines.append(f"  Mean score: {kb.mean_score:.1f}/100")
    lines.append(f"  Range:      {kb.min_score:.0f} – {kb.max_score:.0f}")
    lines.append("")
    lines.append("  Section coverage (items with evidence / total items):")
    for section in _SECTION_FIELDS:
        total = kb.section_totals.get(section, 0)
        with_ev = kb.section_with_evidence.get(section, 0)
        if total:
            pct = with_ev / total
            lines.append(
                f"    {section:<20}  {with_ev:>3}/{total:<3}  "
                f"{_bar(pct)}  {pct * 100:.0f}%"
            )
        else:
            lines.append(f"    {section:<20}  (no items)")
    lines.append("")

    for entry in sorted(kb.entries, key=lambda e: e.score, reverse=True):
        lines.append(format_entry_report(entry))

    lines.append("=" * 60)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = sys.argv[1:]
    as_json = "--json" in args
    targets = [a for a in args if not a.startswith("--")]

    if targets:
        # Single-file mode
        for target in targets:
            ec = analyze_entry(Path(target))
            if as_json:
                print(json.dumps(ec.to_dict(), indent=2))
            else:
                print(format_entry_report(ec))
    else:
        # Whole-KB mode
        kb = analyze_kb()
        if as_json:
            print(json.dumps(kb.to_dict(), indent=2))
        else:
            print(format_kb_report(kb))


if __name__ == "__main__":
    main()
