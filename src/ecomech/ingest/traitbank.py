"""EOL TraitBank ingester for ecological traits.

TraitBank (Encyclopedia of Life) is the primary source for organism-level
ecological traits in EcoMech: trophic guild, habitat association, symbiosis
type, diet, nitrogen fixation, decomposer status, etc.

Access: Cypher API at https://eol.org/service/cypher
Authentication: JWT token — set the EOL_API_TOKEN environment variable.
  To obtain a token: contact the EOL team (eol.org).

Data model (Neo4j):
  (Page)-[:trait]->(Trait)-[:predicate]->(Term)   # what trait
                         -[:object_term]->(Term)   # categorical value
                         -[:object_page]->(Page)   # interacting taxon
  Page: {page_id, canonical, scientific_name}
  Trait: {eol_pk, measurement, literal, source, citation}
  Term: {uri, name, type}

Key ecological trait predicate URIs:
  Trophic guild / level:  http://eol.org/schema/terms/trophicLevel
  Habitat (inhabits):     http://purl.obolibrary.org/obo/RO_0002303
  Diet / eats:            http://purl.obolibrary.org/obo/RO_0002470
  Symbiosis:              http://purl.obolibrary.org/obo/RO_0002440
  Pollination interaction: http://purl.obolibrary.org/obo/RO_0002623
  Biological process:     http://purl.obolibrary.org/obo/GO_0008150
  Growth habit:           http://eol.org/schema/terms/growthHabit
  Nitrogen fixation:      http://purl.obolibrary.org/obo/GO_0009399

Usage:
    export EOL_API_TOKEN="your_token_here"

    # Traits for a single taxon
    uv run python -m ecomech.ingest.traitbank traits "Rhizobium leguminosarum"

    # All taxa exhibiting a named ecological role
    uv run python -m ecomech.ingest.traitbank taxa-for-role decomposer --limit 20
    uv run python -m ecomech.ingest.traitbank taxa-for-role nitrogen_fixer
    uv run python -m ecomech.ingest.traitbank taxa-for-role methanogen

    # Raw Cypher query
    uv run python -m ecomech.ingest.traitbank cypher "MATCH (p:Page) RETURN p.canonical LIMIT 5"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any

from ecomech.ingest.base import BaseIngester, IngestRecord

_CYPHER_URL = "https://eol.org/service/cypher"
_TIMEOUT = 30

# ---------------------------------------------------------------------------
# Curated ecological role → TraitBank predicate + value URIs
# ---------------------------------------------------------------------------

# Each entry: (predicate_uri, optional_value_uri_or_literal)
# None for value_uri means match any value for that predicate.
ECOLOGICAL_ROLES: dict[str, dict[str, str]] = {
    # Decomposers / saprotrophs
    "decomposer": {
        "predicate": "http://eol.org/schema/terms/trophicLevel",
        "value": "http://eol.org/schema/terms/decomposer",
        "notes": "Trophic level = decomposer/saprotroph",
    },
    "saprotroph": {
        "predicate": "http://eol.org/schema/terms/trophicLevel",
        "value": "http://eol.org/schema/terms/decomposer",
    },
    # Nitrogen cycling
    "nitrogen_fixer": {
        "predicate": "http://purl.obolibrary.org/obo/RO_0002303",
        "value": "http://purl.obolibrary.org/obo/GO_0009399",
        "notes": "Inhabits GO:0009399 (nitrogen fixation) — biological process",
    },
    # Primary producers
    "primary_producer": {
        "predicate": "http://eol.org/schema/terms/trophicLevel",
        "value": "http://eol.org/schema/terms/autotroph",
    },
    "photoautotroph": {
        "predicate": "http://eol.org/schema/terms/trophicLevel",
        "value": "http://eol.org/schema/terms/photoautotroph",
    },
    # Consumers
    "herbivore": {
        "predicate": "http://eol.org/schema/terms/trophicLevel",
        "value": "http://eol.org/schema/terms/herbivore",
    },
    "carnivore": {
        "predicate": "http://eol.org/schema/terms/trophicLevel",
        "value": "http://eol.org/schema/terms/carnivore",
    },
    # Pollinators
    "pollinator": {
        "predicate": "http://purl.obolibrary.org/obo/RO_0002623",
        "value": None,
        "notes": "RO:0002623 = visits flowers of",
    },
    # Symbioses
    "mycorrhiza": {
        "predicate": "http://purl.obolibrary.org/obo/RO_0002440",
        "value": "http://eol.org/schema/terms/mycorrhizal",
        "notes": "Symbiotic interaction = mycorrhizal",
    },
    # Methanogens
    "methanogen": {
        "predicate": "http://purl.obolibrary.org/obo/RO_0002303",
        "value": "http://purl.obolibrary.org/obo/GO_0015948",
        "notes": "Inhabits GO:0015948 (methanogenesis)",
    },
    # Seed dispersers
    "seed_disperser": {
        "predicate": "http://purl.obolibrary.org/obo/RO_0002303",
        "value": "http://purl.obolibrary.org/obo/GO_0010188",
        "notes": "Seed dispersal interaction",
    },
}

# ---------------------------------------------------------------------------
# Cypher query templates
# ---------------------------------------------------------------------------

_TRAITS_FOR_TAXON = """\
MATCH (p:Page {{canonical: {name!r}}})-[:trait]->(t:Trait),
      (t)-[:predicate]->(pred:Term)
OPTIONAL MATCH (t)-[:object_term]->(obj:Term)
RETURN pred.name AS trait, pred.uri AS predicate_uri,
       obj.name AS value, t.measurement AS measurement,
       t.literal AS literal, t.source AS source
LIMIT {limit}
"""

_TAXA_FOR_PREDICATE_VALUE = """\
MATCH (t:Trait)-[:predicate]->(pred:Term {{uri: {pred_uri!r}}}),
      (t)-[:object_term]->(val:Term {{uri: {val_uri!r}}}),
      (p:Page)-[:trait]->(t)
WHERE p.canonical IS NOT NULL
RETURN DISTINCT p.page_id AS page_id, p.canonical AS name
LIMIT {limit}
"""

_TAXA_FOR_PREDICATE_ANY = """\
MATCH (t:Trait)-[:predicate]->(pred:Term {{uri: {pred_uri!r}}}),
      (p:Page)-[:trait]->(t)
WHERE p.canonical IS NOT NULL
RETURN DISTINCT p.page_id AS page_id, p.canonical AS name
LIMIT {limit}
"""

_EOL_ID_TO_NCBI = """\
MATCH (p:Page {{page_id: {page_id}}})
OPTIONAL MATCH (p)-[:provider]->(ext)
WHERE ext.resource_id = 'ncbi'
RETURN p.canonical AS name, ext.resource_pk AS ncbi_id
LIMIT 1
"""


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

class TraitBankClient:
    """Low-level Cypher API client for EOL TraitBank.

    Requires an EOL API token in the EOL_API_TOKEN environment variable.
    Contact the EOL team to obtain a token.
    """

    def __init__(self, token: str | None = None) -> None:
        self._token = token or os.environ.get("EOL_API_TOKEN", "")

    @property
    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
        if self._token:
            h["Authorization"] = f"JWT {self._token}"
        return h

    def query(self, cypher: str, fmt: str = "json") -> list[dict[str, Any]]:
        """Execute a Cypher query and return rows as a list of dicts."""
        body = urllib.parse.urlencode({"query": cypher, "format": fmt}).encode()
        req = urllib.request.Request(_CYPHER_URL, data=body, headers=self._headers, method="POST")
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        # TraitBank returns {"columns": [...], "data": [[...], ...]}
        columns = data.get("columns") or []
        rows = data.get("data") or []
        return [dict(zip(columns, row)) for row in rows]

    def traits_for_taxon(self, canonical_name: str, limit: int = 50) -> list[dict[str, Any]]:
        """Return trait records for a taxon by canonical name."""
        cypher = _TRAITS_FOR_TAXON.format(name=canonical_name, limit=limit)
        return self.query(cypher)

    def taxa_for_role(self, role: str, limit: int = 50) -> list[dict[str, Any]]:
        """Return taxa exhibiting a named ecological role.

        `role` must be a key in ECOLOGICAL_ROLES (e.g. 'decomposer',
        'nitrogen_fixer', 'pollinator', 'methanogen').
        """
        spec = ECOLOGICAL_ROLES.get(role)
        if spec is None:
            available = ", ".join(sorted(ECOLOGICAL_ROLES))
            raise ValueError(f"Unknown role {role!r}. Available: {available}")
        pred_uri = spec["predicate"]
        val_uri = spec.get("value")
        if val_uri:
            cypher = _TAXA_FOR_PREDICATE_VALUE.format(
                pred_uri=pred_uri, val_uri=val_uri, limit=limit
            )
        else:
            cypher = _TAXA_FOR_PREDICATE_ANY.format(pred_uri=pred_uri, limit=limit)
        return self.query(cypher)


# ---------------------------------------------------------------------------
# Ingester wrapper
# ---------------------------------------------------------------------------

class TraitBankIngester(BaseIngester):
    """Fetch ecological trait records from EOL TraitBank."""

    source_name = "TraitBank"

    def __init__(self, token: str | None = None) -> None:
        self._client = TraitBankClient(token)

    def search(self, query: str, limit: int = 20) -> list[IngestRecord]:
        """Return trait records for a taxon name."""
        rows = self._client.traits_for_taxon(query, limit=limit)
        records = []
        for row in rows:
            trait = row.get("trait") or row.get("predicate_uri", "")
            value = row.get("value") or row.get("measurement") or row.get("literal", "")
            records.append(IngestRecord(
                source="TraitBank",
                source_id=row.get("predicate_uri", ""),
                name=f"{query}: {trait}",
                description=str(value),
                url=f"https://eol.org/pages?q={urllib.parse.quote(query)}",
                metadata=row,
            ))
        return records

    def fetch(self, record_id: str) -> IngestRecord | None:
        """Fetch traits for a taxon by its canonical name (record_id)."""
        rows = self._client.traits_for_taxon(record_id, limit=50)
        if not rows:
            return None
        return IngestRecord(
            source="TraitBank",
            source_id=record_id,
            name=record_id,
            description=f"{len(rows)} trait records",
            url=f"https://eol.org/pages?q={urllib.parse.quote(record_id)}",
            metadata={"traits": rows},
        )

    def taxa_for_role(
        self, role: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Return taxa exhibiting a named ecological role."""
        return self._client.taxa_for_role(role, limit=limit)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Query EOL TraitBank for organism ecological traits.",
        epilog="Requires EOL_API_TOKEN env var. Contact eol.org to obtain one.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    tr = sub.add_parser("traits", help="Traits for a named taxon")
    tr.add_argument("name", help="Canonical scientific name")
    tr.add_argument("--limit", type=int, default=30)
    tr.add_argument("--output", default="")

    ro = sub.add_parser("taxa-for-role", help="Taxa with a named ecological role")
    ro.add_argument(
        "role",
        choices=sorted(ECOLOGICAL_ROLES),
        help="Ecological role key",
    )
    ro.add_argument("--limit", type=int, default=30)
    ro.add_argument("--output", default="")

    roles = sub.add_parser("roles", help="List available ecological role keys")

    cy = sub.add_parser("cypher", help="Run a raw Cypher query")
    cy.add_argument("query", help="Cypher query string")
    cy.add_argument("--output", default="")

    args = parser.parse_args(argv)

    if args.cmd == "roles":
        print("Available ecological roles for taxa-for-role:")
        for role, spec in sorted(ECOLOGICAL_ROLES.items()):
            notes = spec.get("notes", "")
            print(f"  {role:<20}  {notes or spec['predicate']}")
        return

    token = os.environ.get("EOL_API_TOKEN", "")
    if not token and args.cmd != "roles":
        print(
            "Warning: EOL_API_TOKEN not set. Set it to a valid JWT token "
            "obtained from the EOL team (eol.org). Queries may fail.",
            file=sys.stderr,
        )

    ingester = TraitBankIngester(token)

    if args.cmd == "traits":
        records = ingester.search(args.name, limit=args.limit)
        print(f"Traits for '{args.name}' ({len(records)} records):")
        for r in records:
            print(f"  {r.name:<50}  {r.description}")
        if args.output:
            ingester.save(records, Path(args.output))
            print(f"Saved to {args.output}")

    elif args.cmd == "taxa-for-role":
        taxa = ingester.taxa_for_role(args.role, limit=args.limit)
        spec = ECOLOGICAL_ROLES[args.role]
        print(f"Taxa for role '{args.role}' ({len(taxa)} results):")
        print(f"  Predicate: {spec['predicate']}")
        if spec.get("value"):
            print(f"  Value:     {spec['value']}")
        print()
        for t in taxa:
            print(f"  {t.get('name', ''):<40}  EOL:{t.get('page_id', '')}")
        if args.output:
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w") as fh:
                for t in taxa:
                    fh.write(json.dumps(t) + "\n")
            print(f"Saved to {args.output}")

    elif args.cmd == "cypher":
        client = TraitBankClient(token)
        rows = client.query(args.query)
        print(json.dumps(rows, indent=2))
        if args.output:
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w") as fh:
                for row in rows:
                    fh.write(json.dumps(row) + "\n")
            print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
