# /curate — EcoMech Curation Skill

Perform a full, literature-driven curation workflow for a new ecological process entry.

## Usage

```
/curate <process name>
```

Examples:
- `/curate Denitrification`
- `/curate Marine sediment bioturbation`
- `/curate Mycorrhizal phosphorus uptake`

---

## Curation Workflow

When invoked, follow these steps exactly:

### Step 1 — Find the ENVO/ECOCORE Term

**Always search both ontologies and pick the most specific match.**

#### 1a — Search ENVO first (preferred)

```bash
just oak-search-envo "<process name>"
```

If a hit looks promising, confirm it falls under ENVO:02500000 (ecosystem process):
```bash
uv run runoak -i sqlite:obo:envo ancestors <ENVO:XXXXXXX>
# Look for ENVO:02500000 in the output — if present, the term is valid
```

#### 1b — Search ECOCORE if ENVO has no suitable term

ECOCORE queries require a local OWL file at `conf/ecocore.owl`. Populate it once:

```bash
just update-ecocore
# Copies from ~/ecocore/ecocore.owl if that local checkout exists,
# otherwise downloads from purl.obolibrary.org.
# Set ECOCORE_LOCAL=/path/to/ecocore.owl to override the source path.
```

Then search and inspect terms:

```bash
just oak-search-ecocore "<keyword>"        # label-match search (e.g. "nitrogen", "decomposition")
just oak-ecocore <ECOCORE:XXXXXXX>        # full term details for a specific ID
just oak-ecocore-processes                 # list all ECOCORE ecological process terms
just oak-ecocore-ancestors <ECOCORE:XXXXXXX>   # show parent hierarchy
```

#### 1c — Decision rules

| Situation | Action |
|-----------|--------|
| ENVO term found under ENVO:02500000 | Use it; set `process_term.id: ENVO:XXXXXXX` |
| ECOCORE term found; ENVO has no match | Use ECOCORE; set `process_term.id: ECOCORE:XXXXXXX` |
| Both ENVO and ECOCORE terms found | Prefer ENVO; note ECOCORE equivalent in `synonyms` |
| Neither found | Use the closest available parent and note the gap; propose a new ECOCORE term per WORKPLAN.md §2a |

The `process_term.label` must be the **exact canonical label** returned by OAK, not a paraphrase.

### Step 2 — Research the Process

Search PubMed for each of these aspects:
- Core mechanisms (2–4 papers)
- Quantitative indicators / measurements (1–2 papers)
- Key abiotic and biotic drivers (1–2 papers)
- Restoration or management interventions (1 paper)

Use queries like:
```
"<process name>" mechanism ecological review
"<process name>" field study measurement
"<process name>" driver temperature moisture
"<process name>" restoration management
```

Fetch and cache each PMID before use:
```bash
just fetch-reference PMID:XXXXXXXX
```

**Hallucination prevention**: Never invent PMIDs. Only use PMIDs you can verify exist via `just fetch-reference`.

### Step 3 — Draft the YAML

Create `kb/processes/<ProcessName>.yaml`. Use the template below, replacing all placeholders.

Required fields:
- `id` — the ENVO/ECOCORE CURIE from Step 1
- `name` — human-readable name
- `process_term` — `{id: ..., label: ...}` from Step 1
- `description` — 2–4 sentences summarizing the process
- `ecological_scale` — one of: ORGANISM, POPULATION, COMMUNITY, ECOSYSTEM, LANDSCAPE, BIOME, GLOBAL
- `creation_date` — today's ISO timestamp

Each mechanism must have:
- `name` and `description`
- At least one `biological_processes` entry with GO term
- At least one `evidence` item with exact verbatim `snippet`

### Step 4 — Validate Ontology Terms

```bash
just validate-terms-file kb/processes/<ProcessName>.yaml
```

Fix any unresolved CURIE errors before proceeding.

### Step 5 — Validate References

For each PMID in the file:
```bash
just fetch-reference PMID:XXXXXXXX
```

Then validate snippets are exact verbatim quotes:
```bash
just validate-references kb/processes/<ProcessName>.yaml
```

Fix any snippet mismatches. Snippets must be **exact substrings** of the cached abstract.

### Step 6 — Full QC

```bash
just qc-fast
```

All checks must pass before committing.

### Step 7 — Commit

```bash
git add kb/processes/<ProcessName>.yaml references_cache/
git commit -m "Add <ProcessName> ecological process entry"
```

---

## YAML Template

```yaml
id: ENVO:XXXXXXXX        # or ECOCORE:XXXXXXXX
name: <Process Name>
process_term:
  id: ENVO:XXXXXXXX
  label: <envo canonical label>
description: >
  <2-4 sentence description of the process, its ecological role, and
  the systems it occurs in.>
synonyms:
  - <common alternative name>
ecological_scale: ECOSYSTEM
mechanisms:
  - name: <Mechanism Name>
    description: <1-2 sentence mechanistic description>
    biological_processes:
      - term:
          id: GO:XXXXXXX
          label: <go term label>
        evidence:
          - reference: PMID:XXXXXXXX
            supports: SUPPORT
            evidence_source: FIELD_STUDY
            snippet: "Exact verbatim quote from the abstract"
            explanation: "Why this supports the mechanism claim"
    taxa_involved:
      - taxon:
          id: NCBITaxon:XXXXXX
          label: <Species name>
        role: <DECOMPOSER|NITROGEN_FIXER|PRODUCER|etc>
indicators:
  - name: <Indicator Name>
    indicator_term:
      id: PATO:XXXXXXX
      label: <pato term label>
    measurement: "<units and method, e.g. μmol N m⁻² h⁻¹>"
    frequency: COMMON
    evidence:
      - reference: PMID:XXXXXXXX
        supports: SUPPORT
        evidence_source: FIELD_STUDY
        snippet: "Exact verbatim quote"
        explanation: "Why this is an indicator"
drivers:
  - name: <Driver Name>
    driver_type: <ABIOTIC|BIOTIC|ANTHROPOGENIC|CLIMATE|GEOCHEMICAL>
    description: <How this driver modulates the process>
    evidence:
      - reference: PMID:XXXXXXXX
        supports: SUPPORT
        evidence_source: FIELD_STUDY
        snippet: "Exact verbatim quote"
        explanation: "Why this is a driver"
interventions:
  - name: <Intervention Name>
    intervention_type: <RESTORATION|MANAGEMENT|PROTECTION|MITIGATION|REMOVAL|MONITORING>
    description: <What the intervention does>
    evidence:
      - reference: PMID:XXXXXXXX
        supports: SUPPORT
        evidence_source: FIELD_STUDY
        snippet: "Exact verbatim quote"
        explanation: "Why this intervention is effective"
habitat_context:
  - habitat_term:
      id: ENVO:XXXXXXXX
      label: <habitat label>
creation_date: "2026-09-08T00:00:00Z"
```

---

## Evidence Source Classification

| Code | Use When |
|------|----------|
| `FIELD_STUDY` | In situ data collected in natural ecosystems |
| `LONG_TERM_MONITORING` | LTER sites, multi-year observational datasets |
| `MESOCOSM` | Enclosures, microcosms, mesocosms |
| `LABORATORY` | Controlled lab experiments |
| `META_ANALYSIS` | Statistical synthesis across multiple studies |
| `REVIEW` | Narrative review papers |
| `COMPUTATIONAL` | Models and simulations |
| `REMOTE_SENSING` | Satellite or aerial data |

## Valid Enums

**Taxon roles**: PRIMARY_PRODUCER, DECOMPOSER, CONSUMER, DETRITIVORE, NITROGEN_FIXER, NITRIFIER, DENITRIFIER, KEYSTONE_SPECIES, ENGINEER, VECTOR, HOST, SYMBIONT, FACILITATOR, COMPETITOR, PREDATOR, PREY, POLLINATOR, SEED_DISPERSER, OTHER

**Causal predicates**: CAUSES, CONTRIBUTES_TO, INHIBITS, MODULATES, REGULATES, ENABLES, PRECEDES

**Supports values**: SUPPORT, REFUTE, PARTIAL, NO_EVIDENCE
