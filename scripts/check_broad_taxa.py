#!/usr/bin/env python3
"""List all broad-taxon warnings across the KB.

Emits one line per broad-taxon occurrence and a summary count.
Exits 1 if any broad taxa are found (usable as a CI lint step).
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ecomech.analysis.compliance import analyze_kb

kb = analyze_kb()
total = 0
for entry in kb.entries:
    broad = [i for i in entry.issues if i.startswith("Broad taxon")]
    if broad:
        print(f"\n{entry.name} ({entry.entry_id}):")
        for msg in broad:
            print(f"  {msg}")
            total += 1

print(f"\nTotal broad-taxon warnings: {total}")
if total:
    print("See docs/taxa_and_ecoregion_enhancement_plan.md for priority replacements.")
sys.exit(1 if total else 0)
