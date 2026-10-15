"""Fetch recent ecology process papers from Europe PMC and write a JSON packet.

The packet is consumed by the literature-scan agent workflow.

Usage:
    python -m ecomech.ingest.literature_packet --source MED --days 7 \\
        --output literature_packet.json
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

EUROPE_PMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

# Core ecology process keywords.  Kept short to avoid over-long URLs.
ECOLOGY_TERMS = [
    '"ecosystem process"',
    '"biogeochemical cycle"',
    '"nutrient cycling"',
    '"decomposition"',
    '"primary production"',
    '"trophic interaction"',
    '"nitrogen fixation"',
    '"denitrification"',
    '"carbon sequestration"',
    '"soil microbial"',
    '"succession"',
    '"symbiosis"',
]


def build_query(source: str, days: int) -> str:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    keyword_clause = " OR ".join(ECOLOGY_TERMS[:8])
    parts = [
        f"({keyword_clause})",
        f"FIRST_PDATE:[{cutoff} TO {today}]",
        "HAS_ABSTRACT:Y",
    ]
    if source == "MED":
        parts.append("SRC:MED")
    elif source == "PPR":
        parts.append("SRC:PPR")
    # "ALL" adds no source filter

    return " AND ".join(parts)


def fetch_papers(query: str, max_results: int) -> list[dict]:
    params = urllib.parse.urlencode({
        "query": query,
        "format": "json",
        "pageSize": max_results,
        "resultType": "core",
        "sort": "FIRST_PDATE desc",
    })
    url = f"{EUROPE_PMC_URL}?{params}"

    req = urllib.request.Request(url, headers={"User-Agent": "ecomech-literature-scan/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    papers = []
    for result in data.get("resultList", {}).get("result", []):
        pmid = result.get("pmid")
        result_id = result.get("id", "")
        if pmid:
            paper_id = f"PMID:{pmid}"
        elif result_id.startswith("PPR"):
            paper_id = f"PPR:{result_id}"
        else:
            paper_id = result_id

        papers.append({
            "id": paper_id,
            "title": result.get("title", ""),
            "abstract": result.get("abstractText", ""),
            "journal": result.get("journalTitle", ""),
            "year": result.get("pubYear", ""),
            "authors": result.get("authorString", ""),
        })

    return papers


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a literature packet for the scan agent.")
    parser.add_argument("--source", choices=["MED", "PPR", "ALL"], default="MED",
                        help="Paper source: MED=PubMed, PPR=preprints, ALL=both")
    parser.add_argument("--days", type=int, default=7,
                        help="Lookback window in days")
    parser.add_argument("--max-results", type=int, default=50,
                        help="Maximum papers to fetch")
    parser.add_argument("--output", default="literature_packet.json",
                        help="Output JSON file path")
    args = parser.parse_args()

    query = build_query(args.source, args.days)
    print(f"Query: {query}", file=sys.stderr)

    papers = fetch_papers(query, args.max_results)
    print(f"Fetched {len(papers)} papers", file=sys.stderr)

    packet = {
        "source": args.source,
        "days": args.days,
        "query": query,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "paper_count": len(papers),
        "papers": papers,
    }

    Path(args.output).write_text(json.dumps(packet, indent=2, ensure_ascii=False))
    print(f"Packet written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
