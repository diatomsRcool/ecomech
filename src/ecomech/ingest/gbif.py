"""GBIF (Global Biodiversity Information Facility) occurrence ingester.

**Scope: geographic occurrence data only.**
Use this module to answer "where has this taxon been observed?" and to find
taxa present in a specific ecoregion or country. Do NOT use GBIF to infer
ecological traits or functional roles — use TraitBank for that.

GBIF API docs: https://www.gbif.org/developer/summary
No API key required for read-only queries.

Usage:
    # Resolve a name to a GBIF taxon key (and NCBITaxon CURIE)
    uv run python -m ecomech.ingest.gbif resolve "Rhizobium leguminosarum"

    # Find occurrences of a taxon (by GBIF key) in a country or GADM region
    uv run python -m ecomech.ingest.gbif occurrences 2598429 --country BR
    uv run python -m ecomech.ingest.gbif occurrences 2598429 --gadm "BRA.17_1"

    # Find all taxa recorded in a country/region (useful for biome diversity)
    uv run python -m ecomech.ingest.gbif taxa-in-region --country TZ --rank GENUS --limit 20
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


# ---------------------------------------------------------------------------
# Name resolution (backbone lookup — used internally to get taxon keys)
# ---------------------------------------------------------------------------

def resolve_name(name: str) -> dict[str, Any] | None:
    """Resolve a scientific name to its GBIF backbone record.

    Returns a dict with gbif_key, ncbitaxon_curie, canonical_name, rank, etc.
    This is a utility used by other methods, not a trait source.
    """
    params = urllib.parse.urlencode({"name": name, "verbose": "false"})
    url = f"{_GBIF_API}/species/match?{params}"
    data = _get(url)
    if data.get("matchType") == "NONE":
        return None
    key = data.get("usageKey")
    nub = data.get("usageKey")
    return {
        "gbif_key": key,
        "ncbitaxon_curie": f"NCBITaxon:{nub}" if nub else "",
        "canonical_name": data.get("canonicalName") or data.get("scientificName", ""),
        "rank": data.get("rank", ""),
        "kingdom": data.get("kingdom", ""),
        "confidence": data.get("confidence", 0),
        "status": data.get("status", ""),
    }


# ---------------------------------------------------------------------------
# Occurrence queries
# ---------------------------------------------------------------------------

class GBIFOccurrenceIngester(BaseIngester):
    """Query GBIF for species occurrence records.

    Purpose: geographic distribution data — which taxa have been observed
    in which countries, regions, or biomes. Not for inferring traits.
    """

    source_name = "GBIF-occurrences"

    def search(self, query: str, limit: int = 20) -> list[IngestRecord]:
        """Search occurrences by scientific name."""
        resolved = resolve_name(query)
        if not resolved:
            return []
        return self.occurrences_for_key(str(resolved["gbif_key"]), limit=limit)

    def fetch(self, record_id: str) -> IngestRecord | None:
        """Fetch a single GBIF occurrence record by its occurrence key."""
        url = f"{_GBIF_API}/occurrence/{record_id}"
        try:
            data = _get(url)
        except Exception:
            return None
        return self._occ_to_record(data)

    def occurrences_for_key(
        self,
        gbif_taxon_key: str,
        country: str = "",
        gadm_gid: str = "",
        limit: int = 20,
    ) -> list[IngestRecord]:
        """Return occurrence records for a GBIF taxon key.

        Args:
            gbif_taxon_key: GBIF integer taxon key.
            country: ISO 3166-1 alpha-2 country code (e.g. "BR", "TZ").
            gadm_gid: GADM region identifier (e.g. "BRA.17_1").
            limit: Maximum records to return.
        """
        params: dict[str, Any] = {
            "taxonKey": gbif_taxon_key,
            "hasCoordinate": "true",
            "limit": limit,
        }
        if country:
            params["country"] = country
        if gadm_gid:
            params["gadmGid"] = gadm_gid
        url = f"{_GBIF_API}/occurrence/search?{urllib.parse.urlencode(params)}"
        data = _get(url)
        return [r for r in (self._occ_to_record(o) for o in data.get("results") or []) if r]

    def taxa_in_region(
        self,
        country: str = "",
        gadm_gid: str = "",
        rank: str = "SPECIES",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Return distinct taxa observed in a country or GADM region.

        Returns a list of dicts with taxon name, GBIF key, rank, and NCBITaxon CURIE.
        Useful for finding what taxa are present in a biome to guide KB curation.
        """
        params: dict[str, Any] = {
            "hasCoordinate": "true",
            "taxonRank": rank,
            "facet": "SPECIES_KEY",
            "facetLimit": limit,
            "limit": 0,  # we only want facets
        }
        if country:
            params["country"] = country
        if gadm_gid:
            params["gadmGid"] = gadm_gid
        url = f"{_GBIF_API}/occurrence/search?{urllib.parse.urlencode(params)}"
        data = _get(url)
        results = []
        for facet in (data.get("facets") or []):
            if facet.get("field") == "SPECIES_KEY":
                for count_item in facet.get("counts") or []:
                    key = count_item.get("name")
                    if key:
                        try:
                            spp = _get(f"{_GBIF_API}/species/{key}")
                            results.append({
                                "gbif_key": key,
                                "name": spp.get("canonicalName") or spp.get("scientificName", ""),
                                "rank": spp.get("rank", ""),
                                "kingdom": spp.get("kingdom", ""),
                                "ncbitaxon_curie": f"NCBITaxon:{spp.get('nubKey')}" if spp.get("nubKey") else "",
                                "occurrence_count": count_item.get("count", 0),
                            })
                        except Exception:
                            pass
        return results

    def _occ_to_record(self, occ: dict[str, Any]) -> IngestRecord | None:
        occ_key = occ.get("key")
        if not occ_key:
            return None
        name = occ.get("scientificName") or occ.get("acceptedScientificName", "")
        lat = occ.get("decimalLatitude")
        lon = occ.get("decimalLongitude")
        country = occ.get("country", "")
        return IngestRecord(
            source="GBIF",
            source_id=str(occ_key),
            name=name,
            description=f"{country} ({lat}, {lon})" if lat and lon else country,
            url=f"https://www.gbif.org/occurrence/{occ_key}",
            metadata={
                "taxon_key": occ.get("taxonKey"),
                "ncbitaxon_curie": f"NCBITaxon:{occ.get('taxonKey')}" if occ.get("taxonKey") else "",
                "country": country,
                "countryCode": occ.get("countryCode", ""),
                "lat": lat,
                "lon": lon,
                "year": occ.get("year"),
                "dataset": occ.get("datasetName", ""),
                "basis": occ.get("basisOfRecord", ""),
            },
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Query GBIF for species occurrence / distribution data."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("resolve", help="Resolve a taxon name to GBIF key + NCBITaxon CURIE")
    r.add_argument("name", help="Scientific name")

    o = sub.add_parser("occurrences", help="Occurrence records for a taxon")
    o.add_argument("key", help="GBIF taxon key")
    o.add_argument("--country", default="", help="ISO 3166-1 alpha-2 country code (e.g. BR)")
    o.add_argument("--gadm", default="", help="GADM region ID (e.g. BRA.17_1)")
    o.add_argument("--limit", type=int, default=10)
    o.add_argument("--output", default="")

    t = sub.add_parser("taxa-in-region", help="Taxa observed in a country or GADM region")
    t.add_argument("--country", default="")
    t.add_argument("--gadm", default="")
    t.add_argument("--rank", default="GENUS", choices=["SPECIES", "GENUS", "FAMILY"])
    t.add_argument("--limit", type=int, default=20)
    t.add_argument("--output", default="")

    args = parser.parse_args(argv)
    ingester = GBIFOccurrenceIngester()

    if args.cmd == "resolve":
        result = resolve_name(args.name)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print(f"No match found for '{args.name}'", file=sys.stderr)
            sys.exit(1)

    elif args.cmd == "occurrences":
        records = ingester.occurrences_for_key(
            args.key, country=args.country, gadm_gid=args.gadm, limit=args.limit
        )
        print(f"Found {len(records)} occurrences for taxon key {args.key}:")
        for rec in records:
            print(f"  {rec.source_id}  {rec.name:<40}  {rec.description}")
        if args.output:
            ingester.save(records, Path(args.output))
            print(f"Saved to {args.output}")

    elif args.cmd == "taxa-in-region":
        if not args.country and not args.gadm:
            print("Provide --country or --gadm", file=sys.stderr)
            sys.exit(1)
        taxa = ingester.taxa_in_region(
            country=args.country, gadm_gid=args.gadm, rank=args.rank, limit=args.limit
        )
        print(f"Found {len(taxa)} taxa at rank {args.rank}:")
        for t in taxa:
            ncbi = t.get("ncbitaxon_curie", "")
            print(f"  {t['name']:<40}  {ncbi}  (n={t.get('occurrence_count',0)})")
        if args.output:
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w") as fh:
                for t in taxa:
                    fh.write(json.dumps(t) + "\n")
            print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
