"""GBIF (Global Biodiversity Information Facility) ingester.

Fetches species occurrence data and taxon records from the GBIF API to
enrich EcoMech process entries with curated taxon information.

GBIF API docs: https://www.gbif.org/developer/summary
No API key required for read-only queries.

Usage:
    uv run python -m ecomech.ingest.gbif search "Rhizobium"
    uv run python -m ecomech.ingest.gbif fetch 2598429         # GBIF taxon key
    uv run python -m ecomech.ingest.gbif search "mycorrhizal fungi" --output research/gbif_taxa.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any

from ecomech.ingest.base import BaseIngester, IngestRecord

_GBIF_API = "https://api.gbif.org/v1"
_TIMEOUT = 15


def _get(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode())


class GBIFIngester(BaseIngester):
    """Fetch taxon records from GBIF Species API."""

    source_name = "GBIF"

    def search(self, query: str, limit: int = 20) -> list[IngestRecord]:
        """Search GBIF species backbone by name."""
        params = urllib.parse.urlencode({"q": query, "limit": limit})
        url = f"{_GBIF_API}/species/search?{params}"
        data = _get(url)
        records = []
        for result in data.get("results") or []:
            rec = self._result_to_record(result)
            if rec:
                records.append(rec)
        return records

    def fetch(self, record_id: str) -> IngestRecord | None:
        """Fetch a GBIF taxon by its integer taxon key."""
        url = f"{_GBIF_API}/species/{record_id}"
        try:
            data = _get(url)
        except Exception:
            return None
        return self._result_to_record(data)

    def _result_to_record(self, result: dict[str, Any]) -> IngestRecord | None:
        key = result.get("key") or result.get("nubKey")
        if not key:
            return None
        name = result.get("canonicalName") or result.get("scientificName", "")
        rank = result.get("rank", "")
        kingdom = result.get("kingdom", "")
        ncbi_id = result.get("nubKey")  # closest proxy; GBIF also has taxonID
        return IngestRecord(
            source="GBIF",
            source_id=str(key),
            name=name,
            description=f"{rank} in {kingdom}" if rank or kingdom else "",
            url=f"https://www.gbif.org/species/{key}",
            metadata={
                "rank": rank,
                "kingdom": kingdom,
                "phylum": result.get("phylum", ""),
                "class": result.get("class", ""),
                "order": result.get("order", ""),
                "family": result.get("family", ""),
                "genus": result.get("genus", ""),
                "nubKey": ncbi_id,
                "status": result.get("taxonomicStatus", ""),
                "ncbitaxon_curie": f"NCBITaxon:{ncbi_id}" if ncbi_id else "",
            },
        )

    def ncbitaxon_curie(self, record: IngestRecord) -> str:
        """Return the NCBITaxon CURIE for a record if available."""
        return record.metadata.get("ncbitaxon_curie", "")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Fetch taxon records from GBIF.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="Search GBIF by name")
    s.add_argument("query", help="Taxon name or keyword")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--output", default="", help="Save results as JSON lines to this path")

    f = sub.add_parser("fetch", help="Fetch a GBIF taxon by key")
    f.add_argument("key", help="GBIF taxon key (integer)")
    f.add_argument("--output", default="")

    args = parser.parse_args(argv)
    ingester = GBIFIngester()

    if args.cmd == "search":
        records = ingester.search(args.query, limit=args.limit)
        print(f"Found {len(records)} taxa for '{args.query}':")
        for r in records:
            ncbi = r.metadata.get("ncbitaxon_curie", "")
            ncbi_str = f"  [{ncbi}]" if ncbi else ""
            print(f"  {r.source_id:>10}  {r.name:<40}  {r.description}{ncbi_str}")
        if args.output:
            ingester.save(records, Path(args.output))
            print(f"Saved to {args.output}")

    elif args.cmd == "fetch":
        record = ingester.fetch(args.key)
        if record:
            print(json.dumps(record.to_dict(), indent=2))
            if args.output:
                ingester.save([record], Path(args.output))
        else:
            print(f"No record found for key {args.key}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
