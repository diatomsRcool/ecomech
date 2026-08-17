# EcoMech Workplan

## Phase 1 — Infrastructure (Weeks 1–4)

1. **Install and verify toolchain**: `just install`, run `just qc` on the nitrogen cycling entry with real PMIDs fetched
2. **Finalize schema**: Validate the LinkML schema generates clean Python datamodels (`just gen-all`); refine enums and slots based on first curation experience
3. **HTML renderer**: Implement `src/ecomech/render/render.py` (Jinja2 templates → browsable process pages), following dismech's pattern
4. **Compliance dashboard**: Implement field-coverage analysis (`src/ecomech/analysis/compliance.py`)
5. **CI/CD**: GitHub Actions workflow for `just qc` on every PR

## Phase 2 — Seed Curation (Weeks 5–12)

### 2a — ECOCORE term gap-filling (prerequisite for non-ENVO processes)

Many ecological processes in the target list below have no suitable term in ENVO's
ecosystem process branch (ENVO:02500000). For these, terms must be added to ECOCORE
before KB entries can be curated. The EcoMech schema now accepts both `ENVO:` and
`ECOCORE:` prefixes in `process_term`.

**Workflow for adding terms to ECOCORE at scale — ROBOT template approach:**

1. **Audit the target list** against existing ENVO and ECOCORE terms:
   ```bash
   just oak-envo-ecosystem-processes       # browse ENVO:02500000 descendants
   uv run runoak -i sqlite:obo:ecocore search "<term>"   # check ECOCORE
   ```
   Record gaps in `src/ecocore_terms/gap_analysis.tsv`.

2. **Draft a ROBOT template** (`src/ecocore_terms/new_process_terms.tsv`) with one
   row per needed term. Minimum columns:

   | ID | Label | Definition | SubClassOf | hasRelatedSynonym |
   |----|-------|------------|------------|-------------------|
   | ECOCORE:XXXXXXX | terrestrial net primary production | The net flux... | ECOCORE:00000013 | terrestrial NPP |

   - Assign IDs by requesting a new ID range from the ECOCORE GitHub issue tracker.
   - Parent class (`SubClassOf`) should be the most specific existing ECOCORE term
     (e.g., `ECOCORE:00000013` photoautotrophy for production processes).
   - Definitions should follow OBO/IAO format: genus + differentia.

3. **Generate OWL from the template**:
   ```bash
   robot template --input ecocore.owl \
     --template src/ecocore_terms/new_process_terms.tsv \
     --output src/ecocore_terms/new_terms.owl
   robot merge --input ecocore.owl --input src/ecocore_terms/new_terms.owl \
     --output src/ecocore_terms/ecocore_with_new_terms.owl
   ```

4. **Submit a PR to ECOCORE** (https://github.com/OBO-community/ecocore) with:
   - The ROBOT template TSV (for review and reproducibility)
   - The merged OWL diff
   - A justification linking each term to an EcoMech target process

5. **Update `conf/oak_config.yaml`** once terms are merged and a new ECOCORE release
   is published; the sqlite adapter will pick up new terms automatically.

**Scaling strategy:** Draft all needed terms in one template pass rather than
issue-by-issue. The remaining gaps (~10 processes) need new ECOCORE terms covering
DOM mineralization, trophic cascades, disturbance/succession, biogeochemical coupling,
and ecosystem services. Terms added in the 2026-08 ECOCORE release (ECOCORE:00000183–00000190)
now cover all primary production and symbiosis targets. Prioritize terms that cover
multiple EcoMech entries.

> **Note:** Query the live OWL rather than the sqlite mirror for the most current terms:
> ```bash
> uv run runoak -i pronto:/tmp/ecocore.owl terms | grep "^ECOCORE:"
> # or: curl -L -o /tmp/ecocore.owl http://purl.obolibrary.org/obo/ecocore.owl
> ```

### 2b — KB entry curation

Prioritize **30–50 foundational ecological processes** covering the major
biogeochemical cycles and ecosystem function categories:

| Category | Target Processes | Term |
|---|---|---|
| Nutrient cycles | Nitrogen cycling | ✅ ENVO:01001813 |
| Nutrient cycles | Phosphorus cycling | ✅ ENVO (existing) |
| Nutrient cycles | Carbon cycling | ✅ ENVO (existing) |
| Nutrient cycles | Sulfur cycling | ✅ ENVO (existing) |
| Primary production | Terrestrial NPP | ✅ ECOCORE:00000183 |
| Primary production | Marine primary production | ✅ ECOCORE:00000184 |
| Primary production | Benthic production | ✅ ECOCORE:00000185 |
| Decomposition | Litter decomposition | ✅ ECOCORE:00000186 |
| Decomposition | Dissolved organic matter mineralization | ❌ need ECOCORE term |
| Trophic processes | Herbivory | ✅ ECOCORE:00000020 |
| Trophic processes | Predation | ✅ ECOCORE:00000102 |
| Trophic processes | Detritivory | ✅ ECOCORE:00000057 |
| Trophic processes | Trophic cascades | ❌ need ECOCORE term |
| Symbioses | Mycorrhizal association | ✅ ECOCORE:00000188 |
| Symbioses | Root nodule symbiosis | ✅ ECOCORE:00000189 |
| Symbioses | Coral-zooxanthellae symbiosis | ✅ ECOCORE:00000190 |
| Disturbance/succession | Wildfire succession | ❌ need ECOCORE term |
| Disturbance/succession | Gap dynamics | ❌ need ECOCORE term |
| Disturbance/succession | Flood pulse | ❌ need ECOCORE term |
| Biogeochemical coupling | Redox dynamics | ❌ need ECOCORE term |
| Biogeochemical coupling | Methane cycling | ❌ need ECOCORE term |
| Biogeochemical coupling | Iron cycling | ❌ need ECOCORE term |
| Ecosystem services | Pollination | ❌ need ECOCORE term |
| Ecosystem services | Seed dispersal | ❌ need ECOCORE term |
| Ecosystem services | Water filtration | ❌ need ECOCORE term |
| Ecosystem services | Carbon sequestration | ❌ need ECOCORE term |

For each process:
- Confirm or add ontology term (ENVO preferred; ECOCORE if ENVO gap)
- Curate 3–5 mechanisms backed by ≥2 PMIDs each
- 3–5 quantitative indicators
- 3–5 key drivers
- 2–3 validated interventions

## Phase 3 — Module Library (Months 3–4)

Build reusable **mechanism modules** in `kb/modules/` for conserved components:
- Decomposition cascade
- Trophic amplification
- Redox ladder
- Microbial loop
- Stoichiometric homeostasis
- Threshold/regime shift dynamics

## Phase 4 — Tooling Expansion (Months 4–6)

1. **Network export**: CX2 / KGX graph export for visualization (adapt `dismech-cx2`)
2. **OAK-powered curation skill**: `/curate` Claude Code skill for automated ENVO term lookup, PubMed search, and YAML drafting
3. **ENVO hierarchy browser**: Interactive browser showing which ENVO process subtrees are curated vs. uncurated
4. **Cross-database ingestion**: Pull structured data from GBIF (species traits), LTER (long-term datasets), TRY (plant traits), GloNAF (invasive species)
5. **Embedding explorer**: UMAP/TSNE visualization of process similarity

## Phase 5 — Community & Scale (Months 6–12)

1. Open community curation via GitHub PRs with automated validation
2. Target 200+ ecological processes covering all major biomes
3. Integrate with Earth System ontologies (SWEET) and biodiversity informatics (DwC)
4. KGX export for integration with Monarch Knowledge Graph
5. Prioritization dashboard showing uncurated ENVO processes (analogous to dismech's MONDO coverage dashboard)

## Immediate Next Steps

```bash
cd ecomech
just install
# Replace placeholder snippets in Nitrogen_Cycling.yaml with real PMIDs:
just fetch-reference PMID:15006420
just fetch-reference PMID:16957253
just fetch-reference PMID:11397943
just fetch-reference PMID:9651482
# Then update snippets to exact verbatim quotes and run:
just qc
```
