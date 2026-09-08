"""LTER (Long-Term Ecological Research) network data ingester.

Fetches dataset metadata from the LTER Data Portal (EDI) via the
EML/PASTA REST API. Useful for finding long-term monitoring datasets
that can serve as LONG_TERM_MONITORING evidence sources.

PASTA API docs: https://pastaplus-core.readthedocs.io/en/latest/
No API key required for public datasets.

Usage:
    uv run python -m ecomech.ingest.lter search "nitrogen cycling"
    uv run python -m ecomech.ingest.lter search "primary production" --limit 10
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from ecomech.ingest.base import BaseIngester, IngestRecord

_PASTA_API = "https://pasta.lternet.edu/package/search/eml"
_TIMEOUT = 20


def _solr_search(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({
        "q": query,
        "rows": limit,
        "fl": "packageid,title,abstract,doi,pubdate,site",
        "fq": "pubdate:[2000-01-01T00:00:00Z TO NOW]",
        "sort": "score desc",
    })
    url = f"{_PASTA_API}?{params}"
    req = urllib.request.Request(url, headers={"Accept": "application/xml"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        xml_bytes = resp.read()
    root = ET.fromstring(xml_bytes)
    docs = root.findall(".//doc")
    results = []
    for doc in docs:
        d: dict[str, Any] = {}
        for field in doc.findall("str"):
            d[field.get("name", "")] = field.text or ""
        for field in doc.findall("arr"):
            name = field.get("name", "")
            d[name] = [el.text or "" for el in field]
        results.append(d)
    return results


class LTERIngester(BaseIngester):
    """Fetch LTER dataset metadata from the EDI PASTA portal."""

    source_name = "LTER-EDI"

    def search(self, query: str, limit: int = 20) -> list[IngestRecord]:
        results = _solr_search(query, limit)
        return [r for r in (self._result_to_record(d) for d in results) if r]

    def fetch(self, record_id: str) -> IngestRecord | None:
        """Fetch by PASTA package ID (e.g. 'knb-lter-cap.46.8')."""
        results = _solr_search(f"packageid:{record_id}", limit=1)
        if results:
            return self._result_to_record(results[0])
        return None

    def _result_to_record(self, d: dict[str, Any]) -> IngestRecord | None:
        pkg_id = d.get("packageid", "")
        if not pkg_id:
            return None
        title = d.get("title", "")
        if isinstance(title, list):
            title = title[0] if title else ""
        abstract = d.get("abstract", "")
        if isinstance(abstract, list):
            abstract = abstract[0] if abstract else ""
        doi = d.get("doi", "")
        if isinstance(doi, list):
            doi = doi[0] if doi else ""
        site = d.get("site", "")
        if isinstance(site, list):
            site = site[0] if site else ""
        return IngestRecord(
            source="LTER-EDI",
            source_id=pkg_id,
            name=title[:200],
            description=abstract[:500],
            url=f"https://portal.edirepository.org/nis/mapbrowse?packageid={pkg_id}",
            metadata={
                "doi": doi,
                "site": site,
                "pubdate": d.get("pubdate", ""),
                "suggested_evidence_source": "LONG_TERM_MONITORING",
            },
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Search LTER-EDI for long-term ecological datasets.")
    parser.add_argument("cmd", choices=["search"], help="Command")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output", default="", help="Save JSON lines to this path")
    args = parser.parse_args(argv)

    ingester = LTERIngester()
    records = ingester.search(args.query, limit=args.limit)
    print(f"Found {len(records)} LTER datasets for '{args.query}':")
    for r in records:
        doi_str = f"  DOI:{r.metadata.get('doi', '')}" if r.metadata.get("doi") else ""
        print(f"  {r.source_id:<30}  {r.name[:60]}{doi_str}")
    if args.output:
        ingester.save(records, Path(args.output))
        print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
