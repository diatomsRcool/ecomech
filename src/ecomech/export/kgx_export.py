"""KGX (Knowledge Graph Exchange) export for EcoMech.

Exports all curated ecological process entries as KGX-compatible TSV files
suitable for graph databases, Cytoscape, or the Monarch Knowledge Graph.

Output files derived from --output path:
  <prefix>_nodes.tsv  — node table
  <prefix>_edges.tsv  — edge table

Usage:
    uv run python -m ecomech.export.kgx_export \\
        --input kb/processes --output export/ecomech_kgx.tsv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ECOMECH_SOURCE = "infores:ecomech"

# Biolink category by CURIE prefix
_CATEGORY: dict[str, str] = {
    "ENVO": "biolink:BiologicalProcess",
    "ECOCORE": "biolink:BiologicalProcess",
    "GO": "biolink:BiologicalProcess",
    "NCBITaxon": "biolink:OrganismTaxon",
    "CHEBI": "biolink:ChemicalEntity",
    "PATO": "biolink:PhenotypicQuality",
    "ECTO": "biolink:EnvironmentalExposure",
    "ecomech": "biolink:Pathway",
}

# KGX predicate / RO relation pairs: (biolink_pred, RO_curie)
_REL_HAS_PART = ("biolink:has_part", "BFO:0000051")
_REL_OCCURS_IN = ("biolink:occurs_in", "RO:0001025")
_REL_ENABLED_BY = ("biolink:enabled_by", "RO:0002333")
_REL_PARTICIPANT = ("biolink:has_participant", "RO:0000057")
_REL_HAS_INPUT = ("biolink:has_input", "RO:0002233")
_REL_UPSTREAM = ("biolink:causally_upstream_of", "RO:0002411")
_REL_PHENOTYPE = ("biolink:has_phenotype", "RO:0002200")
_REL_RELATED = ("biolink:related_to", "")

_NODE_COLUMNS = ["id", "category", "name", "description", "provided_by"]
_EDGE_COLUMNS = ["id", "subject", "predicate", "object", "relation", "knowledge_source", "publications"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _prefix(curie: str) -> str:
    return curie.split(":")[0] if ":" in curie else ""


def _category(curie: str) -> str:
    return _CATEGORY.get(_prefix(curie), "biolink:NamedThing")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def _pubs(items: list[dict]) -> str:
    """Collect pipe-separated publication CURIEs from a list of evidence dicts."""
    seen: list[str] = []
    for item in items:
        for ev in item.get("evidence") or []:
            ref = ev.get("reference", "")
            if ref and ref not in seen:
                seen.append(ref)
    return "|".join(seen)


# ---------------------------------------------------------------------------
# Graph extraction
# ---------------------------------------------------------------------------

class GraphBuilder:
    """Accumulates nodes and edges across all process entries."""

    def __init__(self) -> None:
        self._nodes: dict[str, dict[str, str]] = {}  # id → row
        self._edges: list[dict[str, str]] = []
        self._edge_ctr = 0

    # ── Node methods ──

    def add_node(self, node_id: str, name: str, description: str = "", category: str = "") -> None:
        if node_id not in self._nodes:
            self._nodes[node_id] = {
                "id": node_id,
                "category": category or _category(node_id),
                "name": name,
                "description": description[:500].replace("\n", " ") if description else "",
                "provided_by": _ECOMECH_SOURCE,
            }

    # ── Edge methods ──

    def add_edge(
        self,
        subject: str,
        pred_rel: tuple[str, str],
        obj: str,
        publications: str = "",
    ) -> None:
        self._edge_ctr += 1
        self._edges.append({
            "id": f"ecomech:e{self._edge_ctr:06d}",
            "subject": subject,
            "predicate": pred_rel[0],
            "object": obj,
            "relation": pred_rel[1],
            "knowledge_source": _ECOMECH_SOURCE,
            "publications": publications,
        })

    # ── Per-file extraction ──

    def ingest(self, data: dict[str, Any], file_stem: str) -> None:
        pt = data.get("process_term") or {}
        pid = pt.get("id") or data.get("id") or f"ecomech:{file_stem}"
        plabel = pt.get("label") or data.get("name", file_stem)
        self.add_node(pid, plabel, data.get("description", ""))

        # Habitat
        for hc in data.get("habitat_context") or []:
            ht = hc.get("habitat_term") or {}
            if ht.get("id"):
                self.add_node(ht["id"], ht.get("label", ""), category="biolink:EnvironmentalContext")
                self.add_edge(pid, _REL_OCCURS_IN, ht["id"])

        # Mechanisms
        for i, mech in enumerate(data.get("mechanisms") or []):
            mname = mech.get("name") or f"mechanism_{i+1}"
            mid = f"ecomech:{file_stem}:{_slug(mname)}"
            self.add_node(mid, mname, mech.get("description", ""), "biolink:Pathway")
            self.add_edge(pid, _REL_HAS_PART, mid)

            for bp in mech.get("biological_processes") or []:
                t = bp.get("term") or {}
                if t.get("id"):
                    self.add_node(t["id"], t.get("label", ""), category="biolink:BiologicalProcess")
                    self.add_edge(mid, _REL_ENABLED_BY, t["id"], _pubs([bp]))

            for ep in mech.get("ecological_processes") or []:
                t = ep.get("term") or {}
                if t.get("id"):
                    self.add_node(t["id"], t.get("label", ""))
                    self.add_edge(mid, _REL_HAS_PART, t["id"], _pubs([ep]))

            for td in mech.get("taxa_involved") or []:
                taxon = td.get("taxon") or {}
                if taxon.get("id"):
                    self.add_node(taxon["id"], taxon.get("label", ""), category="biolink:OrganismTaxon")
                    self.add_edge(mid, _REL_PARTICIPANT, taxon["id"])

            for ce in mech.get("chemical_entities") or []:
                t = ce.get("term") or {}
                if t.get("id"):
                    self.add_node(t["id"], t.get("label", ""), category="biolink:ChemicalEntity")
                    self.add_edge(mid, _REL_HAS_INPUT, t["id"], _pubs([ce]))

        # Indicators
        for ind in data.get("indicators") or []:
            iname = ind.get("name") or "indicator"
            it = ind.get("indicator_term") or {}
            iid = it.get("id") or f"ecomech:{file_stem}:ind:{_slug(iname)}"
            icat = "biolink:PhenotypicQuality"
            self.add_node(iid, it.get("label") or iname, category=icat)
            self.add_edge(pid, _REL_PHENOTYPE, iid, _pubs([ind]))

        # Drivers
        for drv in data.get("drivers") or []:
            dname = drv.get("name") or "driver"
            dt = drv.get("driver_term") or {}
            chem = drv.get("chemical_agent") or {}
            did = dt.get("id") or chem.get("id") or f"ecomech:{file_stem}:drv:{_slug(dname)}"
            dlabel = dt.get("label") or chem.get("label") or dname
            dcat = (
                "biolink:EnvironmentalExposure" if dt.get("id") else
                "biolink:ChemicalEntity" if chem.get("id") else
                "biolink:EnvironmentalExposure"
            )
            self.add_node(did, dlabel, drv.get("description", ""), dcat)
            self.add_edge(did, _REL_UPSTREAM, pid, _pubs([drv]))

        # Interventions
        for iv in data.get("interventions") or []:
            ivname = iv.get("name") or "intervention"
            ivt = iv.get("intervention_term") or {}
            ivid = ivt.get("id") or f"ecomech:{file_stem}:iv:{_slug(ivname)}"
            ivlabel = ivt.get("label") or ivname
            self.add_node(ivid, ivlabel, iv.get("description", ""), "biolink:Procedure")
            self.add_edge(ivid, _REL_RELATED, pid, _pubs([iv]))

    # ── Output ──

    @property
    def nodes(self) -> list[dict[str, str]]:
        return list(self._nodes.values())

    @property
    def edges(self) -> list[dict[str, str]]:
        return self._edges


# ---------------------------------------------------------------------------
# TSV writers
# ---------------------------------------------------------------------------

def _write_tsv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Export EcoMech KB as KGX TSV files.")
    parser.add_argument("--input", default="kb/processes", help="Directory of process YAML files")
    parser.add_argument(
        "--output",
        default="export/ecomech_kgx.tsv",
        help="Output path stem (suffix is replaced with _nodes.tsv / _edges.tsv)",
    )
    args = parser.parse_args(argv)

    input_dir = Path(args.input)
    out_stem = Path(args.output).with_suffix("")
    nodes_path = Path(str(out_stem) + "_nodes.tsv")
    edges_path = Path(str(out_stem) + "_edges.tsv")

    files = sorted(input_dir.glob("*.yaml"))
    if not files:
        print(f"No YAML files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    builder = GraphBuilder()
    for f in files:
        data = yaml.safe_load(f.read_text())
        if isinstance(data, dict):
            builder.ingest(data, f.stem)

    _write_tsv(nodes_path, builder.nodes, _NODE_COLUMNS)
    _write_tsv(edges_path, builder.edges, _EDGE_COLUMNS)

    print(f"Exported {len(builder.nodes)} nodes → {nodes_path}")
    print(f"Exported {len(builder.edges)} edges → {edges_path}")


if __name__ == "__main__":
    main()
