# EcoMech — Claude Code Guidance

This is the official guidance document for Claude Code when working with EcoMech, a LinkML-based knowledge base of ecological process mechanisms analogous to [DisMech](https://github.com/monarch-initiative/dismech) but focused on ecology.

## Core Components

- **LinkML schema** — `src/ecomech/schema/ecomech.yaml` defines the data model
- **Knowledge base** — `kb/processes/*.yaml` — one YAML file per ecological process
- **Modules** — `kb/modules/*.yaml` — reusable mechanism modules
- **Groupings** — `kb/groupings/*.yaml` — curated process groupings
- **Rendered pages** — `pages/processes/*.html` — generated HTML (not committed)

## Central Ontology: ENVO Ecosystem Process Branch

The root of the ecological process hierarchy is **ENVO:02500000** (ecosystem process).
Every `EcologicalProcess` entry **must** bind to a descendant of this term via `process_term`.

Use OAK to explore available terms:
```bash
just oak-envo-ecosystem-processes        # list descendants of ENVO:02500000
just oak-search-envo "nitrogen cycling"  # search by keyword
just oak-envo ENVO:01001813              # look up a specific term
```

## Ontology Mapping Reference

| Slot | Ontology | Prefix | Example |
|------|----------|--------|---------|
| process_term | ENVO (ecosystem process branch) | ENVO: | ENVO:01001813 |
| ecological_processes | ENVO | ENVO: | ENVO:01001629 |
| biological_processes | GO | GO: | GO:0009399 |
| taxa_involved.taxon | NCBITaxon | NCBITaxon: | NCBITaxon:382 |
| indicator_term | PATO | PATO: | PATO:0000070 |
| driver_term | ECTO | ECTO: | ECTO:0000509 |
| chemical_entities / chemical_agent | CHEBI | CHEBI: | CHEBI:17997 |
| habitat_context.habitat_term | ENVO | ENVO: | ENVO:00000446 |

## Essential Commands

```bash
just install                            # Install dependencies
just qc                                 # Full QC (schema + terms + references)
just qc-fast                            # Schema + term validation only (faster)
just validate kb/processes/MyFile.yaml  # Validate a single entry
just validate-terms-file kb/processes/MyFile.yaml
just fetch-reference PMID:12345678      # Cache a PubMed reference
just validate-references kb/processes/MyFile.yaml
just oak-search-envo "decomposition"    # Search ENVO for terms
```

## YAML Entry Structure

Each entry in `kb/processes/` conforms to the `EcologicalProcess` class:

```yaml
id: ENVO:01001813
name: Nitrogen Cycling
process_term:
  id: ENVO:01001813
  label: nutrient cycling
description: >
  Nitrogen cycling encompasses the biogeochemical transformations of nitrogen
  through ecosystems...
synonyms:
  - nitrogen biogeochemical cycle
  - N cycle
ecological_scale: ECOSYSTEM
mechanisms:
  - name: Biological Nitrogen Fixation
    description: Conversion of atmospheric N2 to bioavailable ammonia by diazotrophs
    biological_processes:
      - term:
          id: GO:0009399
          label: nitrogen fixation
        evidence:
          - reference: PMID:12345678
            supports: SUPPORT
            evidence_source: FIELD_STUDY
            snippet: "Exact verbatim quote from the abstract"
            explanation: "Why this supports the claim"
    taxa_involved:
      - taxon:
          id: NCBITaxon:382
          label: Rhizobium leguminosarum
        role: NITROGEN_FIXER
indicators:
  - name: Soil ammonium concentration
    indicator_term:
      id: PATO:0000070
      label: concentration
    measurement: "NH4+ in mg/kg dry soil"
    frequency: COMMON
    evidence:
      - reference: PMID:12345678
        supports: SUPPORT
        evidence_source: FIELD_STUDY
        snippet: "..."
        explanation: "..."
drivers:
  - name: Soil temperature
    driver_type: ABIOTIC
    description: Temperature modulates rates of microbial N transformation
    evidence:
      - reference: PMID:12345679
        supports: SUPPORT
        evidence_source: FIELD_STUDY
        snippet: "..."
        explanation: "..."
interventions:
  - name: Riparian buffer establishment
    intervention_type: RESTORATION
    description: Planting vegetation buffers to reduce N loading
    evidence:
      - reference: PMID:12345680
        supports: SUPPORT
        evidence_source: FIELD_STUDY
        snippet: "..."
        explanation: "..."
habitat_context:
  - habitat_term:
      id: ENVO:00000446
      label: temperate broadleaf mixed forest biome
creation_date: "2025-06-29T00:00:00Z"
```

## Evidence Requirements

All evidence must include:
- `reference`: PMID, DOI, or structured database prefix (PMID:XXXX preferred)
- `supports`: SupportEnum value
- `evidence_source`: EvidenceSourceEnum — classifies the study type in the paper, NOT the curation method
- `snippet`: Exact verbatim quote from the abstract or main text
- `explanation`: Why this evidence supports or refutes the claim

**Evidence source classification:**
- `FIELD_STUDY`: In situ ecological data collected in natural systems
- `MESOCOSM`: Outdoor enclosures, microcosms, or mesocosms
- `LABORATORY`: Controlled lab experiments (growth chambers, incubations)
- `COMPUTATIONAL`: Models, simulations, statistical analyses
- `META_ANALYSIS`: Cross-study synthesis
- `REVIEW`: Narrative reviews
- `REMOTE_SENSING`: Satellite or aerial data
- `LONG_TERM_MONITORING`: LTER or equivalent datasets

## Critical Reference Cache Rules

Reference caches in `references_cache/` are created EXCLUSIVELY by `linkml-reference-validator`.

**NEVER manually create or edit cache files.**

Correct workflow:
1. Add YAML with `reference: PMID:XXXX` and snippet
2. Run `just fetch-reference PMID:XXXX` for each new PMID
3. Run `just validate-references kb/processes/YourFile.yaml`
4. If snippet does not match exactly, fix it or find a different reference

## Hallucination Prevention

AI tools can fabricate PMIDs, misquote snippets, and invent ontology term IDs.

**Mandatory verification for every AI-curated entry:**
1. For each PMID: run `just fetch-reference PMID:XXXX`
2. For each snippet: verify it is an exact substring of the cached abstract
3. For each ENVO/GO/NCBITaxon/PATO/ECTO term: verify with `just validate-terms-file`
4. Run `just qc-fast` before committing

If a citation cannot be verified, remove it and find an alternative.

## Curating a New Entry

1. Identify the ENVO ecosystem process term: `just oak-search-envo "your process"`
2. Confirm the term is in the ENVO:02500000 hierarchy: `just oak-envo-ecosystem-processes`
3. Research using primary literature (PubMed, Web of Science, Google Scholar)
4. Draft YAML in `kb/processes/ProcessName.yaml`
5. Fetch and validate all references
6. Run `just qc`
7. Submit as a PR

## Modules

Mechanism modules in `kb/modules/` define conserved ecological processes
reusable across multiple entries (e.g., "decomposition cascade", "predator-prey oscillation").
Entries reference modules via `conforms_to: "module_name#Node Name"` but
**always duplicate content** — not DRY. Conformance is for consistency checking only.

## Groupings

Groupings in `kb/groupings/` curate unions of EcologicalProcess entries.
Always point downward via explicit `members:` lists rather than upward inference.

## Git Practices

- Open PRs from origin, not forks
- Use worktrees for parallel work
- Commit: `kb/`, `references_cache/`, `src/`, `scripts/`, `tests/`
- Do NOT commit: `pages/processes/*.html`, `dashboard/`, `docs/site/`
- Never force-push to main
