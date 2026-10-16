#!/usr/bin/env python3
"""Backfill traitmech_xref into TaxonDescriptor entries in KB process YAML files.

Reads mappings/taxon_role_to_traitmech.tsv to determine which TraitMech trait
corresponds to each TaxonRoleEnum value, then scans kb/processes/*.yaml for
taxa_involved entries that have a role but no traitmech_xref.

Roles that map to exactly one TraitMech ID are "unambiguous" and can be
backfilled automatically. Roles with multiple possible IDs (e.g. NITROGEN_FIXER
→ nitrogen_fixing_symbiosis OR nitrogen_fixation) require human review.

Usage:
    uv run python scripts/backfill_traitmech_xrefs.py --check
    uv run python scripts/backfill_traitmech_xrefs.py --apply [--dry-run]
    uv run python scripts/backfill_traitmech_xrefs.py --apply kb/processes/Foo.yaml
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ROLE_MAP_TSV = REPO_ROOT / "mappings" / "taxon_role_to_traitmech.tsv"
PROCESSES_DIR = REPO_ROOT / "kb" / "processes"

_ROLE_LINE = re.compile(r"^(\s+)role:\s+(\S+)\s*$")
_XREF_LINE = re.compile(r"^\s+traitmech_xref:\s")
_TAXON_ID_LINE = re.compile(r"^\s+id:\s+(NCBITaxon:\S+)\s*$")

# Taxa that must NOT receive automatic traitmech_xref for a given role because
# no appropriate TraitMech trait exists. Key: role, value: set of NCBITaxon CURIEs.
XREF_SKIP: dict[str, set[str]] = {
    # Methylobacter is an aerobic methanotroph — not a saprotroph.
    # Aerobic methane oxidation has no TraitMech trait as of Oct 2026.
    "DECOMPOSER": {"NCBITaxon:429"},
}


def load_role_map(tsv_path: Path) -> dict[str, list[str]]:
    """Return {role: [traitmech_id, ...]} excluding TODO entries."""
    role_map: dict[str, list[str]] = {}
    with open(tsv_path, newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            tid = row["traitmech_id"].strip()
            if tid.startswith("TODO"):
                continue
            role = row["taxon_role"].strip()
            role_map.setdefault(role, []).append(tid)
    return role_map


def _next_content_line(lines: list[str], start: int) -> tuple[int, str]:
    """Return (index, line) of the first non-blank line at or after `start`."""
    for i in range(start, len(lines)):
        if lines[i].strip():
            return i, lines[i]
    return len(lines), ""


def _taxon_id_near(lines: list[str], role_line_idx: int) -> str | None:
    """Scan up to 5 lines above role_line_idx for an NCBITaxon id: line."""
    for j in range(max(0, role_line_idx - 5), role_line_idx):
        m = _TAXON_ID_LINE.match(lines[j])
        if m:
            return m.group(1)
    return None


def check_file(path: Path, role_map: dict[str, list[str]]) -> list[dict]:
    """Return list of missing-xref records for a file."""
    issues = []
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines):
        m = _ROLE_LINE.match(line)
        if not m:
            continue
        role = m.group(2)
        if role not in role_map:
            continue
        # Check exclusion list
        taxon_id = _taxon_id_near(lines, i)
        if taxon_id and taxon_id in XREF_SKIP.get(role, set()):
            continue
        # Look at the next content line
        ni, next_line = _next_content_line(lines, i + 1)
        if _XREF_LINE.match(next_line):
            continue  # already has xref
        traitmech_ids = role_map[role]
        issues.append({
            "file": path.name,
            "line": i + 1,
            "role": role,
            "traitmech_ids": traitmech_ids,
            "ambiguous": len(traitmech_ids) > 1,
        })
    return issues


def apply_file(
    path: Path,
    role_map: dict[str, list[str]],
    dry_run: bool = False,
) -> tuple[int, int]:
    """Insert traitmech_xref for unambiguous roles. Returns (applied, skipped)."""
    lines = path.read_text().splitlines(keepends=True)
    result: list[str] = []
    applied = 0
    skipped = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _ROLE_LINE.match(line)
        if m:
            indent = m.group(1)
            role = m.group(2)
            ids = role_map.get(role, [])
            # Check exclusion list by scanning recent result lines for taxon id
            recent = [ln.rstrip("\n") for ln in result[-5:]]
            taxon_id = _taxon_id_near(recent, len(recent))
            if taxon_id and taxon_id in XREF_SKIP.get(role, set()):
                result.append(line)
                i += 1
                continue
            # Peek at next content line
            ni, next_line = _next_content_line(lines, i + 1)
            already_has = _XREF_LINE.match(next_line)
            if ids and not already_has:
                if len(ids) == 1:
                    result.append(line)
                    result.append(f"{indent}traitmech_xref: {ids[0]}\n")
                    applied += 1
                    i += 1
                    continue
                else:
                    skipped += 1  # ambiguous — leave for human
        result.append(line)
        i += 1
    if applied and not dry_run:
        path.write_text("".join(result))
    return applied, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        action="store_true",
        help="Report taxa entries missing traitmech_xref (read-only)",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Insert traitmech_xref for unambiguous role mappings",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --apply: show what would change without writing files",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Specific YAML files to process (default: all kb/processes/*.yaml)",
    )
    args = parser.parse_args(argv)

    if not ROLE_MAP_TSV.exists():
        print(f"ERROR: {ROLE_MAP_TSV} not found", file=sys.stderr)
        return 1

    role_map = load_role_map(ROLE_MAP_TSV)
    unambiguous_roles = {r for r, ids in role_map.items() if len(ids) == 1}
    ambiguous_roles = {r for r, ids in role_map.items() if len(ids) > 1}

    if args.files:
        paths = [Path(f) for f in args.files]
    else:
        paths = sorted(PROCESSES_DIR.glob("*.yaml"))

    if args.check:
        total_missing = 0
        total_ambiguous = 0
        for path in paths:
            issues = check_file(path, role_map)
            if not issues:
                continue
            for iss in issues:
                if iss["ambiguous"]:
                    status = "AMBIGUOUS (manual)"
                    total_ambiguous += 1
                else:
                    status = "MISSING (auto-fixable)"
                    total_missing += 1
                ids_str = ", ".join(iss["traitmech_ids"])
                print(
                    f"  {iss['file']}:{iss['line']}  role={iss['role']}"
                    f"  [{status}]  candidates={ids_str}"
                )
        print()
        print(f"Auto-fixable:  {total_missing}  (run --apply to insert)")
        print(f"Manual review: {total_ambiguous}  (ambiguous role mapping)")
        return 0 if total_missing == 0 else 1

    # --apply mode
    total_applied = 0
    total_skipped = 0
    for path in paths:
        applied, skipped = apply_file(path, role_map, dry_run=args.dry_run)
        if applied:
            tag = "(dry-run)" if args.dry_run else ""
            print(f"  {path.name}: inserted {applied} xref(s) {tag}")
        total_applied += applied
        total_skipped += skipped

    print()
    if args.dry_run:
        print(f"Dry run — would insert {total_applied} xref(s)")
    else:
        print(f"Inserted {total_applied} xref(s)")
    if total_skipped:
        print(
            f"Skipped {total_skipped} ambiguous role(s) "
            f"({', '.join(sorted(ambiguous_roles))}) — set traitmech_xref manually"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
