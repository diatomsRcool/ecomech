# EcoMech — Ecological Process Mechanisms Knowledge Base

EcoMech is a curated knowledge base of ecological process mechanisms, with structured evidence from the scientific literature. It is modeled after [DisMech](https://github.com/monarch-initiative/dismech) but focused on ecological processes rather than diseases.

Each entry documents an **ecosystem process** (drawn from the ENVO ecosystem process branch) with:

- **Mechanisms** — the ecological, biological, and physicochemical steps involved
- **Indicators** — observable ecological outcomes and measurements
- **Drivers** — abiotic, biotic, and anthropogenic factors that initiate or modulate the process
- **Interventions** — management, conservation, and restoration actions

All data are backed by primary literature references with exact quoted snippets, validated against PubMed abstracts.

## Ontologies Used

| Entity Type | Ontology |
|---|---|
| Ecosystem processes | ENVO (ecosystem process branch) |
| Ecological / biological processes | GO (Gene Ontology) |
| Organisms / taxa | NCBITaxon |
| Phenotypic qualities / measurements | PATO |
| Environmental exposures / stressors | ECTO |
| Habitats / biomes / environmental conditions | ENVO |
| Chemicals (nutrients, pollutants) | CHEBI |

## Quick Start

```bash
# Install dependencies
just install

# Run all quality checks
just qc

# Validate a single process entry
just validate kb/processes/Nitrogen_Cycling.yaml

# Validate ontology term references
just validate-terms

# Fetch and cache a PubMed reference
just fetch-reference PMID:12345678
```

## Repository Structure

```
kb/processes/       # YAML knowledge base entries (one per ecological process)
kb/modules/         # Reusable mechanism modules
kb/groupings/       # Process groupings
src/ecomech/        # Python source: validation, rendering, CLI
src/ecomech/schema/ # LinkML schema definition
conf/               # OAK configuration for term validation
references_cache/   # Cached PubMed abstracts (auto-generated)
templates/          # HTML rendering templates
pages/processes/    # Generated HTML pages (derived, not committed)
tests/              # Test suite
```

## Curation

See [CONTRIBUTING.md](CONTRIBUTING.md) for curation guidelines.

Use the `/curate` skill in Claude Code to perform a full literature-driven curation workflow for a new ecological process.

## License

BSD-3-Clause
